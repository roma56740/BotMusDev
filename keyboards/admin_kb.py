from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="📁 Все записи")],
        [KeyboardButton(text="📨 Рассылка"), KeyboardButton(text="🍓 Монеты")],
        [KeyboardButton(text="📤 Экспорт Excel"), KeyboardButton(text="👥 Пользователи")],
        [KeyboardButton(text="🛍️ Магазин")],
    ],
    resize_keyboard=True
)


from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_statistics_period_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📅 1 день", callback_data="stats_1d"),
            InlineKeyboardButton(text="📆 Неделя", callback_data="stats_7d"),
            InlineKeyboardButton(text="🗓 Месяц", callback_data="stats_30d")
        ]
    ])

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_shop_management_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Создать", callback_data="shop_create"),
            InlineKeyboardButton(text="✏️ Редактировать", callback_data="shop_edit")
        ],
        [
            InlineKeyboardButton(text="🗑 Удалить", callback_data="shop_delete"),
            InlineKeyboardButton(text="📋 Посмотреть", callback_data="shop_view")
        ]
    ])





def get_record_type_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📅 Прошедшие", callback_data="records_past"),
            InlineKeyboardButton(text="📆 Будущие", callback_data="records_future")
        ]
    ])

def get_record_period_keyboard(prefix: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1 день", callback_data=f"{prefix}_1d"),
            InlineKeyboardButton(text="7 дней", callback_data=f"{prefix}_7d"),
            InlineKeyboardButton(text="30 дней", callback_data=f"{prefix}_30d")
        ]
    ])


def get_user_action_keyboard(user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📅 Записи", callback_data=f"user_records:{user_id}"),
            InlineKeyboardButton(text="🛒 Покупки", callback_data=f"user_purchases:{user_id}")
        ]
    ])


def get_purchase_action_keyboard(purchase_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Активировать", callback_data=f"activate_purchase:{purchase_id}")]
    ])

