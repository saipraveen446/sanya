const API = (import.meta.env.VITE_API_URL ?? "") + "/api";

async function read(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || "Request failed");
  }
  return res.json();
}

function apiFetch(path, options = {}) {
  return fetch(`${API}${path}`, { cache: "no-store", ...options }).then(read);
}

export function fetchHealth() {
  return apiFetch("/health");
}

export function fetchSummary(period) {
  return apiFetch(`/summaries?period=${period}`);
}

export function fetchExpenses(period) {
  const query = period ? `?period=${period}` : "";
  return apiFetch(`/expenses${query}`);
}

export function addExpense(payload) {
  return apiFetch("/expenses", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function deleteExpense(id) {
  return apiFetch(`/expenses/${id}`, { method: "DELETE" });
}

export function fetchCategories() {
  return apiFetch("/categories");
}

export function addCategory(payload) {
  return apiFetch("/categories", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function fetchSkills() {
  return apiFetch("/skills");
}

export function parseSkillText(text, skill) {
  return apiFetch("/skills/parse", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, skill }),
  });
}

export function handleSkill(text, skill, telegramUserId = "") {
  return apiFetch("/skills/handle", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, skill, telegram_user_id: telegramUserId }),
  });
}

export function fetchReminders(includeDone = true) {
  return apiFetch(`/reminders?include_done=${includeDone}`);
}

export function addReminder(payload) {
  return apiFetch("/reminders", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function updateReminder(id, payload) {
  return apiFetch(`/reminders/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function deleteReminder(id) {
  return apiFetch(`/reminders/${id}`, { method: "DELETE" });
}

export function fetchTodos(status = "open") {
  return apiFetch(`/todos?status=${status}`);
}

export function addTodo(payload) {
  return apiFetch("/todos", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function updateTodo(id, payload) {
  return apiFetch(`/todos/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function deleteTodo(id) {
  return apiFetch(`/todos/${id}`, { method: "DELETE" });
}

export function fetchNews(topic = "tech", day, refresh = false) {
  const params = new URLSearchParams({ topic, limit: "12" });
  if (day) params.set("day", day);
  if (refresh) params.set("refresh", "true");
  return apiFetch(`/news?${params}`);
}
