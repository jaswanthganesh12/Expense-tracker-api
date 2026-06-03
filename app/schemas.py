from datetime import date, datetime
from typing import Annotated, Union

from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ─────────────────────────────────────────────
# User Schemas
# ─────────────────────────────────────────────

class UserCreate(BaseModel):
    """Schema for user registration requests."""
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Username must be between 3 and 50 characters",
        examples=["john_doe"],
    )
    email: EmailStr = Field(
        ...,
        description="A valid email address",
        examples=["john@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password must be at least 8 characters",
        examples=["securepassword123"],
    )


class UserLogin(BaseModel):
    """Schema for user login requests."""
    email: EmailStr = Field(..., examples=["john@example.com"])
    password: str = Field(..., examples=["securepassword123"])


class UserResponse(BaseModel):
    """Schema for user profile responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    created_at: datetime


# ─────────────────────────────────────────────
# Token Schemas
# ─────────────────────────────────────────────

class Token(BaseModel):
    """Schema for JWT token responses."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for data extracted from JWT tokens."""
    user_id: Union[int, None] = None


# ─────────────────────────────────────────────
# Expense Schemas
# ─────────────────────────────────────────────

class ExpenseCreate(BaseModel):
    """Schema for creating a new expense."""
    title: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Title of the expense",
        examples=["Lunch at restaurant"],
    )
    amount: float = Field(
        ...,
        gt=0,
        description="Amount spent (must be greater than 0)",
        examples=[250.00],
    )
    category: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Category of the expense",
        examples=["Food"],
    )
    description: Annotated[
        Union[str, None],
        Field(
            default=None,
            max_length=500,
            description="Optional description of the expense",
            examples=["Business lunch with client"],
        ),
    ]
    date: Annotated[
        Union[date, None],
        Field(
            default=None,
            description="Date of the expense (defaults to today if not provided)",
        ),
    ]


class ExpenseUpdate(BaseModel):
    """Schema for updating an existing expense. All fields optional."""
    title: Annotated[
        Union[str, None],
        Field(
            default=None,
            min_length=1,
            max_length=100,
            examples=["Updated lunch title"],
        ),
    ]
    amount: Annotated[
        Union[float, None],
        Field(
            default=None,
            gt=0,
            examples=[300.00],
        ),
    ]
    category: Annotated[
        Union[str, None],
        Field(
            default=None,
            min_length=1,
            max_length=50,
            examples=["Travel"],
        ),
    ]
    description: Annotated[
        Union[str, None],
        Field(
            default=None,
            max_length=500,
            examples=["Updated description"],
        ),
    ]
    date: Annotated[
        Union[date, None],
        Field(
            default=None,
            description="Updated date of the expense",
        ),
    ]


class ExpenseResponse(BaseModel):
    """Schema for expense responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    amount: float
    category: str
    description: Union[str, None] = None
    date: date
    owner_id: int
    created_at: datetime


class PaginatedExpenses(BaseModel):
    """Schema for paginated expense list responses."""
    items: list[ExpenseResponse]
    total: int
    page: int
    limit: int
    pages: int


# ─────────────────────────────────────────────
# Analytics Schemas
# ─────────────────────────────────────────────

class ExpenseSummary(BaseModel):
    """Schema for total expense summary."""
    total_spent: float
    total_expenses: int


class CategorySummary(BaseModel):
    """Schema for expense breakdown by category."""
    breakdown: dict[str, float] = Field(
        ...,
        description="Category-wise spending breakdown",
        examples=[{"Food": 5000.0, "Travel": 10000.0, "Shopping": 7000.0}],
    )


class MonthlyReport(BaseModel):
    """Schema for monthly expense report."""
    year: int
    breakdown: dict[str, float] = Field(
        ...,
        description="Month-wise spending breakdown",
        examples=[{"January": 12000.0, "February": 9000.0, "March": 15000.0}],
    )
