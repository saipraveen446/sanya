import { useEffect, useMemo, useState } from "react";
import { addTodo, deleteTodo, fetchTodos, updateTodo } from "../api";
import { useLiveRefresh } from "../useLiveRefresh";

function todayISO() {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}

function startOfDay(value) {
  const date = new Date(value);
  date.setHours(0, 0, 0, 0);
  return date.getTime();
}

function dueMeta(value) {
  if (!value) return { label: "No date", kind: "none" };
  const today = startOfDay(new Date());
  const due = startOfDay(value);
  const label = new Date(value).toLocaleDateString(undefined, { month: "short", day: "numeric" });
  if (due === today) return { label, kind: "today" };
  if (due === today + 86400000) return { label, kind: "soon" };
  if (due < today) return { label, kind: "overdue" };
  return { label, kind: "later" };
}

function CalendarIcon() {
  return (
    <svg viewBox="0 0 20 20" width="14" height="14" aria-hidden="true">
      <rect x="2.5" y="4" width="15" height="13.5" rx="2.5" fill="none" stroke="currentColor" strokeWidth="1.6" />
      <path d="M2.5 8h15M6.5 2.5v3.2M13.5 2.5v3.2" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

function isToday(value) {
  return Boolean(value) && startOfDay(value) === startOfDay(new Date());
}

export default function TodoDashboard({ onError }) {
  const [items, setItems] = useState([]);
  const [tab, setTab] = useState("all");
  const [search, setSearch] = useState("");
  const [filterDate, setFilterDate] = useState("");
  const [form, setForm] = useState({ title: "", due_at: todayISO() });

  async function load() {
    setItems(await fetchTodos("all"));
  }

  useEffect(() => {
    load().catch(() => onError("Could not load todos."));
  }, []);

  useLiveRefresh(load);

  async function submit(event) {
    event.preventDefault();
    if (!form.title.trim()) return;
    onError("");
    try {
      await addTodo({
        title: form.title.trim(),
        due_at: form.due_at ? new Date(`${form.due_at}T09:00:00`).toISOString() : null,
        source: "web",
        telegram_user_id: "",
      });
      setForm({ title: "", due_at: todayISO() });
      await load();
    } catch {
      onError("Could not add that todo.");
    }
  }

  async function complete(id, isDone) {
    onError("");
    try {
      await updateTodo(id, { is_done: isDone });
      await load();
    } catch {
      onError("Could not update that todo.");
    }
  }

  async function remove(id) {
    onError("");
    try {
      await deleteTodo(id);
      await load();
    } catch {
      onError("Could not delete that todo.");
    }
  }

  const visible = useMemo(() => {
    return items.filter((item) => {
      if (tab === "today" && !isToday(item.due_at)) return false;
      if (tab === "pending" && item.is_done) return false;
      if (tab === "done" && !item.is_done) return false;
      if (search && !item.title.toLowerCase().includes(search.toLowerCase())) return false;
      if (filterDate && (!item.due_at || item.due_at.slice(0, 10) !== filterDate)) return false;
      return true;
    });
  }, [items, tab, search, filterDate]);

  const counts = {
    all: items.length,
    today: items.filter((item) => isToday(item.due_at)).length,
    pending: items.filter((item) => !item.is_done).length,
    done: items.filter((item) => item.is_done).length,
  };

  return (
    <div className="todo-page">
      <header className="page-head">
        <div>
          <h2>Todo</h2>
        </div>
      </header>

      <form className="todo-composer" onSubmit={submit}>
        <label className="todo-field grow">
          Task Description
          <input
            placeholder="What needs to be done?"
            value={form.title}
            onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
            required
          />
        </label>
        <label className="todo-field">
          Due Date
          <input
            type="date"
            value={form.due_at}
            onChange={(event) => setForm((current) => ({ ...current, due_at: event.target.value }))}
          />
        </label>
        <button className="todo-add-btn" type="submit">
          Add Task
        </button>
      </form>

      <section className="todo-toolbar">
        <div className="todo-search-row">
          <input
            className="todo-search"
            placeholder="Search tasks..."
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
          <input
            type="date"
            value={filterDate}
            onChange={(event) => setFilterDate(event.target.value)}
          />
          <button
            className="todo-clear"
            type="button"
            onClick={() => {
              setSearch("");
              setFilterDate("");
            }}
          >
            Clear
          </button>
        </div>
        <nav className="todo-filters">
          {[
            { id: "all", label: "All", count: counts.all },
            { id: "today", label: "Today", count: counts.today },
            { id: "pending", label: "Pending", count: counts.pending },
            { id: "done", label: "Completed", count: counts.done },
          ].map((item) => (
            <button
              key={item.id}
              className={tab === item.id ? "active" : ""}
              type="button"
              onClick={() => setTab(item.id)}
            >
              {item.label}
              <span>{item.count}</span>
            </button>
          ))}
        </nav>
      </section>

      <section className="todo-list">
        {!visible.length ? (
          <div className="todo-empty">
            <strong>No tasks here</strong>
            <p>Add one above, or switch the filter.</p>
          </div>
        ) : null}
        {visible.map((item) => {
          const due = dueMeta(item.due_at);
          const tone = item.is_done ? "done" : due.kind === "today" ? "today" : due.kind === "overdue" ? "overdue" : "";
          return (
            <article className={`todo-row ${tone}`} key={item.id}>
              <div className="todo-copy">
                <strong>{item.title}</strong>
                <div className={`todo-due ${due.kind}`}>
                  <CalendarIcon />
                  {due.label}
                </div>
              </div>
              <div className="todo-actions">
                <button
                  className="todo-check"
                  type="button"
                  onClick={() => complete(item.id, !item.is_done)}
                  aria-label={item.is_done ? "Mark pending" : "Mark complete"}
                >
                  ✓
                </button>
                <button className="todo-delete" type="button" onClick={() => remove(item.id)} aria-label="Delete">
                  ×
                </button>
              </div>
            </article>
          );
        })}
      </section>
    </div>
  );
}
