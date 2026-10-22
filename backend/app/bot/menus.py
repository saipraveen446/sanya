from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

HOME_LABELS = {
    "💰 Expenses": "expenses",
    "⏰ Reminders": "reminders",
    "✅ Todo": "todo",
    "📰 News": "news",
    "📰 Tech & AI News": "news",
}

AWAITING_PROMPTS = {
    "expense_add": "Send the expense, e.g. <b>tiffin 80</b> or <b>petrol 500 at Indian Oil</b>.",
    "reminder_add": "Send the reminder, e.g. <b>call dentist tomorrow 10am</b>.",
    "todo_add": "Send the todo, e.g. <b>submit invoice tomorrow</b>.",
}


def home_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("💰 Expenses"), KeyboardButton("⏰ Reminders")],
            [KeyboardButton("✅ Todo"), KeyboardButton("📰 News")],
        ],
        resize_keyboard=True,
    )


def full_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("➕ Add Expense", callback_data="menu:expense:add"),
                InlineKeyboardButton("📊 Expense Summary", callback_data="menu:expense:summary"),
            ],
            [InlineKeyboardButton("📜 Expense History", callback_data="menu:expense:history")],
            [
                InlineKeyboardButton("➕ Add Reminder", callback_data="menu:reminder:add"),
                InlineKeyboardButton("📋 My Reminders", callback_data="menu:reminder:list"),
            ],
            [InlineKeyboardButton("🗑 Delete Reminder", callback_data="menu:reminder:delete")],
            [
                InlineKeyboardButton("➕ Add Todo", callback_data="menu:todo:add"),
                InlineKeyboardButton("📋 Todo List", callback_data="menu:todo:list"),
            ],
            [
                InlineKeyboardButton("☑️ Completed", callback_data="menu:todo:done"),
                InlineKeyboardButton("🗑 Delete Todo", callback_data="menu:todo:delete"),
            ],
            [
                InlineKeyboardButton("🤖 AI News", callback_data="menu:news:ai"),
                InlineKeyboardButton("💻 Tech News", callback_data="menu:news:tech"),
                InlineKeyboardButton("🔥 Top News", callback_data="menu:news:top"),
            ],
        ]
    )


def skill_keyboard(skill_id: str) -> InlineKeyboardMarkup:
    if skill_id in {"expense_tracking", "expenses", "expense"}:
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("➕ Add Expense", callback_data="menu:expense:add"),
                    InlineKeyboardButton("📊 Expense Summary", callback_data="menu:expense:summary"),
                ],
                [InlineKeyboardButton("📜 Expense History", callback_data="menu:expense:history")],
            ]
        )
    if skill_id == "reminders":
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("➕ Add Reminder", callback_data="menu:reminder:add"),
                    InlineKeyboardButton("📋 My Reminders", callback_data="menu:reminder:list"),
                ],
                [InlineKeyboardButton("🗑 Delete Reminder", callback_data="menu:reminder:delete")],
            ]
        )
    if skill_id == "todo":
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("➕ Add Todo", callback_data="menu:todo:add"),
                    InlineKeyboardButton("📋 Todo List", callback_data="menu:todo:list"),
                ],
                [
                    InlineKeyboardButton("☑️ Completed", callback_data="menu:todo:done"),
                    InlineKeyboardButton("🗑 Delete Todo", callback_data="menu:todo:delete"),
                ],
            ]
        )
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🤖 AI News", callback_data="menu:news:ai"),
                InlineKeyboardButton("💻 Tech News", callback_data="menu:news:tech"),
            ],
            [InlineKeyboardButton("🔥 Top News", callback_data="menu:news:top")],
        ]
    )


def menu_text() -> str:
    return "\n".join(
        [
            "Hi, I'm <b>Sanya</b>. Same actions work here and on the web dashboard.",
            "",
            "<b>💰 Expenses</b> — add, summary, history",
            "<b>⏰ Reminders</b> — add, list, delete, and I alert you when due",
            "<b>✅ Todo</b> — add, list, completed, delete",
            "<b>📰 Tech & AI News</b> — AI, tech, top headlines",
            "",
            "Tap a button, or just type like <code>tiffin 80</code>.",
        ]
    )
