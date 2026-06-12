const state = {
  user: null,
  assets: [],
  categories: [],
  bookings: [],
  analytics: null,
  authMode: "login",
};

const authScreen = document.querySelector("#auth-screen");
const dashboardScreen = document.querySelector("#dashboard-screen");
const authForm = document.querySelector("#auth-form");
const toast = document.querySelector("#toast");

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    credentials: "same-origin",
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || "Something went wrong");
  }
  return data;
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.remove("hidden");
  window.setTimeout(() => toast.classList.add("hidden"), 2800);
}

function isAdmin() {
  return state.user?.role === "admin";
}

async function boot() {
  try {
    const data = await api("/api/me");
    state.user = data.user;
    await loadDashboard();
  } catch {
    showAuth();
  }
}

function showAuth() {
  authScreen.classList.remove("hidden");
  dashboardScreen.classList.add("hidden");
}

async function loadDashboard() {
  authScreen.classList.add("hidden");
  dashboardScreen.classList.remove("hidden");
  document.querySelector("#current-user").textContent = `${state.user.name} (${state.user.role})`;
  await Promise.all([loadAssets(), loadBookings(), loadAnalytics()]);
  renderAll();
}

async function loadAssets(search = "", category = "") {
  const params = new URLSearchParams({ search, category });
  const data = await api(`/api/assets?${params}`);
  state.assets = data.assets;
  state.categories = data.categories;
}

async function loadBookings() {
  state.bookings = (await api("/api/bookings")).bookings;
}

async function loadAnalytics() {
  state.analytics = await api("/api/analytics");
}

function renderAll() {
  renderOverview();
  renderAssets();
  renderBookings();
  renderHistory();
}

function renderOverview() {
  const { summary, utilization, status_mix: statusMix } = state.analytics;
  const maxUnits = Math.max(...utilization.map((item) => item.units_booked), 1);
  document.querySelector("#overview-view").innerHTML = `
    <div class="card-grid">
      ${summaryCard("Asset Types", summary.total_assets)}
      ${summaryCard("Total Units", summary.total_units)}
      ${summaryCard("Active Bookings", summary.active_bookings)}
      ${summaryCard("Pending Requests", summary.pending_requests)}
      ${summaryCard("Overdue Returns", summary.overdue_returns)}
    </div>
    <div class="split">
      <section class="panel">
        <h2>Most Utilized Assets</h2>
        <div class="bar-list">
          ${utilization.map((item) => `
            <div>
              <div class="asset-meta"><strong>${item.asset_name}</strong><span>${item.units_booked} units</span></div>
              <div class="bar-track"><div class="bar-fill" style="width:${Math.max(6, (item.units_booked / maxUnits) * 100)}%"></div></div>
            </div>
          `).join("")}
        </div>
      </section>
      <section class="panel">
        <h2>Booking Status Mix</h2>
        <div class="bar-list">
          ${statusMix.map((item) => `<p><span class="status ${item.status}">${item.status}</span> ${item.count} request${item.count === 1 ? "" : "s"}</p>`).join("")}
        </div>
      </section>
    </div>
  `;
}

function summaryCard(label, value) {
  return `<article class="summary-card"><span>${label}</span><strong>${value}</strong></article>`;
}

