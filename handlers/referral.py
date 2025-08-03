from aiogram import Bot, types, Router
from aiogram.types import Message
from db import is_user_registered, get_referral_count

router = Router()

@router.message(lambda message: message.text == "🤝 Моя реферальная ссылка")
async def referral_link_handler(message: Message, bot: Bot):
    telegram_id = message.from_user.id

    if not is_user_registered(telegram_id):
        await message.answer("Пожалуйста, сначала пройдите регистрацию.")
        return

    # Получаем username бота через get_me
    bot_info = await bot.get_me()
    bot_username = bot_info.username

    invite_link = f"https://t.me/{bot_username}?start={telegram_id}"
    invited_count = get_referral_count(telegram_id)

    await message.answer(
        f"Ваша реферальная ссылка:\n{invite_link}\n\n"
        f"Вы уже пригласили: {invited_count} человек(а)."
    )





from aiogram import F, Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from db import get_db_connection
from aiogram.exceptions import TelegramAPIError
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery


class MailingState(StatesGroup):
    waiting_for_text = State()
    waiting_for_confirmation = State()


@router.message(F.text == "📨 Рассылка")
async def ask_mailing_text(message: Message, state: FSMContext):
    await message.answer("📬 <b>Введите текст рассылки:</b>", parse_mode="HTML")
    await state.set_state(MailingState.waiting_for_text)


@router.message(MailingState.waiting_for_text)
async def ask_for_confirmation(message: Message, state: FSMContext):
    await state.update_data(mailing_text=message.text)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_mailing"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_mailing")
        ]
    ])

    await message.answer(
        f"<b>Вы уверены, что хотите разослать это сообщение?</b>\n\n{message.text}",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await state.set_state(MailingState.waiting_for_confirmation)


@router.callback_query(F.data == "confirm_mailing")
async def confirm_and_send(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    mailing_text = data.get("mailing_text")

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT telegram_id FROM users WHERE is_registered = 1")
    users = c.fetchall()
    conn.close()

    success = 0
    failed = 0

    await callback.message.edit_text("🚀 Начинаю рассылку...")

    for (user_id,) in users:
        try:
            await callback.bot.send_message(chat_id=user_id, text=mailing_text)
            success += 1
        except Exception:
            failed += 1

    await callback.message.answer(
        f"📢 <b>Рассылка завершена!</b>\n\n"
        f"✅ Отправлено: {success}\n"
        f"❌ Ошибок: {failed}",
        parse_mode="HTML"
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "cancel_mailing")
async def cancel_mailing(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("❌ Рассылка отменена.")
    await state.clear()
    await callback.answer()



def get_user_shop_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📜 История монет", callback_data="shop_history")],
        [InlineKeyboardButton(text="🎁 Мои покупки", callback_data="shop_my_purchases")],
        [InlineKeyboardButton(text="🛒 Товары", callback_data="shop_items")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")],
    ])


from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from db import get_user, get_coin_history, get_active_purchases, get_all_shop_items, purchase_item



@router.message(F.text == "🛒 Магазин")
async def user_shop_menu(message: Message):
    if not is_user_registered(message.from_user.id):
        await message.answer("❗ Вы не зарегистрированы. Пожалуйста, пройдите регистрацию, чтобы использовать магазин.")
        return

    text = (
        "🛍️ <b>Добро пожаловать в магазин!</b>\n\n"
        "Выберите нужный раздел:\n"
        "🔸 <b>История монет</b> — просмотр пополнений и списаний\n"
        "🔸 <b>Покупки</b> — ваши активные товары\n"
        "🔸 <b>Товары</b> — доступные товары для покупки\n"
    )
    await message.answer(text, reply_markup=get_user_shop_menu_kb(), parse_mode="HTML")


@router.callback_query(F.data == "shop_history")
async def show_coin_history(callback: CallbackQuery):
    history = get_coin_history(callback.from_user.id)

    if not history:
        await callback.message.edit_text("📜 <b>У вас пока нет истории по монетам.</b>", parse_mode="HTML")
        return

    text = "<b>📜 История по монетам:</b>\n\n"
    for entry in history:
        sign = "➕" if entry["amount"] > 0 else "➖"
        text += (
            f"{sign} <b>{abs(entry['amount'])} STRAWBERRY Coin</b>\n"
            f"📄 {entry['description']}\n"
            f"🕒 {entry['timestamp']}\n\n"
        )
    await callback.message.edit_text(text, parse_mode="HTML")



@router.callback_query(F.data == "shop_my_purchases")
async def show_user_purchases(callback: CallbackQuery):
    purchases = get_active_purchases(callback.from_user.id)

    if not purchases:
        await callback.message.edit_text("🎁 <b>У вас пока нет активных покупок.</b>", parse_mode="HTML")
        return

    text = "<b>🎁 Ваши покупки:</b>\n\n"
    for item in purchases:
        text += (
            f"📦 <b>{item['name']}</b>\n"
            f"🔑 Код: <code>{item['code']}</code>\n"
            f"📄 {item['description']}\n\n"
        )
    await callback.message.edit_text(text, parse_mode="HTML")


@router.callback_query(F.data == "shop_items")
async def show_shop_items(callback: CallbackQuery):
    items = get_all_shop_items()

    if not items:
        await callback.message.edit_text("🛒 <b>В магазине пока нет товаров.</b>", parse_mode="HTML")
        return

    text = "<b>🛍️ Доступные товары:</b>\n\n"
    kb = []
    for item in items:
        text += (
            f"📦 <b>{item['name']}</b>\n"
            f"💰 Цена: <b>{item['price']}</b> STRAWBERRY Coin\n"
            f"📄 {item['description']}\n\n"
        )
        kb.append([InlineKeyboardButton(
            text=f"🛒 Купить: {item['name']}", callback_data=f"buy_{item['id']}"
        )])

    await callback.message.edit_text(text.strip(), reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")


@router.callback_query(F.data.startswith("buy_"))
async def handle_buy(callback: CallbackQuery):
    item_id = int(callback.data.split("_")[1])
    success, msg = purchase_item(callback.from_user.id, item_id)
    await callback.answer(msg, show_alert=True)

    if success:
        await callback.message.answer("✅ Покупка успешна! Ваш код отображён в разделе 'Покупки'.")
