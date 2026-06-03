const API_BASE_URL = "http://127.0.0.1:8001";

// ─────────────────────────────────────────────────
// Global State
// ─────────────────────────────────────────────────
let state = {
  token: localStorage.getItem("token") || null,
  currentUser: null,
  currentPage: 1,
  limit: 10,
  totalPages: 1,
  searchTimeout: null,
  charts: {
    monthly: null,
    category: null
  }
};

// Category Colors for Charts & Tags
const CATEGORY_COLORS = {
  Food: { bg: "rgba(6, 182, 212, 0.15)", border: "#06b6d4" },       // Cyan
  Travel: { bg: "rgba(99, 102, 241, 0.15)", border: "#6366f1" },     // Indigo
  Shopping: { bg: "rgba(236, 72, 153, 0.15)", border: "#ec4899" },   // Pink
  Entertainment: { bg: "rgba(245, 158, 11, 0.15)", border: "#f59e0b" }, // Amber
  Utilities: { bg: "rgba(16, 185, 129, 0.15)", border: "#10b981" },   // Emerald
  Education: { bg: "rgba(139, 92, 246, 0.15)", border: "#8b5cf6" },   // Purple
  Other: { bg: "rgba(100, 116, 139, 0.15)", border: "#64748b" }       // Slate
};

// ─────────────────────────────────────────────────
// App Initialization
// ─────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  initApp();
});

async function initApp() {
  if (state.token) {
    const success = await fetchCurrentUser();
    if (success) {
      showView("dashboard-view");
      loadDashboard();
    } else {
      handleLogout();
    }
  } else {
    showView("auth-view");
  }
}

// ─────────────────────────────────────────────────
// Authentication Views & Tabs
// ─────────────────────────────────────────────────
function switchAuthTab(tab) {
  const loginTab = document.getElementById("tab-login");
  const regTab = document.getElementById("tab-register");
  const loginForm = document.getElementById("form-login-container");
  const regForm = document.getElementById("form-register-container");
  
  hideAlert("auth-alert");

  if (tab === "login") {
    loginTab.classList.add("active");
    regTab.classList.remove("active");
    loginForm.classList.add("active");
    regForm.classList.remove("active");
  } else {
    loginTab.classList.remove("active");
    regTab.classList.add("active");
    loginForm.classList.remove("active");
    regForm.classList.add("active");
  }
}

function showView(viewId) {
  const views = ["auth-view", "dashboard-view"];
  views.forEach(id => {
    const el = document.getElementById(id);
    if (id === viewId) {
      el.classList.add("active");
    } else {
      el.classList.remove("active");
    }
  });
}

// ─────────────────────────────────────────────────
// Auth Callbacks & Handlers
// ─────────────────────────────────────────────────
async function handleLogin(e) {
  e.preventDefault();
  hideAlert("auth-alert");

  const email = document.getElementById("login-email").value;
  const password = document.getElementById("login-password").value;

  try {
    const response = await fetch(`${API_BASE_URL}/users/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Authentication failed. Please verify credentials.");
    }

    state.token = data.access_token;
    localStorage.setItem("token", data.access_token);
    
    const userSuccess = await fetchCurrentUser();
    if (userSuccess) {
      showView("dashboard-view");
      loadDashboard();
      showDashboardAlert("Welcome back, " + state.currentUser.username + "!", "success");
      // Reset form
      document.getElementById("form-login").reset();
    } else {
      throw new Error("Unable to retrieve user profile details.");
    }

  } catch (error) {
    showAuthAlert(error.message);
  }
}

async function handleRegister(e) {
  e.preventDefault();
  hideAlert("auth-alert");

  const username = document.getElementById("register-username").value;
  const email = document.getElementById("register-email").value;
  const password = document.getElementById("register-password").value;

  try {
    const response = await fetch(`${API_BASE_URL}/users/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, email, password })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Registration failed. Ensure email/username is unique.");
    }

    // Success alert and switch to login
    showDashboardAlert("Registration successful! Please login below.", "success");
    switchAuthTab("login");
    document.getElementById("login-email").value = email;
    document.getElementById("form-register").reset();
  } catch (error) {
    showAuthAlert(error.message);
  }
}

