import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

const COLORS = ["#5b86ff", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#ec4899", "#84cc16"];

export default function BreakdownChart({ items, currency, total = 0 }) {
  const data = items.map((item) => ({ ...item, total: Number(item.total) }));
  const max = Number(total) || data.reduce((sum, item) => sum + item.total, 0);

  if (!data.length) {
    return <p className="empty">No category spend for this period.</p>;
  }

  return (
    <div>
      <div className="expense-pie">
        <ResponsiveContainer width="100%" height={180}>
          <PieChart>
            <Pie data={data} dataKey="total" nameKey="name" innerRadius={48} outerRadius={72} paddingAngle={3}>
              {data.map((entry, index) => (
                <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value, name) => [`${currency} ${Number(value).toFixed(2)}`, name]}
              contentStyle={{ background: "#ffffff", border: "1px solid #e5eaf2", borderRadius: 12 }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      {data.map((item) => {
        const pct = max ? Math.max(6, (item.total / max) * 100) : 0;
        return (
          <div className="spend-bar" key={item.name}>
            <div className="spend-bar-meta">
              <strong>{item.name}</strong>
              <span>
                {currency} {item.total.toFixed(2)}
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
