import urllib.request
import urllib.parse
import json
import random
import string
import sys

BASE_URL = "http://127.0.0.1:8000"

def random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def make_request(path, method="GET", data=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    req_data = None
    if data is not None:
        req_data = json.dumps(data).encode("utf-8")
        
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as response:
            res_data = response.read().decode("utf-8")
            return response.status, json.loads(res_data) if res_data else {}
    except urllib.error.HTTPError as e:
        res_data = e.read().decode("utf-8")
        try:
            err_json = json.loads(res_data)
        except Exception:
            err_json = res_data
        return e.code, err_json
    except urllib.error.URLError as e:
        print(f"Error connecting to server: {e}")
        sys.exit(1)

def run_tests():
    print("=== Starting API Tests ===")
    
    # 1. Health & Root tests
    status, res = make_request("/")
    assert status == 200, f"Expected 200, got {status}"
    assert "Welcome" in res.get("message", ""), f"Unexpected response: {res}"
    print("OK: Health / passed")
    
    status, res = make_request("/health")
    assert status == 200, f"Expected 200, got {status}"
    assert res.get("status") == "healthy", f"Unexpected response: {res}"
    print("OK: Health /health passed")

    # Generate unique credentials
    username = f"user_{random_string()}"
    email = f"{username}@example.com"
    password = "SecurePassword123!"
    
    # 2. Registration test
    reg_data = {
        "username": username,
        "email": email,
        "password": password
    }
    status, res = make_request("/users/register", method="POST", data=reg_data)
    assert status == 201, f"Register failed: {status} - {res}"
    assert res.get("username") == username, f"Unexpected username: {res}"
    assert "id" in res, f"Missing id in response: {res}"
    user_id = res["id"]
    print(f"OK: User Registration passed (username={username}, id={user_id})")
    
    # 3. Duplicate Registration test
    status, res = make_request("/users/register", method="POST", data=reg_data)
    assert status == 400, f"Expected 400, got {status} - {res}"
    print("OK: Duplicate registration prevented correctly")

    # 4. Login test
    login_data = {
        "email": email,
        "password": password
    }
    status, res = make_request("/users/login", method="POST", data=login_data)
    assert status == 200, f"Login failed: {status} - {res}"
    token = res.get("access_token")
    assert token is not None, f"Missing access_token in login response: {res}"
    print("OK: User Login passed")

    # 5. Get current user profile (Me)
    status, res = make_request("/users/me", token=token)
    assert status == 200, f"Get current user failed: {status} - {res}"
    assert res.get("id") == user_id, f"Profile ID mismatch: {res}"
    print("OK: User Profile (/users/me) passed")

    # 6. Expenses CRUD
    # Let's create multiple expenses for different dates and categories
    expenses_to_create = [
        {"title": "Lunch", "amount": 25.50, "category": "Food", "date": "2026-06-01", "description": "Sushi with coworker"},
        {"title": "Taxi ride", "amount": 15.00, "category": "Travel", "date": "2026-06-01", "description": "To office"},
        {"title": "Weekly groceries", "amount": 120.00, "category": "Food", "date": "2026-06-02", "description": "Supermarket run"},
        {"title": "Online course", "amount": 49.99, "category": "Education", "date": "2026-05-15", "description": "Python deep dive"},
    ]
    
    created_expenses = []
    for exp in expenses_to_create:
        status, res = make_request("/expenses", method="POST", data=exp, token=token)
        assert status == 201, f"Expense creation failed: {status} - {res}"
        assert res.get("title") == exp["title"], f"Title mismatch: {res}"
        created_expenses.append(res)
        
    print(f"OK: Created {len(created_expenses)} expenses successfully")
    
    # 7. List expenses (without filters)
    status, res = make_request("/expenses", token=token)
    assert status == 200, f"List expenses failed: {status} - {res}"
    assert res.get("total") == 4, f"Expected total 4, got {res.get('total')}"
    assert len(res.get("items", [])) == 4, f"Expected 4 items, got {len(res.get('items'))}"
    print("OK: Listing expenses (unfiltered) passed")
    
    # 8. List expenses (filtered by category)
    status, res = make_request("/expenses?category=Food", token=token)
    assert status == 200, f"List expenses filtered by category failed: {status} - {res}"
    assert res.get("total") == 2, f"Expected total 2 Food expenses, got {res.get('total')}"
    print("OK: Filtering by category passed")
    
    # 9. List expenses (filtered by amount range)
    status, res = make_request("/expenses?min_amount=20&max_amount=100", token=token)
    assert status == 200, f"List expenses filtered by amount range failed: {status} - {res}"
    assert res.get("total") == 2, f"Expected total 2, got {res.get('total')}"  # Lunch (25.50) and Online course (49.99)
    print("OK: Filtering by amount range passed")
    
    # 10. Search query
    status, res = make_request("/expenses?search=sushi", token=token)
    assert status == 200, f"Search failed: {status} - {res}"
    assert res.get("total") == 1, f"Expected search result 1, got {res.get('total')}"
    print("OK: Search query passed")

    # 11. Pagination
    status, res = make_request("/expenses?page=1&limit=2", token=token)
    assert status == 200, f"Pagination failed: {status} - {res}"
    assert len(res.get("items", [])) == 2, f"Expected 2 items, got {len(res.get('items'))}"
    assert res.get("pages") == 2, f"Expected 2 pages, got {res.get('pages')}"
    print("OK: Pagination passed")

    # 12. Retrieve individual expense by ID
    exp_id = created_expenses[0]["id"]
    status, res = make_request(f"/expenses/{exp_id}", token=token)
    assert status == 200, f"Retrieve expense failed: {status} - {res}"
    assert res.get("id") == exp_id, f"ID mismatch: {res}"
    print("OK: Retrieve expense by ID passed")

    # 13. Update expense
    update_data = {"amount": 30.00, "description": "Sushi with coworker (updated)"}
    status, res = make_request(f"/expenses/{exp_id}", method="PUT", data=update_data, token=token)
    assert status == 200, f"Update expense failed: {status} - {res}"
    assert res.get("amount") == 30.00, f"Amount not updated: {res}"
    assert res.get("description") == "Sushi with coworker (updated)", f"Description not updated: {res}"
    print("OK: Update expense passed")

    # 14. Analytics: Summary
    status, res = make_request("/expenses/summary", token=token)
    assert status == 200, f"Summary failed: {status} - {res}"
    # Total spent: Lunch (30.00) + Taxi (15.00) + Groceries (120.00) + Course (49.99) = 214.99
    assert abs(res.get("total_spent", 0) - 214.99) < 0.01, f"Expected 214.99, got {res.get('total_spent')}"
    assert res.get("total_expenses") == 4, f"Expected 4 expenses, got {res.get('total_expenses')}"
    print("OK: Expense summary analytics passed")

    # 15. Analytics: Category breakdown
    status, res = make_request("/expenses/category-summary", token=token)
    assert status == 200, f"Category summary failed: {status} - {res}"
    breakdown = res.get("breakdown", {})
    # Food: Lunch (30.00) + Groceries (120.00) = 150.00
    assert abs(breakdown.get("Food", 0) - 150.00) < 0.01, f"Expected 150.00 for Food, got {breakdown.get('Food')}"
    # Travel: 15.00
    assert abs(breakdown.get("Travel", 0) - 15.00) < 0.01, f"Expected 15.00 for Travel, got {breakdown.get('Travel')}"
    print("OK: Category breakdown analytics passed")

    # 16. Analytics: Monthly report
    status, res = make_request("/expenses/monthly-report?year=2026", token=token)
    assert status == 200, f"Monthly report failed: {status} - {res}"
    monthly_breakdown = res.get("breakdown", {})
    # June: Lunch (30.00) + Taxi (15.00) + Groceries (120.00) = 165.00
    # Wait, let's verify if the SQLite date extracting works
    print(f"Monthly breakdown structure received: {monthly_breakdown}")
    assert "June" in monthly_breakdown or "06" in monthly_breakdown or "6" in monthly_breakdown, f"Missing June data in: {monthly_breakdown}"
    
    # Check amount for June (either by "June" or "06" depending on extract result)
    june_key = "June" if "June" in monthly_breakdown else ("06" if "06" in monthly_breakdown else "6")
    assert abs(monthly_breakdown.get(june_key, 0) - 165.00) < 0.01, f"Expected 165.00 for June, got {monthly_breakdown.get(june_key)}"
    print("OK: Monthly report analytics passed")

    # 17. Delete expense
    status, res = make_request(f"/expenses/{exp_id}", method="DELETE", token=token)
    assert status == 200, f"Delete failed: {status} - {res}"
    
    # Confirm it is deleted
    status, res = make_request(f"/expenses/{exp_id}", token=token)
    assert status == 404, f"Expected 404 after delete, got {status} - {res}"
    print("OK: Delete expense passed")

    # 18. Analytics after deletion
    status, res = make_request("/expenses/summary", token=token)
    assert res.get("total_expenses") == 3, f"Expected 3 expenses after deletion, got {res.get('total_expenses')}"
    print("OK: Post-deletion summary check passed")

    print("\nALL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