async function fetchCurrentUser() {
  try {
    const response = await fetch(`${API_BASE_URL}/users/me`, {
      headers: { "Authorization": `Bearer ${state.token}` }
    });
    if (!response.ok) return false;
    
    state.currentUser = await response.json();
    document.getElementById("user-name").innerText = state.currentUser.username;
    document.getElementById("user-avatar").innerText = state.currentUser.username.charAt(0).toUpperCase();
    return true;
  } catch (err) {
    console.error("Error fetching current user:", err);
    return false;
  }
}

function handleLogout() {
  state.token = null;
  state.currentUser = null;
  localStorage.removeItem("token");
  showView("auth-view");
  showDashboardAlert("You have logged out successfully.", "success");
  
  // Reset filters
  document.getElementById("filter-search").value = "";
  document.getElementById("filter-category").value = "";
  document.getElementById("filter-min-amount").value = "";
  document.getElementById("filter-max-amount").value = "";
  document.getElementById("filter-month").value = "";
  document.getElementById("filter-year").value = "";
}

// ─────────────────────────────────────────────────
// Dashboard Loading & Analytics
// ─────────────────────────────────────────────────
function loadDashboard() {
  state.currentPage = 1;
  fetchDashboardMetrics();
  fetchExpenses();
}

async function fetchDashboardMetrics() {
  try {
    const headers = { "Authorization": `Bearer ${state.token}` };
    
    // Fetch Summary Metrics
    const resSummary = await fetch(`${API_BASE_URL}/expenses/summary`, { headers });
    const dataSummary = await resSummary.json();
    
    if (resSummary.ok) {
      document.getElementById("metric-total-spent").innerText = `$${dataSummary.total_spent.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
      document.getElementById("metric-total-count").innerText = dataSummary.total_expenses;
    }

    // Fetch Category Summary (for pie chart and top category)
    const resCategory = await fetch(`${API_BASE_URL}/expenses/category-summary`, { headers });
    const dataCategory = await resCategory.json();
    
    if (resCategory.ok) {
      const breakdown = dataCategory.breakdown || {};
      
      // Determine Top Category
      let topCat = "-";
      let maxVal = -1;
      for (const [cat, val] of Object.entries(breakdown)) {
        if (val > maxVal) {
          maxVal = val;
          topCat = cat;
        }
      }
      document.getElementById("metric-top-category").innerText = topCat !== "-" ? topCat : "None";
      
      // Render Category Chart
      renderCategoryChart(breakdown);
    }

    // Fetch Monthly Spending (for bar chart)
    const currentYear = new Date().getFullYear();
    const resMonthly = await fetch(`${API_BASE_URL}/expenses/monthly-report?year=${currentYear}`, { headers });
    const dataMonthly = await resMonthly.json();

    if (resMonthly.ok) {
      renderMonthlyChart(dataMonthly.breakdown || {});
    }

  } catch (err) {
    console.error("Error loading dashboard metrics:", err);
  }
}

// ─────────────────────────────────────────────────
// Expense List Retrieval, Filters & Sorting
// ─────────────────────────────────────────────────
async function fetchExpenses() {
  try {
    const headers = { "Authorization": `Bearer ${state.token}` };
    
    // Read Filter Inputs
    const search = document.getElementById("filter-search").value;
    const category = document.getElementById("filter-category").value;
    const minAmount = document.getElementById("filter-min-amount").value;
    const maxAmount = document.getElementById("filter-max-amount").value;
    const month = document.getElementById("filter-month").value;
    const year = document.getElementById("filter-year").value;
    
    // Build Query String
    let queryParams = new URLSearchParams({
      page: state.currentPage,
      limit: state.limit
    });
    
    if (search) queryParams.append("search", search);
    if (category) queryParams.append("category", category);
    if (minAmount) queryParams.append("min_amount", minAmount);
    if (maxAmount) queryParams.append("max_amount", maxAmount);
    if (month) queryParams.append("month", month);
    if (year) queryParams.append("year", year);
    
    const response = await fetch(`${API_BASE_URL}/expenses?${queryParams.toString()}`, { headers });
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || "Could not retrieve expenses list.");
    }
    
    renderExpenseTable(data.items || [], data.total);
    
    state.totalPages = data.pages || 1;
    updatePaginationUI(data.page, data.pages, data.total);
    
  } catch (err) {
    console.error("Error loading expenses:", err);
    showDashboardAlert(err.message, "danger");
  }
}

function renderExpenseTable(expenses, totalItems) {
  const tbody = document.getElementById("expense-list-body");
  const emptyState = document.getElementById("expense-empty-state");
  const table = document.getElementById("expense-table");
  
  tbody.innerHTML = "";
  
  if (expenses.length === 0) {
    emptyState.style.display = "flex";
    table.style.display = "none";
    return;
  }
  
  emptyState.style.display = "none";
  table.style.display = "table";
  
  expenses.forEach(exp => {
    const row = document.createElement("tr");
    
    // Format Date nicely
    const dateObj = new Date(exp.date);
    const formattedDate = dateObj.toLocaleDateString(undefined, { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
    
    // Category style tag
    const catStyle = CATEGORY_COLORS[exp.category] || CATEGORY_COLORS.Other;
    const categoryTag = `<span class="category-tag" style="background: ${catStyle.bg}; color: ${catStyle.border}; border-color: ${catStyle.border}">${exp.category}</span>`;
    
    row.innerHTML = `
      <td style="color: var(--text-secondary); font-size: 0.9rem;">${formattedDate}</td>
      <td style="font-weight: 600;">${escapeHTML(exp.title)}</td>
      <td>${categoryTag}</td>
      <td style="color: var(--text-secondary); font-size: 0.9rem; max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
        ${escapeHTML(exp.description || "-")}
      </td>
      <td class="expense-amount">$${exp.amount.toFixed(2)}</td>
      <td>
        <div class="action-buttons">
          <button class="btn btn-secondary btn-icon-only" onclick="openEditModal(${JSON.stringify(exp).replace(/"/g, '&quot;')})" title="Edit">
            <i class="fa-solid fa-pen-to-square"></i>
          </button>
          <button class="btn btn-secondary btn-icon-only" onclick="openDeleteModal(${exp.id})" title="Delete" style="color: var(--accent-red)">
            <i class="fa-solid fa-trash"></i>
          </button>
        </div>
      </td>
    `;
    
    tbody.appendChild(row);
  });
}

// ─────────────────────────────────────────────────
// Pagination Handlers
// ─────────────────────────────────────────────────
function updatePaginationUI(page, pages, total) {
  const startItem = total === 0 ? 0 : (page - 1) * state.limit + 1;
  const endItem = Math.min(page * state.limit, total);
  
  document.getElementById("pagination-info").innerText = 
    `Showing ${startItem} to ${endItem} of ${total} entries`;
    
  const btnPrev = document.getElementById("btn-prev-page");
  const btnNext = document.getElementById("btn-next-page");
  
  btnPrev.disabled = page <= 1;
  btnNext.disabled = page >= pages;
}

function changePage(delta) {
  const newPage = state.currentPage + delta;
  if (newPage >= 1 && newPage <= state.totalPages) {
    state.currentPage = newPage;
    fetchExpenses();
  }
}

// ─────────────────────────────────────────────────
// Filter Actions
// ─────────────────────────────────────────────────
function toggleFiltersPanel() {
  const panel = document.getElementById("filters-panel");
  panel.classList.toggle("active");
}

function applyFilters() {
  state.currentPage = 1;
  fetchExpenses();
}

function handleSearchFilter() {
  clearTimeout(state.searchTimeout);
  state.searchTimeout = setTimeout(() => {
    applyFilters();
  }, 350); // Debounce search calls
}

// ─────────────────────────────────────────────────
// Add Expense Actions
// ─────────────────────────────────────────────────
async function handleAddExpense(e) {
  e.preventDefault();
  
  const title = document.getElementById("add-title").value;
  const amount = parseFloat(document.getElementById("add-amount").value);
  const category = document.getElementById("add-category").value;
  const date = document.getElementById("add-date").value;
  const description = document.getElementById("add-description").value;
  
  try {
    const response = await fetch(`${API_BASE_URL}/expenses`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Authorization": `Bearer ${state.token}`
      },
      body: JSON.stringify({ title, amount, category, date, description })
    });
    
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Unable to save expense.");
    }
    
    closeModal("add-expense-modal");
    showDashboardAlert("Expense added successfully!", "success");
    loadDashboard();
    
  } catch (err) {
    console.error("Error adding expense:", err);
    showDashboardAlert(err.message, "danger");
  }
}

// ─────────────────────────────────────────────────
// Edit Expense Actions
// ─────────────────────────────────────────────────
function openEditModal(expense) {
  document.getElementById("edit-id").value = expense.id;
  document.getElementById("edit-title").value = expense.title;
  document.getElementById("edit-amount").value = expense.amount;
  document.getElementById("edit-category").value = expense.category;
  document.getElementById("edit-date").value = expense.date;
  document.getElementById("edit-description").value = expense.description || "";
  
  openModal("edit-expense-modal");
}

async function handleEditExpense(e) {
  e.preventDefault();
  
  const id = document.getElementById("edit-id").value;
  const title = document.getElementById("edit-title").value;
  const amount = parseFloat(document.getElementById("edit-amount").value);
  const category = document.getElementById("edit-category").value;
  const date = document.getElementById("edit-date").value;
  const description = document.getElementById("edit-description").value;
  
  try {
    const response = await fetch(`${API_BASE_URL}/expenses/${id}`, {
      method: "PUT",
      headers: { 
        "Content-Type": "application/json",
        "Authorization": `Bearer ${state.token}`
      },
      body: JSON.stringify({ title, amount, category, date, description })
    });
    
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Unable to save modifications.");
    }
    
    closeModal("edit-expense-modal");
    showDashboardAlert("Expense updated successfully!", "success");
    loadDashboard();
    
  } catch (err) {
    console.error("Error editing expense:", err);
    showDashboardAlert(err.message, "danger");
  }
}

// ─────────────────────────────────────────────────
// Delete Expense Actions
// ─────────────────────────────────────────────────
function openDeleteModal(id) {
  document.getElementById("delete-id").value = id;
  openModal("delete-expense-modal");
}

async function confirmDeleteExpense() {
  const id = document.getElementById("delete-id").value;
  
  try {
    const response = await fetch(`${API_BASE_URL}/expenses/${id}`, {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${state.token}` }
    });
    
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Unable to delete expense.");
    }
    
    closeModal("delete-expense-modal");
    showDashboardAlert("Expense deleted successfully.", "success");
    loadDashboard();
    
  } catch (err) {
    console.error("Error deleting expense:", err);
    showDashboardAlert(err.message, "danger");
  }
}

