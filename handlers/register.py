# handlers/register.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from keyboards.register_kb import confirm_kb
from db import add_user_after_register
from datetime import datetime

router = Router()

class RegisterState(StatesGroup):
    full_name = State()
    birthday = State()
    phone = State()
    confirm = State()

@router.message(F.text == "📝 Регистрация")
async def start_register(message: Message, state: FSMContext):
    await state.set_state(RegisterState.full_name)
    await message.answer("Введите вашу <b>Фамилию и Имя</b>:", parse_mode="HTML")  # ✅ исправлено


@router.message(RegisterState.full_name)
async def get_full_name(message: Message, state: FSMContext):
    text = message.text.strip()
    parts = text.split()

    if len(parts) < 2 or not all(p.isalpha() for p in parts):
        await message.answer("❌ Введите <b>Фамилию и Имя</b>, разделяя пробелом.")
        return

    formatted_name = ' '.join(part.capitalize() for part in parts)
    await state.update_data(full_name=formatted_name)
    await state.set_state(RegisterState.birthday)
    await message.answer("Введите <b>дату рождения</b> в формате ДД.ММ.ГГГГ:", parse_mode="HTML")


@router.message(RegisterState.birthday)
async def get_birthday(message: Message, state: FSMContext):
    try:
        b_date = datetime.strptime(message.text.strip(), "%d.%m.%Y")
        today = datetime.today()
        age = today.year - b_date.year - ((today.month, today.day) < (b_date.month, b_date.day))
        await state.update_data(birth_date=b_date.strftime("%Y-%m-%d"), age=age)
        await state.set_state(RegisterState.phone)
        await message.answer("Введите <b>номер телефона</b>:", parse_mode="HTML")
    except ValueError:
        await message.answer("❌ Неверный формат даты. Введите в формате ДД.ММ.ГГГГ")

import re  # вверху файла

@router.message(RegisterState.phone)
async def get_phone(message: Message, state: FSMContext):
    phone = message.text.strip()

    if not re.fullmatch(r"\+7\d{10}", phone):
        await message.answer("❌ Введите корректный номер телефона в формате <b>+7XXXXXXXXXX</b>")
        return

    await state.update_data(phone=phone)
    data = await state.get_data()

    confirm_text = (
        f"<b>Проверьте введённые данные:</b>\n\n"
        f"👤 ФИО: {data['full_name']}\n"
        f"🎂 Дата рождения: {data['birth_date']}\n"
        f"📞 Телефон: {data['phone']}\n"
    )
    await message.answer(confirm_text, reply_markup=confirm_kb, parse_mode="HTML")
    await state.set_state(RegisterState.confirm)

from keyboards.user_kb import get_user_keyboard  # Не забудь импорт

@router.callback_query(F.data == "confirm_register")
async def confirm_register(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    telegram_id = callback.from_user.id

    underage = int(data['age'] < 14)

    # Добавляем пользователя в БД
    add_user_after_register(
        telegram_id=telegram_id,
        full_name=data['full_name'],
        birth_date=data['birth_date'],
        phone=data['phone'],
        age=data['age'],
        underage=underage
    )

    # Удаляем сообщение с кнопками
    await callback.message.delete()

    # Отправляем сообщение с новой клавиатурой
    await callback.message.answer(
        "✅ Вы успешно зарегистрированы!",
        reply_markup=get_user_keyboard(registered=True)
    )

    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "cancel_register")
async def cancel_register(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("❌ Регистрация отменена.")
    await state.clear()
    await callback.answer()


    