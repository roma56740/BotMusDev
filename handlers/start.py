from aiogram import Router
from aiogram.types import Message, FSInputFile
from aiogram.utils.markdown import hbold, hitalic
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import os

from keyboards.user_kb import get_user_keyboard
from keyboards.admin_kb import admin_keyboard
from db import user_exists, add_user, is_user_registered, get_username_by_id, add_referral_bonus
from aiogram.types import CallbackQuery
from dotenv import load_dotenv
from db import set_invited_by

router = Router()

load_dotenv()
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))


@router.message(lambda msg: msg.text.startswith("/start"))
async def start_handler(message: Message):
    print(f"[DEBUG] message.text = {message.text}")

    telegram_id = message.from_user.id
    full_name = message.from_user.full_name
    username = message.from_user.username or ""

    inviter_id = None

    # Поддержка формата "/start 123456789" и "/start_123456789"
    if " " in message.text:
        try:
            inviter_id = int(message.text.split(" ", 1)[1])
        except ValueError:
            inviter_id = None
    elif "_" in message.text:
        try:
            inviter_id = int(message.text.split("_", 1)[1])
        except ValueError:
            inviter_id = None

    print(f"[START] Пользователь {telegram_id} запустил бота. Пригласил: {inviter_id}")

    # Приветствие для админа
    if telegram_id == ADMIN_ID:
        await message.answer(
            "👋 <b>Добро пожаловать в админ-панель.</b>",
            reply_markup=admin_keyboard,
            parse_mode="HTML"
        )
        return

    # Проверка: новый ли пользователь
    is_new = not user_exists(telegram_id)
    print(f"[START] Новый пользователь? {'Да' if is_new else 'Нет'}")

    if is_new:
        add_user(telegram_id, full_name, username, inviter_id)
        print(f"[START] Пользователь {telegram_id} добавлен. Пригласивший: {inviter_id}")

        if inviter_id:
            inviter_username = get_username_by_id(inviter_id)
            if inviter_username:
                await message.answer(f"🎉 Вы пришли по приглашению от @{inviter_username}!")
            else:
                await message.answer("🎉 Вы пришли по приглашению!")
    else:
        if inviter_id:
            was_set = set_invited_by(telegram_id, inviter_id)
            print(f"[START] Попытка установить пригласившего: {inviter_id} → {'успешно' if was_set else 'уже был установлен'}")
            if was_set:
                inviter_username = get_username_by_id(inviter_id)
                if inviter_username:
                    await message.answer(f"🎉 Вы пришли по приглашению от @{inviter_username}!")
                else:
                    await message.answer("🎉 Вы пришли по приглашению!")

    registered = is_user_registered(telegram_id)

    # Кнопка "Как работает бот"
    how_it_works_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎧 Как работает бот?", callback_data="how_it_works")]
    ])

    # Приветственное сообщение
    photo = FSInputFile("media/welcome.jpg")
    text = (
        f"{hbold('Добро пожаловать в музыкальную студию!')} 🎶\n\n"
        f"{hitalic('С нами ты сможешь легко записаться на сессии, отслеживать посещения, получать бонусы и многое другое.')}\n\n"
        f"Нажми кнопку ниже, чтобы узнать подробнее 👇"
    )

    await message.answer_photo(
        photo=photo,
        caption=text,
        reply_markup=how_it_works_kb,
        parse_mode="HTML"
    )

    await message.answer("📋 Главное меню:", reply_markup=get_user_keyboard(registered))




@router.callback_query(lambda c: c.data == "how_it_works")
async def how_it_works_handler(callback: CallbackQuery):
    await callback.answer("Скоро здесь появится информация! 🎧", show_alert=True)




from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from keyboards.admin_kb import get_user_action_keyboard, get_purchase_action_keyboard
from db import (
    get_user_by_username,
    get_user_bookings,
    get_user_purchases,
    mark_purchase_as_used
)

searched_users = {}


@router.message(F.text == "👥 Пользователи")
async def ask_for_username(msg: Message, state: FSMContext):
    await msg.answer("Введите @username пользователя для поиска.")


@router.message(F.text.startswith("@"))
async def handle_username_search(msg: Message):
    username = msg.text.strip("@")
    user = get_user_by_username(username)

    if not user:
        await msg.answer("❌ Пользователь не найден.")
        return

    searched_users[msg.from_user.id] = user["telegram_id"]

    text = (
        f"👤 <b>{user['full_name']}</b>\n"
        f"🆔 <code>{user['telegram_id']}</code>\n"
        f"📛 Username: @{user['username']}\n"
        f"📞 Телефон: {user.get('phone', '—')}\n"
        f"🎂 Дата рождения: {user.get('birthdate', '—')}\n"
        f"🔢 Возраст: {user.get('age', '—')}\n"
        f"🍓 Монет: {user.get('coins', 0)}\n"
    )

    await msg.answer(text, reply_markup=get_user_action_keyboard(user["telegram_id"]), parse_mode="HTML")