// ─────────────────────────────────────────────────
// Modal Windows Helpers
// ─────────────────────────────────────────────────
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  modal.style.display = "flex";
  
  // Set immediate animation step
  setTimeout(() => {
    modal.classList.add("active");
  }, 10);
  
  // Default add-date field to current local date
  if (modalId === "add-expense-modal") {
    const dateInput = document.getElementById("add-date");
    if (!dateInput.value) {
      dateInput.value = new Date().toISOString().split('T')[0];
    }
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  modal.classList.remove("active");
  
  // Hide container after transition is finished
  setTimeout(() => {
    modal.style.display = "none";
  }, 300);
}

function handleOutsideModalClick(e, modalId) {
  if (e.target.id === modalId) {
    closeModal(modalId);
  }
}

// ─────────────────────────────────────────────────
// Chart.js Visualizations
// ─────────────────────────────────────────────────
function renderCategoryChart(breakdown) {
  const ctx = document.getElementById("categoryChart").getContext("2d");
  
  // Destroy existing chart to prevent canvas hover rendering glitches
  if (state.charts.category) {
    state.charts.category.destroy();
  }
  
  const labels = Object.keys(breakdown);
  const data = Object.values(breakdown);
  
  if (labels.length === 0) {
    // Render empty chart or write info text
    ctx.clearRect(0, 0, 400, 400);
    return;
  }
  
  const backgroundColors = labels.map(label => (CATEGORY_COLORS[label] || CATEGORY_COLORS.Other).bg);
  const borderColors = labels.map(label => (CATEGORY_COLORS[label] || CATEGORY_COLORS.Other).border);
  
  state.charts.category = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: backgroundColors,
        borderColor: borderColors,
        borderWidth: 1.5,
        hoverOffset: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: {
            color: '#94a3b8',
            font: { family: 'Plus Jakarta Sans', size: 12, weight: '500' },
            padding: 15,
            usePointStyle: true,
            pointStyle: 'circle'
          }
        },
        tooltip: {
          backgroundColor: 'rgba(15, 23, 42, 0.95)',
          titleFont: { family: 'Plus Jakarta Sans', weight: '700' },
          bodyFont: { family: 'Plus Jakarta Sans' },
          borderColor: 'rgba(255,255,255,0.08)',
          borderWidth: 1,
          callbacks: {
            label: function(context) {
              const val = context.raw || 0;
              const total = context.dataset.data.reduce((a, b) => a + b, 0);
              const percentage = ((val / total) * 100).toFixed(1);
              return ` $${val.toFixed(2)} (${percentage}%)`;
            }
          }
        }
      },
      cutout: '65%'
    }
  });
}

