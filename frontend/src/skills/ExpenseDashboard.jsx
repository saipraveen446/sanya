import { useEffect, useRef, useState } from "react";
import AddExpenseForm from "../components/AddExpenseForm";
import BreakdownChart from "../components/BreakdownChart";
import ExpenseTable from "../components/ExpenseTable";
import MerchantList from "../components/MerchantList";
import SummaryCards from "../components/SummaryCards";
import { addCategory, addExpense, deleteExpense, fetchCategories, fetchExpenses, fetchSummary } from "../api";
import { useLiveRefresh } from "../useLiveRefresh";

const PERIODS = [
  { id: "today", label: "Today" },
  { id: "week", label: "This week" },
  { id: "month", label: "This month" },
];

function kolkataDay(value = new Date()) {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Kolkata",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(value);
}

export default function ExpenseDashboard({ onError }) {
  const [tab, setTab] = useState("summary");
  const [period, setPeriod] = useState("month");
  const [summary, setSummary] = useState(null);
  const [expenses, setExpenses] = useState([]);
  const [categories, setCategories] = useState([]);
  const periodRef = useRef(period);
  periodRef.current = period;

  async function load(nextPeriod = periodRef.current) {
    const [nextSummary, nextExpenses, nextCategories] = await Promise.all([
      fetchSummary(nextPeriod),
      fetchExpenses(nextPeriod),
      fetchCategories().catch(() => []),
    ]);
    setSummary(nextSummary);
    setExpenses(nextExpenses);
    setCategories(nextCategories);
  }

  useEffect(() => {
    let cancelled = false;
    load(period).catch(() => {
      if (!cancelled) onError("Could not reach the API. Start the backend first.");
    });
    return () => {
      cancelled = true;
    };
  }, [period, tab]);

  useLiveRefresh(() => load());

  function periodForSpend(spentAt) {
    const spentDay = spentAt ? String(spentAt).slice(0, 10) : kolkataDay();
    if (spentDay === kolkataDay()) return periodRef.current;
    if (periodRef.current === "today") return "month";
    return periodRef.current;
  }

  async function handleAdd(payload) {
    onError("");
    try {
      await addExpense(payload);
      const nextPeriod = periodForSpend(payload.spent_at);
      if (nextPeriod !== periodRef.current) setPeriod(nextPeriod);
      await load(nextPeriod);
      setTab("history");
    } catch (err) {
      onError(err.message || "Could not add that spend.");
    }
  }

  async function handleAddCategory(payload) {
    onError("");
    const created = await addCategory(payload);
    await load();
    return created;
  }

  async function handleDelete(id) {
    onError("");
    try {
      await deleteExpense(id);
      await load();
    } catch (err) {
      onError(err.message || "Could not remove that spend.");
    }
  }

  return (
    <div className="expense-page">
      <header className="page-head">
        <div>
          <h2>Expenses</h2>
          <p className="subtitle">Web and Telegram share the same spends.</p>
        </div>
        <div className="head-actions">
          <nav className="tabs">
            <button
              className={tab === "summary" ? "active" : ""}
              onClick={() => {
                if (tab === "summary") load().catch(() => {});
                setTab("summary");
              }}
              type="button"
            >
              Summary
            </button>
            <button
              className={tab === "history" ? "active" : ""}
              onClick={() => {
                if (tab === "history") load().catch(() => {});
                setTab("history");
              }}
              type="button"
            >
              History
            </button>
          </nav>
          <button className={tab === "add" ? "primary" : "primary ghost-primary"} onClick={() => setTab("add")} type="button">
            + Add
          </button>
        </div>
      </header>

      {tab === "add" ? (
        <AddExpenseForm categories={categories} onAdd={handleAdd} onAddCategory={handleAddCategory} />
      ) : null}

      {tab === "summary" ? (
        <>
          <section className="todo-toolbar">
            <nav className="todo-filters">
              {PERIODS.map((item) => (
                <button key={item.id} className={period === item.id ? "active" : ""} onClick={() => setPeriod(item.id)} type="button">
                  {item.label}
                </button>
              ))}
            </nav>
          </section>
          {summary ? (
            <SummaryCards
              summary={summary}
              periodLabel={PERIODS.find((item) => item.id === period)?.label?.toLowerCase() || "this period"}
            />
          ) : null}
          <section className="grid expense-split">
            <div className="todo-toolbar">
              <h3>By category</h3>
              <BreakdownChart
                items={summary?.by_category || []}
                currency={summary?.currency || "INR"}
                total={summary?.total || 0}
              />
            </div>
            <div className="todo-toolbar">
              <h3>By place</h3>
              <MerchantList items={summary?.by_merchant || []} currency={summary?.currency || "INR"} />
            </div>
          </section>
        </>
      ) : null}

      {tab === "history" ? (
        <>
          <section className="todo-toolbar">
            <nav className="todo-filters">
              {PERIODS.map((item) => (
                <button key={item.id} className={period === item.id ? "active" : ""} onClick={() => setPeriod(item.id)} type="button">
                  {item.label}
                </button>
              ))}
            </nav>
          </section>
          <ExpenseTable expenses={expenses} onDelete={handleDelete} />
        </>
      ) : null}
    </div>
  );
}
