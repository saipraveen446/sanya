import { useEffect, useState } from "react";
import { fetchHealth, fetchSkills } from "./api";
import ExpenseDashboard from "./skills/ExpenseDashboard";
import NewsDashboard from "./skills/NewsDashboard";
import RemindersDashboard from "./skills/RemindersDashboard";
import TodoDashboard from "./skills/TodoDashboard";

const SKILL_META = {
  expense_tracking: { icon: "💰", label: "Expenses" },
  reminders: { icon: "⏰", label: "Reminders" },
  todo: { icon: "✅", label: "Todo" },
  news: { icon: "📰", label: "News" },
};

const FALLBACK_SKILLS = [
  { id: "expense_tracking", name: "Expenses", ready: true },
  { id: "reminders", name: "Reminders", ready: true },
  { id: "todo", name: "Todo", ready: true },
  { id: "news", name: "News", ready: true },
];

export default function App() {
  const [skillId, setSkillId] = useState("expense_tracking");
  const [boardKey, setBoardKey] = useState(0);
  const [skills, setSkills] = useState(FALLBACK_SKILLS);
  const [health, setHealth] = useState({ telegram: false, llm: false });
  const [error, setError] = useState("");

  useEffect(() => {
    fetchSkills()
      .then((items) => setSkills(items.length ? items : FALLBACK_SKILLS))
      .catch(() => setSkills(FALLBACK_SKILLS));
    fetchHealth()
      .then(setHealth)
      .catch(() => setHealth({ telegram: false, llm: false }));
  }, []);

  const llmOn = Boolean(health.llm);
  const llmLabel = health.llm_provider ? `LLM ${health.llm_provider}` : llmOn ? "LLM on" : "LLM fallback";

  function renderSkill() {
    if (skillId === "reminders") return <RemindersDashboard key={boardKey} onError={setError} />;
    if (skillId === "todo") return <TodoDashboard key={boardKey} onError={setError} />;
    if (skillId === "news") return <NewsDashboard key={boardKey} onError={setError} />;
    return <ExpenseDashboard key={boardKey} onError={setError} />;
  }

  return (
    <div className="shell">
      <aside className="skill-nav">
        <div className="brand">
          <p className="eyebrow">Personal assistant</p>
          <h1>Sanya</h1>
        </div>
        <div className="status">
          <span className={`pill ${health.telegram ? "on" : ""}`}>Telegram {health.telegram ? "on" : "off"}</span>
          <span className={`pill ${llmOn ? "on" : ""}`}>{llmLabel}</span>
        </div>
        {skills.map((item) => {
          const meta = SKILL_META[item.id] || { icon: "•", label: item.name };
          return (
            <button
              key={item.id}
              className={item.id === skillId ? "active" : ""}
              type="button"
              onClick={() => {
                setError("");
                if (item.id === skillId) setBoardKey((n) => n + 1);
                setSkillId(item.id);
              }}
            >
              <span className="nav-label">
                <span className="nav-icon">{meta.icon}</span>
                {meta.label}
              </span>
            </button>
          );
        })}
      </aside>
      <main className="app">
        {error ? <p className="error">{error}</p> : null}
        {renderSkill()}
      </main>
    </div>
  );
}
