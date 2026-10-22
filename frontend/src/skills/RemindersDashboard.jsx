import { useEffect, useMemo, useState } from "react";
import { addReminder, deleteReminder, fetchReminders, updateReminder } from "../api";
import { useLiveRefresh } from "../useLiveRefresh";

function pad(value) {
  return String(value).padStart(2, "0");
}

function splitLocal(date) {
  return {
    date: `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`,
    time: `${pad(date.getHours())}:${pad(date.getMinutes())}`,
  };
}

function inOneHour() {
  const next = new Date(Date.now() + 60 * 60 * 1000);
  next.setSeconds(0, 0);
  return splitLocal(next);
}

function addMinutesFromNow(minutes) {
  const next = new Date(Date.now() + minutes * 60 * 1000);
  next.setSeconds(0, 0);
  return splitLocal(next);
}

function atHour(hour, { daysAhead = 0 } = {}) {
  const next = new Date();
  next.setDate(next.getDate() + daysAhead);
  next.setHours(hour, 0, 0, 0);
  if (next.getTime() <= Date.now()) next.setDate(next.getDate() + 1);
  return splitLocal(next);
}

function startOfDay(value) {
  const date = new Date(value);
  date.setHours(0, 0, 0, 0);
  return date.getTime();
}

function isToday(value) {
  return Boolean(value) && startOfDay(value) === startOfDay(new Date());
}

function dueMeta(value) {
  const due = new Date(value);
  const now = Date.now();
  const today = startOfDay(now);
  const dueDay = startOfDay(due);
  const time = due.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
  const day = due.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  if (due.getTime() < now) return { label: `${day} · ${time}`, kind: "overdue" };
  if (dueDay === today) return { label: `Today · ${time}`, kind: "today" };
  if (dueDay === today + 86400000) return { label: `Tomorrow · ${time}`, kind: "soon" };
  return { label: `${day} · ${time}`, kind: "later" };
}

