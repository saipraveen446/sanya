export default function SummaryCards({ summary, periodLabel = "this period" }) {
  const topCategory = summary.by_category[0];
  const topMerchant = summary.by_merchant[0];
  const average = summary.count ? Number(summary.total) / summary.count : 0;

  return (
    <section className="cards expense-stats">
      <article className="stat-card stat-total">
        <span>Total spent</span>
        <strong className="money">
          {summary.currency} {Number(summary.total).toFixed(2)}
        </strong>
        <p>{periodLabel}</p>
      </article>
      <article className="stat-card stat-count">
        <span>Transactions</span>
        <strong className="money">{summary.count}</strong>
        <p>{summary.count ? `Avg ${summary.currency} ${average.toFixed(2)}` : "No spends yet"}</p>
      </article>
      <article className="stat-card stat-category">
        <span>Top category</span>
        <strong>{topCategory ? topCategory.name : "—"}</strong>
        <p>
          {topCategory ? `${summary.currency} ${Number(topCategory.total).toFixed(2)}` : "Add a spend to see this"}
        </p>
      </article>
      <article className="stat-card stat-place">
        <span>Top place</span>
        <strong>{topMerchant ? topMerchant.name : "—"}</strong>
        <p>
          {topMerchant ? `${summary.currency} ${Number(topMerchant.total).toFixed(2)}` : "Places show when you add Where"}
        </p>
      </article>
    </section>
  );
}
