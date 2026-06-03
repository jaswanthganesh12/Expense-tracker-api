import sys
sys.path.insert(0, ".")
from app.schemas import ExpenseCreate
print("OK:", ExpenseCreate(title="test", amount=100, category="Food").model_dump())