function renderMonthlyChart(breakdown) {
  const ctx = document.getElementById("monthlyChart").getContext("2d");
  
  if (state.charts.monthly) {
    state.charts.monthly.destroy();
  }

  // Prepopulate standard calendar order
  const monthOrder = [
    "January", "February", "March", "April", "May", "June", 
    "July", "August", "September", "October", "November", "December"
  ];
  
  // Reorder values according to calendar order
  const filteredLabels = monthOrder.filter(m => breakdown[m] !== undefined || Object.keys(breakdown).length === 0);
  const data = filteredLabels.map(m => breakdown[m] || 0);

  // If no items, show empty chart state
  if (filteredLabels.length === 0) {
    // Check if there are keys that don't match, e.g. numeric "05", "06"
    const fallbackLabels = Object.keys(breakdown);
    if (fallbackLabels.length > 0) {
      // Use whatever keys returned
      state.charts.monthly = createBarChart(ctx, fallbackLabels, Object.values(breakdown));
    }
    return;
  }

  state.charts.monthly = createBarChart(ctx, filteredLabels, data);
}

function createBarChart(ctx, labels, data) {
  // Create gradient fill for the bars
  const gradient = ctx.createLinearGradient(0, 0, 0, 300);
  gradient.addColorStop(0, '#6366f1'); // purple
  gradient.addColorStop(1, '#06b6d4'); // cyan

  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Spent Amount ($)',
        data: data,
        backgroundColor: gradient,
        borderRadius: 6,
        borderWidth: 0,
        barThickness: 24
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(15, 23, 42, 0.95)',
          titleFont: { family: 'Plus Jakarta Sans', weight: '700' },
          bodyFont: { family: 'Plus Jakarta Sans' },
          borderColor: 'rgba(255,255,255,0.08)',
          borderWidth: 1,
          callbacks: {
            label: function(context) {
              return ` $${(context.raw || 0).toFixed(2)}`;
            }
          }
        }
      },
      scales: {
        y: {
          grid: { color: 'rgba(255, 255, 255, 0.04)', drawTicks: false },
          ticks: {
            color: '#64748b',
            font: { family: 'Plus Jakarta Sans', size: 10 },
            callback: function(value) { return '$' + value; }
          },
          border: { display: false }
        },
        x: {
          grid: { display: false },
          ticks: { color: '#64748b', font: { family: 'Plus Jakarta Sans', size: 10 } },
          border: { display: false }
        }
      }
    }
  });
}