function ClockIcon() {
  return (
    <svg viewBox="0 0 20 20" width="14" height="14" aria-hidden="true">
      <circle cx="10" cy="10" r="7.2" fill="none" stroke="currentColor" strokeWidth="1.6" />
      <path d="M10 6.2V10l2.6 1.8" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

const PRESETS = [
  { id: "30m", label: "In 30 min", when: () => addMinutesFromNow(30) },
  { id: "1h", label: "In 1 hour", when: () => addMinutesFromNow(60) },
  { id: "tonight", label: "Tonight 8pm", when: () => atHour(20) },
  { id: "tomorrow", label: "Tomorrow 9am", when: () => atHour(9, { daysAhead: 1 }) },
];

export default function RemindersDashboard({ onError }) {
  const [items, setItems] = useState([]);
  const [tab, setTab] = useState("upcoming");
  const [search, setSearch] = useState("");
  const [filterDate, setFilterDate] = useState("");
  const [form, setForm] = useState(inOneHour());
  const [title, setTitle] = useState("");
  const [editingId, setEditingId] = useState(null);
  const [edit, setEdit] = useState({ date: "", time: "" });

  async function load() {
    setItems(await fetchReminders(true));
  }

  useEffect(() => {
    load().catch(() => onError("Could not load reminders."));
  }, []);

  useLiveRefresh(load);

  async function submit(event) {
    event.preventDefault();
    if (!title.trim() || !form.date || !form.time) return;
    onError("");
    try {
      await addReminder({
        title: title.trim(),
        due_at: new Date(`${form.date}T${form.time}:00`).toISOString(),
        source: "web",
        telegram_user_id: "",
      });
      setTitle("");
      setForm(inOneHour());
      await load();
    } catch {
      onError("Could not add that reminder.");
    }
  }

  async function complete(id, isDone) {
    onError("");
    try {
      await updateReminder(id, { is_done: isDone });
      await load();
    } catch {
      onError("Could not update that reminder.");
    }
  }

  async function snooze(id, dueAt) {
    onError("");
    try {
      const next = new Date(new Date(dueAt).getTime() + 60 * 60 * 1000);
      await updateReminder(id, { due_at: next.toISOString() });
      setEditingId(null);
      await load();
    } catch {
      onError("Could not snooze that reminder.");
    }
  }

  function startEdit(item) {
    setEditingId(item.id);
    setEdit(splitLocal(new Date(item.due_at)));
  }

  async function saveWhen(event, id) {
    event.preventDefault();
    if (!edit.date || !edit.time) return;
    onError("");
    try {
      await updateReminder(id, {
        due_at: new Date(`${edit.date}T${edit.time}:00`).toISOString(),
      });
      setEditingId(null);
      await load();
    } catch {
      onError("Could not update that date or time.");
    }
  }

  async function remove(id) {
    onError("");
    try {
      await deleteReminder(id);
      await load();
    } catch {
      onError("Could not delete that reminder.");
    }
  }

  const visible = useMemo(() => {
    const now = Date.now();
    return items.filter((item) => {
      const due = new Date(item.due_at).getTime();
      if (tab === "upcoming" && (item.is_done || due < now)) return false;
      if (tab === "today" && !isToday(item.due_at)) return false;
      if (tab === "overdue" && (item.is_done || due >= now)) return false;
      if (tab === "done" && !item.is_done) return false;
      if (search && !item.title.toLowerCase().includes(search.toLowerCase())) return false;
      if (filterDate && item.due_at.slice(0, 10) !== filterDate) return false;
      return true;
    });
  }, [items, tab, search, filterDate]);

  const now = Date.now();
  const counts = {
    upcoming: items.filter((item) => !item.is_done && new Date(item.due_at).getTime() >= now).length,
    today: items.filter((item) => isToday(item.due_at)).length,
    overdue: items.filter((item) => !item.is_done && new Date(item.due_at).getTime() < now).length,
    done: items.filter((item) => item.is_done).length,
  };

  return (
    <div className="todo-page">
      <header className="page-head">
        <div>
          <h2>Reminders</h2>
          <p className="subtitle">Telegram pings you when you add one, 15 minutes before, and at the due time.</p>
        </div>
      </header>

      <form className="todo-composer reminder-composer" onSubmit={submit}>
        <label className="todo-field grow">
          Reminder
          <input
            placeholder="What should I remind you?"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            required
          />
        </label>
        <label className="todo-field">
          Date
          <input
            type="date"
            value={form.date}
            onChange={(event) => setForm((current) => ({ ...current, date: event.target.value }))}
            required
          />
        </label>
        <label className="todo-field">
          Time
          <input
            type="time"
            value={form.time}
            onChange={(event) => setForm((current) => ({ ...current, time: event.target.value }))}
            required
          />
        </label>
        <button className="todo-add-btn" type="submit">
          Add Reminder
        </button>
        <div className="reminder-presets">
          {PRESETS.map((preset) => (
            <button
              key={preset.id}
              className="reminder-chip"
              type="button"
              onClick={() => setForm(preset.when())}
            >
              {preset.label}
            </button>
          ))}
        </div>
      </form>

      <section className="todo-toolbar">
        <div className="todo-search-row">
          <input
            className="todo-search"
            placeholder="Search reminders..."
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
            { id: "upcoming", label: "Upcoming", count: counts.upcoming },
            { id: "today", label: "Today", count: counts.today },
            { id: "overdue", label: "Overdue", count: counts.overdue },
            { id: "done", label: "Done", count: counts.done },
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
            <strong>No reminders here</strong>
            <p>Add one above, or switch the filter.</p>
          </div>
        ) : null}
        {visible.map((item) => {
          const due = dueMeta(item.due_at);
          const tone = item.is_done ? "done" : due.kind === "overdue" ? "overdue" : due.kind === "today" ? "today" : "";
          return (
            <article className={`todo-row ${tone}`} key={item.id}>
              <div className="todo-copy">
                <strong>{item.title}</strong>
                {editingId === item.id ? (
                  <form className="reminder-edit" onSubmit={(event) => saveWhen(event, item.id)}>
                    <label className="todo-field">
                      Date
                      <input
                        type="date"
                        value={edit.date}
                        onChange={(event) => setEdit((current) => ({ ...current, date: event.target.value }))}
                        required
                      />
                    </label>
                    <label className="todo-field">
                      Time
                      <input
                        type="time"
                        value={edit.time}
                        onChange={(event) => setEdit((current) => ({ ...current, time: event.target.value }))}
                        required
                      />
                    </label>
                    <button className="reminder-save" type="submit">
                      Save
                    </button>
                    <button className="reminder-cancel" type="button" onClick={() => setEditingId(null)}>
                      Cancel
                    </button>
                  </form>
                ) : (
                  <button className={`todo-due ${due.kind}`} type="button" onClick={() => startEdit(item)}>
                    <ClockIcon />
                    {due.label}
                    {item.notified_at ? <em className="reminder-alerted">Alerted</em> : null}
                    <span className="reminder-edit-hint">Edit</span>
                  </button>
                )}
              </div>
              <div className="todo-actions">
                <button className="todo-edit" type="button" onClick={() => startEdit(item)} aria-label="Edit date and time">
                  Edit
                </button>
                {!item.is_done ? (
                  <>
                    <button
                      className="todo-snooze"
                      type="button"
                      onClick={() => snooze(item.id, item.due_at)}
                      aria-label="Add 1 hour to due time"
                    >
                      +1h
                    </button>
                    <button
                      className="todo-check"
                      type="button"
                      onClick={() => complete(item.id, true)}
                      aria-label="Mark done"
                    >
                      ✓
                    </button>
                  </>
                ) : null}
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
