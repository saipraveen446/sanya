from decimal import Decimal

from app.database import SessionLocal
from app.origin import record_origin
from app.skills.base import Skill, SkillResult
from app.skills.expense_tracking.parser import parse_expense_messages
from app.skills.expense_tracking.service import create_expense, get_summary
from app.time import now_local


def _money(amount: Decimal, currency: str) -> str:
    return f"{currency} {amount:,.2f}"


def _when(value) -> str:
    return value.astimezone(now_local().tzinfo).strftime("%d %b")


class ExpenseTrackingSkill(Skill):
    id = "expense_tracking"
    name = "Expense Tracking"
    description = "Log spends, categories, and daily / weekly / monthly totals."
    ready = True
    keywords = (
        "spent",
        "spend",
        "paid",
        "bought",
        "rs",
        "inr",
        "₹",
        "petrol",
        "tiffin",
        "milk",
        "rent",
        "gym",
        "expense",
        "bill",
        "coffee",
        "swiggy",
        "zomato",
    )
    examples = ("tiffin 80", "oct 1 tiffin 135", "october 2nd\nfish 300\nlemon juice 10")
    commands = ("/expenses", "/today", "/week", "/month", "/list", "/categories", "/addcategory", "/undo")

    async def parse(self, text: str) -> SkillResult:
        lowered = text.lower().strip()
        if lowered in {"summary", "expense summary", "today", "week", "month"} or "summary" in lowered:
            period = "month"
            if "today" in lowered:
                period = "today"
            elif "week" in lowered:
                period = "week"
            return SkillResult(
                skill_id=self.id,
                ok=True,
                message="summary",
                data={"action": "summary", "period": period},
            )
        if lowered in {"history", "list", "expense history", "recent"} or "history" in lowered:
            return SkillResult(skill_id=self.id, ok=True, message="history", data={"action": "history"})
        try:
            payloads = await parse_expense_messages(text)
        except ValueError as exc:
            return SkillResult(skill_id=self.id, ok=False, message=str(exc))
        preview = ", ".join(f"{item.description} {_money(item.amount, item.currency)}" for item in payloads[:6])
        return SkillResult(
            skill_id=self.id,
            ok=True,
            message=preview,
            data={"action": "create", "items": [item.model_dump(mode="json") for item in payloads]},
            payload=payloads,
        )

    async def execute(self, parsed: SkillResult, *, telegram_user_id: str | None = None) -> SkillResult:
        action = (parsed.data or {}).get("action") or "create"
        if action == "summary":
            period = (parsed.data or {}).get("period") or "month"
            async with SessionLocal() as session:
                summary = await get_summary(session, period)
            return SkillResult(
                skill_id=self.id,
                ok=True,
                message=f"{period.title()} total: {_money(summary.total, summary.currency)} · {summary.count} spends",
                data=summary.model_dump(mode="json"),
            )
        if action == "history":
            from app.skills.expense_tracking.service import list_expenses

            async with SessionLocal() as session:
                expenses = await list_expenses(session, limit=10)
            if not expenses:
                return SkillResult(skill_id=self.id, ok=True, message="No expenses yet.", data={"items": []})
            lines = ["<b>Expense history</b>"]
            for item in expenses:
                place = f" at {item.merchant}" if item.merchant else ""
                lines.append(f"• {_when(item.spent_at)} {_money(item.amount, item.currency)} {item.category}{place}")
            return SkillResult(skill_id=self.id, ok=True, message="\n".join(lines))

        payloads = parsed.payload
        if not payloads:
            return SkillResult(skill_id=self.id, ok=False, message="Nothing to add.")
        if not isinstance(payloads, list):
            payloads = [payloads]

        created = []
        async with SessionLocal() as session:
            for payload in payloads:
                payload.source, payload.telegram_user_id = record_origin(
                    telegram_user_id or payload.telegram_user_id
                )
                created.append(await create_expense(session, payload))
            today_summary = await get_summary(session, "today")

        lines = [f"Added <b>{len(created)}</b> spend{'s' if len(created) != 1 else ''}"]
        for expense in created:
            place = f" at {expense.merchant}" if expense.merchant else ""
            lines.append(
                f"• {_when(expense.spent_at)} <b>{_money(expense.amount, expense.currency)}</b> · {expense.category} — {expense.description}{place}"
            )
        lines.append(f"\nToday so far: <b>{_money(today_summary.total, today_summary.currency)}</b>")
        return SkillResult(
            skill_id=self.id,
            ok=True,
            message="\n".join(lines),
            data={"ids": [str(item.id) for item in created], "count": len(created)},
            payload=created,
        )

    def register_bot_handlers(self, application) -> None:
        from app.skills.expense_tracking.bot import register_handlers

        register_handlers(application)


expense_tracking_skill = ExpenseTrackingSkill()
