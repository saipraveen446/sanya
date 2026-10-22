export default function MerchantList({ items, currency }) {
  if (!items.length) {
    return <p className="empty">No places logged yet.</p>;
  }

  const max = items.reduce((sum, item) => Math.max(sum, Number(item.total)), 0);

  return (
    <div>
      {items.slice(0, 8).map((item) => {
        const value = Number(item.total);
        const pct = max ? Math.max(6, (value / max) * 100) : 0;
        return (
          <div className="spend-bar" key={item.name}>
            <div className="spend-bar-meta">
              <strong>{item.name}</strong>
              <span>
                {currency} {value.toFixed(2)}
              </span>
            </div>
            <div className="spend-bar-track">
              <i style={{ width: `${pct}%` }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