// ─────────────────────────────────────────────────
// Alert Notifications & Utilities
// ─────────────────────────────────────────────────
function showAuthAlert(msg) {
  const alertEl = document.getElementById("auth-alert");
  document.getElementById("auth-alert-text").innerText = msg;
  alertEl.classList.add("active");
}

function showDashboardAlert(msg, type = "success") {
  const alertEl = document.getElementById("dashboard-alert");
  const textEl = document.getElementById("dashboard-alert-text");
  
  textEl.innerText = msg;
  
  // Set alert design
  alertEl.className = "alert active"; // reset classes
  if (type === "danger") {
    alertEl.classList.add("alert-danger");
    alertEl.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> <span id="dashboard-alert-text">${escapeHTML(msg)}</span>`;
  } else {
    alertEl.classList.add("alert-success");
    alertEl.innerHTML = `<i class="fa-solid fa-circle-check"></i> <span id="dashboard-alert-text">${escapeHTML(msg)}</span>`;
  }

  // Clear alert after 4 seconds
  setTimeout(() => {
    hideAlert("dashboard-alert");
  }, 4000);
}

function hideAlert(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove("active");
}

function escapeHTML(str) {
  if (!str) return "";
  return str.replace(/[&<>'"]/g, 
    tag => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      "'": '&#39;',
      '"': '&quot;'
    }[tag] || tag)
  );
}
