import { useEffect, useState } from "react";

export default function ExpenseTable({ expenses, onDelete }) {
  const [pending, setPending] = useState(null);

  useEffect(() => {
    if (!pending) return undefined;
    function onKey(event) {
      if (event.key === "Escape") setPending(null);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [pending]);

  if (!expenses.length) {
    return (
      <div className="todo-empty">
        <strong>No expenses in this period</strong>
        <p>Add one here or send it to Telegram.</p>
      </div>
    );
  }

  return (
    <>
      <section className="todo-list">
        {expenses.map((item) => (
          <article className="todo-row spend-row" key={item.id}>
            <div className="todo-copy">
              <strong>{item.description || item.category}</strong>
              <div className="todo-due later">
                {new Date(item.spent_at).toLocaleDateString(undefined, { day: "numeric", month: "short" })}
                {" · "}
                {item.category}
                {item.merchant ? ` · ${item.merchant}` : ""}
              </div>
            </div>
            <div className="spend-amount">
              {item.currency} {Number(item.amount).toFixed(2)}
            </div>
            <button className="todo-delete" onClick={() => setPending(item)} type="button" aria-label="Remove">
              ×
            </button>
          </article>
        ))}
      </section>

      {pending ? (
        <div className="confirm-overlay" onClick={() => setPending(null)} role="presentation">
          <div
            className="confirm-card"
            role="dialog"
            aria-modal="true"
            aria-labelledby="expense-remove-title"
            onClick={(event) => event.stopPropagation()}
          >
            <h3 id="expense-remove-title">Remove this spend?</h3>
            <p>
              {pending.description || pending.category} · {pending.currency} {Number(pending.amount).toFixed(2)}
            </p>
            <div className="confirm-actions">
              <button className="ghost-btn" type="button" onClick={() => setPending(null)}>
                Cancel
              </button>
              <button
                className="danger-btn"
                type="button"
                onClick={() => {
                  const id = pending.id;
                  setPending(null);
                  onDelete(id);
                }}
              >
                Remove
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
