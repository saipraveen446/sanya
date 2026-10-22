import { useEffect, useMemo, useState } from "react";

const GROUPS = ["Food & home", "Daily life", "Family", "Savings & money", "Insurance"];

function kolkataDate(value = new Date()) {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Kolkata",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(value);
}

export default function AddExpenseForm({ categories, onAdd, onAddCategory }) {
  const defaultCategory = categories[0]?.name || "Miscellaneous";
  const [form, setForm] = useState({
    amount: "",
    date: kolkataDate(),
    category: defaultCategory,
    merchant: "",
    description: "",
  });
  const [newCategory, setNewCategory] = useState("");
  const [newGroup, setNewGroup] = useState("Daily life");

  useEffect(() => {
    if (!categories.length) return;
    setForm((current) => {
      if (categories.some((item) => item.name === current.category)) return current;
      return { ...current, category: categories[0].name };
    });
  }, [categories]);

  const grouped = useMemo(() => {
    const buckets = {};
    for (const item of categories) {
      buckets[item.group_name] = buckets[item.group_name] || [];
      buckets[item.group_name].push(item);
    }
    return buckets;
  }, [categories]);

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function submit(event) {
    event.preventDefault();
    if (!form.amount) return;
    await onAdd({
      amount: Number(form.amount),
      category: form.category || defaultCategory,
      merchant: form.merchant || null,
      description: form.description || form.category,
      spent_at: `${form.date}T12:00:00+05:30`,
      source: "web",
      telegram_user_id: "",
    });
    setForm({
      amount: "",
      date: form.date || kolkataDate(),
      category: form.category || defaultCategory,
      merchant: "",
      description: "",
    });
  }

  async function submitCategory(event) {
    event.preventDefault();
    const name = newCategory.trim();
    if (!name) return;
    const created = await onAddCategory({ name, group_name: newGroup, keywords: name.toLowerCase() });
    setNewCategory("");
    setForm((current) => ({ ...current, category: created.name }));
  }

  return (
    <>
      <form className="todo-composer expense-composer" onSubmit={submit}>
        <label className="todo-field">
          Amount
          <input
            type="number"
            min="0.01"
            step="0.01"
            placeholder="80"
            value={form.amount}
            onChange={(event) => update("amount", event.target.value)}
            required
          />
        </label>
        <label className="todo-field">
          Date
          <input type="date" value={form.date} onChange={(event) => update("date", event.target.value)} required />
        </label>
        <label className="todo-field grow">
          Category
          <select value={form.category} onChange={(event) => update("category", event.target.value)}>
            {Object.entries(grouped).map(([group, items]) => (
              <optgroup key={group} label={group}>
                {items.map((item) => (
                  <option key={item.id} value={item.name}>
                    {item.name}
                  </option>
                ))}
              </optgroup>
            ))}
          </select>
        </label>
        <button className="todo-add-btn" type="submit">
          Add spend
        </button>
        <div className="expense-composer-row">
          <label className="todo-field">
            Where
            <input
              placeholder="Shop or app"
              value={form.merchant}
              onChange={(event) => update("merchant", event.target.value)}
            />
          </label>
          <label className="todo-field">
            What
            <input
              placeholder="What you bought"
              value={form.description}
              onChange={(event) => update("description", event.target.value)}
            />
          </label>
        </div>
      </form>

      <form className="todo-toolbar expense-category-form" onSubmit={submitCategory}>
        <label className="todo-field grow">
          New category
          <input
            placeholder="e.g. Snacks"
            value={newCategory}
            onChange={(event) => setNewCategory(event.target.value)}
          />
        </label>
        <label className="todo-field">
          Group
          <select value={newGroup} onChange={(event) => setNewGroup(event.target.value)}>
            {GROUPS.map((group) => (
              <option key={group}>{group}</option>
            ))}
          </select>
        </label>
        <button className="todo-add-btn" type="submit">
          Add category
        </button>
      </form>
    </>
  );
}