function renderAssets() {
  const adminForm = isAdmin() ? `
    <section class="panel">
      <h2>Add or Update Asset</h2>
      <form id="asset-form" class="split-form">
        <input type="hidden" name="id">
        <label>Asset Name <input name="asset_name" required></label>
        <label>Category <input name="category" required></label>
        <label>Total Quantity <input name="quantity_total" type="number" min="0" required></label>
        <label>Status <input name="status" value="Available"></label>
        <label>Description <textarea name="description"></textarea></label>
        <button type="submit">Save Asset</button>
      </form>
    </section>
  ` : "";

  document.querySelector("#assets-view").innerHTML = `
    <section class="panel">
      <div class="filters">
        <input id="asset-search" placeholder="Search assets">
        <select id="category-filter">
          <option value="">All categories</option>
          ${state.categories.map((category) => `<option value="${category}">${category}</option>`).join("")}
        </select>
        <button id="filter-assets">Filter</button>
      </div>
    </section>
    ${adminForm}
    <section class="asset-grid">
      ${state.assets.map(assetCard).join("")}
    </section>
  `;

  document.querySelector("#filter-assets").addEventListener("click", async () => {
    await loadAssets(document.querySelector("#asset-search").value, document.querySelector("#category-filter").value);
    renderAssets();
  });

  if (isAdmin()) {
    document.querySelector("#asset-form").addEventListener("submit", saveAsset);
    document.querySelectorAll("[data-edit-asset]").forEach((button) => button.addEventListener("click", fillAssetForm));
    document.querySelectorAll("[data-delete-asset]").forEach((button) => button.addEventListener("click", deleteAsset));
  }
  document.querySelectorAll("[data-book-asset]").forEach((button) => button.addEventListener("click", prepareBooking));
}

function assetCard(asset) {
  return `
    <article class="asset-card">
      <div class="asset-meta"><span>${asset.category}</span><span>${asset.available_now}/${asset.quantity_total} available</span></div>
      <h3>${asset.asset_name}</h3>
      <p>${asset.description || "No description added."}</p>
      <p><span class="status">${asset.status}</span></p>
      <div class="row-actions">
        <button data-book-asset="${asset.id}">Request</button>
        ${isAdmin() ? `<button class="secondary" data-edit-asset="${asset.id}">Edit</button><button class="danger" data-delete-asset="${asset.id}">Delete</button>` : ""}
      </div>
    </article>
  `;
}

async function saveAsset(event) {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(event.target));
  const id = data.id;
  delete data.id;
  data.quantity_total = Number(data.quantity_total);
  await api(id ? `/api/assets/${id}` : "/api/assets", {
    method: id ? "PUT" : "POST",
    body: JSON.stringify(data),
  });
  event.target.reset();
  await loadAssets();
  await loadAnalytics();
  renderAll();
  showToast("Asset saved");
}

function fillAssetForm(event) {
  const asset = state.assets.find((item) => item.id === Number(event.target.dataset.editAsset));
  const form = document.querySelector("#asset-form");
  ["id", "asset_name", "category", "quantity_total", "status", "description"].forEach((field) => {
    form.elements[field].value = asset[field] || "";
  });
}

async function deleteAsset(event) {
  await api(`/api/assets/${event.target.dataset.deleteAsset}`, { method: "DELETE" });
  await loadAssets();
  renderAssets();
  showToast("Asset deleted");
}

function prepareBooking(event) {
  switchView("bookings");
  const select = document.querySelector("#booking-form select[name='asset_id']");
  select.value = event.target.dataset.bookAsset;
  document.querySelector("#booking-form input[name='quantity_requested']").focus();
}

function renderBookings() {
  document.querySelector("#bookings-view").innerHTML = `
    <div class="split">
      <section class="panel">
        <h2>Request Asset</h2>
        <form id="booking-form">
          <label>Asset
            <select name="asset_id" required>
              ${state.assets.map((asset) => `<option value="${asset.id}">${asset.asset_name} (${asset.available_now} available)</option>`).join("")}
            </select>
          </label>
          <label>Quantity <input name="quantity_requested" type="number" min="1" value="1" required></label>
          <label>Start Date <input name="start_date" type="date" required></label>
          <label>End Date <input name="end_date" type="date" required></label>
          <label>Purpose <textarea name="purpose" placeholder="Event, section or use case"></textarea></label>
          <button type="submit">Submit Request</button>
        </form>
      </section>
      <section class="panel">
        <h2>${isAdmin() ? "Approval Queue" : "My Active Requests"}</h2>
        ${bookingTable(state.bookings.filter((booking) => ["pending", "approved", "issued", "overdue"].includes(booking.status)))}
      </section>
    </div>
  `;
  document.querySelector("#booking-form").addEventListener("submit", createBooking);
  bindBookingActions();
}

