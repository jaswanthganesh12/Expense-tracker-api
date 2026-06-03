import calendar
import logging
from datetime import date, datetime
from typing import Union

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Expense, User
from app.schemas import (
    CategorySummary,
    ExpenseCreate,
    ExpenseResponse,
    ExpenseSummary,
    ExpenseUpdate,
    MonthlyReport,
    PaginatedExpenses,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/expenses", tags=["Expenses"])


# ─────────────────────────────────────────────────
# Helper: build base query filtered to current user
# ─────────────────────────────────────────────────

def _base_query(db: Session, user: User):
    """Return a base query scoped to the current user's expenses."""
    return db.query(Expense).filter(Expense.owner_id == user.id)


def _get_expense_or_404(
    expense_id: int, db: Session, user: User
) -> Expense:
    """Fetch an expense by ID, enforcing ownership.

    Returns the Expense if found and owned by the user.
    Raises 404 if not found, 403 if owned by a different user.
    """
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} not found",
        )
    if expense.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this expense",
        )
    return expense


# ─────────────────────────────────────────────────
# POST /expenses — Create Expense
# ─────────────────────────────────────────────────

@router.post(
    "",
    response_model=ExpenseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new expense",
    description="Create a new expense linked to the authenticated user.",
)
def create_expense(
    expense_data: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new expense for the authenticated user."""
    new_expense = Expense(
        title=expense_data.title,
        amount=expense_data.amount,
        category=expense_data.category,
        description=expense_data.description,
        date=expense_data.date or date.today(),
        owner_id=current_user.id,
    )
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)

    logger.info(
        f"Expense created: id={new_expense.id}, user={current_user.id}, "
        f"amount={new_expense.amount}, category={new_expense.category}"
    )
    return new_expense


# ─────────────────────────────────────────────────
# GET /expenses/summary — Total Expense Summary
# ─────────────────────────────────────────────────

@router.get(
    "/summary",
    response_model=ExpenseSummary,
    summary="Get expense summary",
    description="Returns the total amount spent and total number of expenses for the current user.",
)
def get_expense_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get aggregate spending summary for the authenticated user."""
    result = (
        db.query(
            func.coalesce(func.sum(Expense.amount), 0).label("total_spent"),
            func.count(Expense.id).label("total_expenses"),
        )
        .filter(Expense.owner_id == current_user.id)
        .first()
    )

    return ExpenseSummary(
        total_spent=float(result.total_spent),
        total_expenses=result.total_expenses,
    )


# ─────────────────────────────────────────────────
# GET /expenses/category-summary — Category Breakdown
# ─────────────────────────────────────────────────

@router.get(
    "/category-summary",
    response_model=CategorySummary,
    summary="Get category breakdown",
    description="Returns spending breakdown grouped by expense category.",
)
def get_category_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get spending grouped by category for the authenticated user."""
    results = (
        db.query(
            Expense.category,
            func.sum(Expense.amount).label("total"),
        )
        .filter(Expense.owner_id == current_user.id)
        .group_by(Expense.category)
        .all()
    )

    breakdown = {row.category: float(row.total) for row in results}
    return CategorySummary(breakdown=breakdown)


# ─────────────────────────────────────────────────
# GET /expenses/monthly-report — Monthly Report
# ─────────────────────────────────────────────────

@router.get(
    "/monthly-report",
    response_model=MonthlyReport,
    summary="Get monthly expense report",
    description="Returns spending breakdown by month for a given year.",
)
def get_monthly_report(
    year: Union[int, None] = Query(
        None,
        description="Year for the report (defaults to current year)",
        examples=[2026],
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get monthly spending breakdown for the authenticated user."""
    report_year = year or datetime.utcnow().year

    results = (
        db.query(
            extract("month", Expense.date).label("month"),
            func.sum(Expense.amount).label("total"),
        )
        .filter(
            Expense.owner_id == current_user.id,
            extract("year", Expense.date) == report_year,
        )
        .group_by(extract("month", Expense.date))
        .all()
    )

    breakdown = {
        calendar.month_name[int(row.month)]: float(row.total)
        for row in results
    }

    return MonthlyReport(year=report_year, breakdown=breakdown)


# ─────────────────────────────────────────────────
# GET /expenses — List Expenses (Filtered + Paginated)
# ─────────────────────────────────────────────────

@router.get(
    "",
    response_model=PaginatedExpenses,
    summary="List expenses",
    description="Returns a paginated, filterable list of the current user's expenses.",
)
def list_expenses(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    category: Union[str, None] = Query(None, description="Filter by category"),
    month: Union[int, None] = Query(None, ge=1, le=12, description="Filter by month (1-12)"),
    year: Union[int, None] = Query(None, description="Filter by year"),
    min_amount: Union[float, None] = Query(None, ge=0, description="Minimum amount"),
    max_amount: Union[float, None] = Query(None, ge=0, description="Maximum amount"),
    search: Union[str, None] = Query(None, description="Search in title and description"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List expenses with filtering and pagination.

    Supports filtering by category, date (month/year), amount range,
    and keyword search in title/description.
    """
    query = _base_query(db, current_user)

    # Apply filters
    if category:
        query = query.filter(Expense.category == category)
    if month:
        query = query.filter(extract("month", Expense.date) == month)
    if year:
        query = query.filter(extract("year", Expense.date) == year)
    if min_amount is not None:
        query = query.filter(Expense.amount >= min_amount)
    if max_amount is not None:
        query = query.filter(Expense.amount <= max_amount)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Expense.title.ilike(search_pattern))
            | (Expense.description.ilike(search_pattern))
        )

    # Get total count before pagination
    total = query.count()

    # Calculate total pages
    pages = (total + limit - 1) // limit  # ceiling division

    # Apply pagination
    offset = (page - 1) * limit
    expenses = (
        query.order_by(Expense.date.desc(), Expense.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return PaginatedExpenses(
        items=expenses,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


# ─────────────────────────────────────────────────
# GET /expenses/{expense_id} — Get Expense by ID
# ─────────────────────────────────────────────────

@router.get(
    "/{expense_id}",
    response_model=ExpenseResponse,
    summary="Get expense by ID",
    description="Returns a single expense by its ID. Must be owned by the current user.",
)
def get_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single expense by ID with ownership validation."""
    return _get_expense_or_404(expense_id, db, current_user)


# ─────────────────────────────────────────────────
# PUT /expenses/{expense_id} — Update Expense
# ─────────────────────────────────────────────────

@router.put(
    "/{expense_id}",
    response_model=ExpenseResponse,
    summary="Update an expense",
    description="Update an existing expense. Only provided fields will be changed.",
)
def update_expense(
    expense_id: int,
    expense_data: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing expense with partial data.

    Only fields included in the request body will be updated.
    Ownership is validated before applying changes.
    """
    expense = _get_expense_or_404(expense_id, db, current_user)

    # Apply only the fields that were explicitly set
    update_data = expense_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(expense, field, value)

    db.commit()
    db.refresh(expense)

    logger.info(f"Expense updated: id={expense.id}, fields={list(update_data.keys())}")
    return expense


# ─────────────────────────────────────────────────
# DELETE /expenses/{expense_id} — Delete Expense
# ─────────────────────────────────────────────────

@router.delete(
    "/{expense_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete an expense",
    description="Delete an expense by its ID. Must be owned by the current user.",
)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an expense with ownership validation."""
    expense = _get_expense_or_404(expense_id, db, current_user)

    db.delete(expense)
    db.commit()

    logger.info(f"Expense deleted: id={expense_id}, user={current_user.id}")
    return {"detail": "Expense deleted successfully"}