@router.callback_query(F.data.startswith("user_records:"))
async def show_user_bookings(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    bookings = get_user_bookings(user_id)

    if not bookings:
        await callback.message.answer("📅 У пользователя нет записей.")
        return

    text = "📅 <b>Активные записи:</b>\n\n"
    for b in bookings:
        text += (
            f"🗓 {b['date']} | {b['time_from']}–{b['time_to']}\n"
            f"📌 Тариф: {b['tariff']}\n"
            f"✅ Подтверждена: {'Да' if b['confirmed'] else 'Нет'}\n\n"
        )

    await callback.message.answer(text, parse_mode="HTML")


@router.callback_query(F.data.startswith("user_purchases:"))
async def show_user_purchases(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    purchases = get_user_purchases(user_id)

    if not purchases:
        await callback.message.answer("🛒 У пользователя нет покупок.")
        return

    for p in purchases:
        status = "✅ Использовано" if p['status'] == 'used' else "🟡 Активно"
        text = (
            f"🛍 <b>{p['name']}</b>\n"
            f"💬 {p['description']}\n"
            f"🆔 Код: <code>{p['code']}</code>\n"
            f"📅 Дата: {p['timestamp']}\n"
            f"📌 Статус: {status}"
        )

        markup = None
        if p['status'] != 'used':
            markup = get_purchase_action_keyboard(p['id'])

        await callback.message.answer(text, reply_markup=markup, parse_mode="HTML")


@router.callback_query(F.data.startswith("activate_purchase:"))
async def activate_purchase(callback: CallbackQuery):
    purchase_id = int(callback.data.split(":")[1])
    mark_purchase_as_used(purchase_id)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("✅ Покупка активирована")



import pandas as pd
from io import BytesIO
import sqlite3




def get_export_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👤 Пользователи", callback_data="export_users"),
            InlineKeyboardButton(text="📅 Записи", callback_data="export_bookings")
        ],
        [
            InlineKeyboardButton(text="🛒 Покупки", callback_data="export_purchases"),
            InlineKeyboardButton(text="🍓 История монет", callback_data="export_coin_history")
        ]
    ])

@router.message(F.text == "📤 Экспорт Excel")
async def export_menu(msg: Message):
    await msg.answer("Что вы хотите экспортировать?", reply_markup=get_export_keyboard())


@router.callback_query(F.data.startswith("export_"))
async def export_table(callback: CallbackQuery):
    table = callback.data.replace("export_", "")
    db_path = "users.db"

    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
        conn.close()

        if df.empty:
            await callback.message.answer("❌ Таблица пуста.")
            return

        buffer = BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)

        from aiogram.types import BufferedInputFile

        file = BufferedInputFile(buffer.read(), filename=f"{table}.xlsx")
        await callback.message.answer_document(
            document=file,
            caption=f"📄 Таблица: {table}"
        )
        await callback.answer()

    except Exception as e:
        await callback.message.answer(f"⚠️ Ошибка экспорта: {e}")





















from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton 

def get_reply_to_user_keyboard(user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✉ Ответить", callback_data=f"reply_to_user:{user_id}")]
    ])

# 


class ChatWithAdmin(StatesGroup):
    waiting_user_message = State()
    waiting_admin_reply = State()


# --- Пользователь нажал "Чат с админом"
@router.message(F.text == "💬 Чат с админом")
async def start_chat_with_admin(msg: Message, state: FSMContext):
    await msg.answer("✍ Напишите сообщение, которое будет отправлено администратору:")
    await state.set_state(ChatWithAdmin.waiting_user_message)


@router.message(ChatWithAdmin.waiting_user_message)
async def handle_user_message(msg: Message, state: FSMContext):
    await state.clear()

    text = (
        f"📩 Новое сообщение от пользователя:\n\n"
        f"<b>{msg.from_user.full_name}</b> (@{msg.from_user.username})\n"
        f"<code>{msg.from_user.id}</code>\n\n"
        f"{msg.text}"
    )

    await msg.answer("✅ Сообщение отправлено администратору.")
    await msg.bot.send_message(
        chat_id=ADMIN_ID,
        text=text,
        reply_markup=get_reply_to_user_keyboard(msg.from_user.id),
        parse_mode="HTML"
    )


# --- Админ нажал "Ответить"
@router.callback_query(F.data.startswith("reply_to_user:"))
async def ask_admin_for_reply(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split(":")[1])
    await state.update_data(reply_to=user_id)
    await callback.message.answer("✍ Введите сообщение, которое хотите отправить пользователю:")
    await state.set_state(ChatWithAdmin.waiting_admin_reply)
    await callback.answer()


# --- Админ ввёл текст — подтверждение
@router.message(ChatWithAdmin.waiting_admin_reply)
async def handle_admin_reply(msg: Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("reply_to")

    if not user_id:
        await msg.answer("⚠️ Ошибка: не выбран пользователь.")
        await state.clear()
        return

    await state.update_data(reply_text=msg.text)

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📨 Подтвердить отправку", callback_data="confirm_admin_reply")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_admin_reply")]
    ])

    await msg.answer(
        f"🔔 Вы уверены, что хотите отправить пользователю сообщение:\n\n{msg.text}",
        reply_markup=markup
    )


# --- Подтверждение отправки
@router.callback_query(F.data == "confirm_admin_reply")
async def confirm_admin_reply(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("reply_to")
    reply_text = data.get("reply_text")

    if not user_id or not reply_text:
        await callback.message.answer("⚠️ Ошибка при подтверждении.")
        await state.clear()
        return

    try:
        await callback.bot.send_message(
            chat_id=user_id,
            text=f"📬 Сообщение от администратора:\n\n{reply_text}"
        )
        await callback.message.edit_text("✅ Сообщение успешно отправлено пользователю.")
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка при отправке: {e}")

    await state.clear()
    await callback.answer()


# --- Отмена отправки
@router.callback_query(F.data == "cancel_admin_reply")
async def cancel_admin_reply(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Отправка сообщения отменена.")
    await callback.answer()