async function createBooking(event) {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(event.target));
  data.asset_id = Number(data.asset_id);
  data.quantity_requested = Number(data.quantity_requested);
  await api("/api/bookings", { method: "POST", body: JSON.stringify(data) });
  event.target.reset();
  await refreshData();
  showToast("Booking request submitted");
}

function renderHistory() {
  const title = isAdmin() ? "System Activity" : "Borrowing History";
  document.querySelector("#history-view").innerHTML = `
    <section class="panel">
      <h2>${title}</h2>
      ${bookingTable(state.bookings)}
    </section>
  `;
  bindBookingActions();
}

function bookingTable(bookings) {
  if (!bookings.length) {
    return `<p class="hint">No records found.</p>`;
  }
  return `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Asset</th>
            ${isAdmin() ? "<th>User</th>" : ""}
            <th>Dates</th>
            <th>Qty</th>
            <th>Status</th>
            <th>Purpose</th>
            ${isAdmin() ? "<th>Actions</th>" : ""}
          </tr>
        </thead>
        <tbody>
          ${bookings.map((booking) => `
            <tr>
              <td><strong>${booking.asset_name}</strong><br><span class="hint">${booking.category}</span></td>
              ${isAdmin() ? `<td>${booking.user_name}</td>` : ""}
              <td>${booking.start_date} to ${booking.end_date}</td>
              <td>${booking.quantity_requested}</td>
              <td><span class="status ${booking.status}">${booking.status}</span></td>
              <td>${booking.purpose || "-"}</td>
              ${isAdmin() ? `<td>${bookingActions(booking)}</td>` : ""}
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function bookingActions(booking) {
  const actions = [];
  if (booking.status === "pending") {
    actions.push(["approve", "Approve"], ["reject", "Reject"]);
  }
  if (booking.status === "approved") {
    actions.push(["issue", "Issue"]);
  }
  if (booking.status === "issued" || booking.status === "overdue") {
    actions.push(["return", "Return"]);
  }
  return `<div class="row-actions">${actions.map(([action, label]) => `<button data-booking-action="${action}" data-booking-id="${booking.id}">${label}</button>`).join("")}</div>`;
}

function bindBookingActions() {
  document.querySelectorAll("[data-booking-action]").forEach((button) => {
    button.addEventListener("click", async () => {
      await api(`/api/bookings/${button.dataset.bookingId}/${button.dataset.bookingAction}`, { method: "POST" });
      await refreshData();
      showToast("Booking updated");
    });
  });
}

async function refreshData() {
  await Promise.all([loadAssets(), loadBookings(), loadAnalytics()]);
  renderAll();
}

function switchView(viewName) {
  document.querySelectorAll(".tab").forEach((tab) => tab.classList.toggle("active", tab.dataset.view === viewName));
  document.querySelectorAll(".view").forEach((view) => view.classList.add("hidden"));
  document.querySelector(`#${viewName}-view`).classList.remove("hidden");
}

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => switchView(tab.dataset.view));
});

document.querySelector("#toggle-auth").addEventListener("click", () => {
  state.authMode = state.authMode === "login" ? "register" : "login";
  document.querySelector("#auth-title").textContent = state.authMode === "login" ? "Log in" : "Create account";
  document.querySelector("#auth-submit").textContent = state.authMode === "login" ? "Log in" : "Register";
  document.querySelector("#toggle-auth").textContent = state.authMode === "login" ? "Create a user account" : "Back to login";
  document.querySelector("#name-field").style.display = state.authMode === "login" ? "none" : "grid";
});

authForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(authForm));
  try {
    const result = await api(state.authMode === "login" ? "/api/login" : "/api/register", {
      method: "POST",
      body: JSON.stringify(data),
    });
    state.user = result.user;
    await loadDashboard();
  } catch (error) {
    showToast(error.message);
  }
});

document.querySelector("#logout-button").addEventListener("click", async () => {
  await api("/api/logout", { method: "POST" });
  state.user = null;
  showAuth();
});

document.querySelector("#name-field").style.display = "none";
boot();
