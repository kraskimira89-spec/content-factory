"""
TG-хэндлер карусели: пошаговый сценарий как в КОНТЕНТ МАШИНА.
Шаг 1 — Режим генерации → Шаг 2 — Фото → Шаг 3 — Настройки → Шаг 4 — Сценарий → Готово.
Фото сохраняются в temp/{session_id}/. Одно статус-сообщение обновляется оркестратором.
"""
import asyncio
import shutil
import tempfile
import uuid
import sys
from pathlib import Path

from aiogram import Bot, Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

KARUSEL_ROOT = Path(__file__).resolve().parent.parent
if str(KARUSEL_ROOT) not in sys.path:
    sys.path.insert(0, str(KARUSEL_ROOT))

from agents.orchestrator import run_pipeline, run
from agents.ai_dialog import expand_brief, get_sample_brief, BRIEF_MIN_LENGTH

router = Router()
TEMP_BASE = KARUSEL_ROOT / "temp"

# --- Reply: под полем ввода всегда «Главная» ---
def reply_kb_main() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Главная")]],
        resize_keyboard=True,
        one_time_keyboard=False,
    )

# --- Inline: главное меню ---
def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Карусель", callback_data="car:enter")],
    ])

# --- Шаг 1: Режим генерации ---
def step1_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="С персонажем", callback_data="car:mode_with"),
            InlineKeyboardButton(text="Без персонажа", callback_data="car:mode_without"),
        ],
        [InlineKeyboardButton(text="Назад", callback_data="car:back_0")],
    ])

# --- Шаг 2: Фото (после получения — действия). В режиме «без персонажа» можно сразу в настройки. ---
def step2_keyboard(has_photo: bool, mode: str = "with") -> InlineKeyboardMarkup:
    rows = []
    if has_photo:
        rows.append([InlineKeyboardButton(text="Перейти к настройкам", callback_data="car:to_settings")])
        rows.append([InlineKeyboardButton(text="Изменить фото", callback_data="car:change_photo")])
    elif mode == "without":
        rows.append([InlineKeyboardButton(text="Перейти к настройкам", callback_data="car:to_settings")])
    rows.append([InlineKeyboardButton(text="Назад", callback_data="car:back_1")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

# --- Шаг 3: Настройки карусели ---
def step3_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Перейти к сценарию", callback_data="car:to_scenario")],
        [InlineKeyboardButton(text="Назад", callback_data="car:back_2")],
    ])

# --- Шаг 4: Сценарий ---
def step4_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ввести текст", callback_data="car:scenario_text")],
        [InlineKeyboardButton(text="✨ Подсказка от ИИ", callback_data="car:ai_hint")],
        [InlineKeyboardButton(text="Назад", callback_data="car:back_3")],
    ])

# --- Готово ---
def step_done_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Новая карусель", callback_data="car:enter")],
        [InlineKeyboardButton(text="Назад", callback_data="car:back_0")],
    ])

# --- Общая кнопка «Назад» для любого шага (car:back_1 = назад на шаг 1, т.е. в меню; car:back_2 = на шаг 2 и т.д.) ---
def nav_back_keyboard(back_to: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data=f"car:back_{back_to}")],
    ])


class CarouselStates(StatesGroup):
    step1_mode = State()      # Режим: с персонажем / без
    step2_photo = State()     # Фото (сохраняются в temp/session_id/)
    step3_settings = State()  # Настройки
    step4_scenario = State()  # Сценарий (текст ТЗ)
    processing = State()     # Идёт генерация — блокируем повторный ввод


async def _show_main_menu(message_or_callback, state: FSMContext, is_callback: bool = False):
    await state.clear()
    text = (
        "Привет. Я бот для генерации каруселей 1080×1350 по вашим фото и ТЗ.\n\n"
        "Выбери раздел и давай начнём."
    )
    if is_callback:
        await message_or_callback.message.answer(text, reply_markup=main_menu_keyboard())
        await message_or_callback.answer()
    else:
        await message_or_callback.answer(text, reply_markup=main_menu_keyboard())


# ---------- Callback из меню после карусели ----------
@router.callback_query(F.data == "main:menu")
async def car_main_menu(callback: CallbackQuery, state: FSMContext):
    await _show_main_menu(callback, state, is_callback=True)


@router.callback_query(F.data == "car:autopost")
async def car_autopost(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "📤 <b>Опубликовать</b>\n\n"
        "В какой канал публикуем? Введи @username канала или перешли сообщение из него.",
    )


@router.callback_query(F.data == "car:edit")
async def car_edit(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "✏️ <b>Изменить слайд</b>\n\n"
        "Введи номер слайда (1–8) и новый текст через двоеточие.\n"
        "Пример: <code>3: Новый заголовок | буллет1 | буллет2</code>",
    )


# ---------- /start и Главная ----------
@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Привет. Я бот для генерации каруселей 1080×1350 по вашим фото и ТЗ.\n\n"
        "Выбери раздел и давай начнём.",
        reply_markup=main_menu_keyboard(),
    )
    await message.answer("👇 Кнопка «Главная» всегда внизу.", reply_markup=reply_kb_main())


@router.message(F.text == "Главная")
async def cmd_main(message: Message, state: FSMContext):
    await _show_main_menu(message, state, is_callback=False)


# ---------- Вход в карусель → Шаг 1 ----------
@router.message(F.text == "/carousel")
async def cmd_carousel(message: Message, state: FSMContext):
    await state.set_state(CarouselStates.step1_mode)
    await state.set_data({})
    await message.answer(
        "Шаг 1. Режим генерации\n\n"
        "Выбери режим:\n"
        "• С персонажем — нужно фото человека для слайдов\n"
        "• Без персонажа — фото не нужны, фон по сценарию",
        reply_markup=step1_keyboard(),
    )


@router.callback_query(F.data == "car:enter")
async def carousel_enter(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CarouselStates.step1_mode)
    await state.set_data({})
    await callback.message.answer(
        "Шаг 1. Режим генерации\n\n"
        "Выбери режим:\n"
        "• С персонажем — нужно фото человека для слайдов\n"
        "• Без персонажа — фото не нужны, фон по сценарию",
        reply_markup=step1_keyboard(),
    )
    await callback.answer()


# ---------- Назад: car:back_0 = в меню, back_1 = на шаг 1, back_2 = на шаг 2, back_3 = на шаг 3 ----------
@router.callback_query(F.data == "car:back_0")
async def car_back_to_main(callback: CallbackQuery, state: FSMContext):
    await _show_main_menu(callback, state, is_callback=True)


@router.callback_query(F.data == "car:back_1")
async def car_back_to_step1(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CarouselStates.step1_mode)
    await callback.message.answer(
        "Шаг 1. Режим генерации\n\n"
        "Выбери режим:\n"
        "• С персонажем — нужно фото человека для слайдов\n"
        "• Без персонажа — фото не нужны, фон по сценарию",
        reply_markup=step1_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "car:back_2")
async def car_back_to_step2(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    photo_paths = data.get("photo_paths", [])
    mode = data.get("mode", "with")
    await state.set_state(CarouselStates.step2_photo)
    text = (
        "Шаг 2. Фото\n\n"
        "Отправь до 10 фотографий (альбомом или по одному). "
        "Фото с персонажем будут использованы для слайдов."
    )
    if mode == "without":
        text = (
            "Шаг 2. Фото\n\n"
            "Режим без персонажа: фото не обязательны. "
            "Можешь отправить одно фоновое фото или нажать «Перейти к настройкам»."
        )
    await callback.message.answer(text, reply_markup=step2_keyboard(len(photo_paths) > 0, mode))
    await callback.answer()


@router.callback_query(F.data == "car:back_3")
async def car_back_to_step3(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CarouselStates.step3_settings)
    await callback.message.answer(
        "Шаг 3. Настройки карусели\n\n"
        "Язык: Русский\nКоличество слайдов: до 8\nФормат: 1080×1350\n\n"
        "Когда готов — нажми «Перейти к сценарию».",
        reply_markup=step3_keyboard(),
    )
    await callback.answer()


# ---------- Шаг 1: выбор режима ----------
@router.callback_query(F.data == "car:mode_with", CarouselStates.step1_mode)
@router.callback_query(F.data == "car:mode_without", CarouselStates.step1_mode)
async def car_step1_mode(callback: CallbackQuery, state: FSMContext):
    mode = "with" if callback.data == "car:mode_with" else "without"
    session_id = str(uuid.uuid4())
    await state.set_state(CarouselStates.step2_photo)
    await state.set_data({"mode": mode, "session_id": session_id, "photo_paths": []})
    if mode == "with":
        text = (
            "Шаг 2. Фото\n\n"
            "Отправь до 10 фотографий (альбомом или по одному). "
            "Лицо и фигура должны быть хорошо видны — они пойдут на слайды."
        )
    else:
        text = (
            "Шаг 2. Фото\n\n"
            "Режим без персонажа: фото не обязательны. "
            "Можешь отправить одно фоновое фото или нажать «Перейти к настройкам»."
        )
    await callback.message.answer(text, reply_markup=step2_keyboard(False, mode))
    await callback.answer()


# ---------- Шаг 2: фото (сохраняем в temp/session_id/) ----------
@router.callback_query(F.data == "car:change_photo", CarouselStates.step2_photo)
async def car_change_photo(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    session_id = data.get("session_id") or str(uuid.uuid4())
    temp_dir = TEMP_BASE / session_id
    if temp_dir.is_dir():
        shutil.rmtree(temp_dir, ignore_errors=True)
    await state.update_data(photo_paths=[], session_id=session_id)
    await callback.message.answer(
        "Отправь фото заново (до 10 шт).",
        reply_markup=step2_keyboard(False, data.get("mode", "with")),
    )
    await callback.answer()


@router.callback_query(F.data == "car:to_settings", CarouselStates.step2_photo)
async def car_to_settings(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CarouselStates.step3_settings)
    await callback.message.answer(
        "Шаг 3. Настройки карусели\n\n"
        "Язык: Русский\nКоличество слайдов: до 8\nФормат: 1080×1350\n\n"
        "Когда готов — нажми «Перейти к сценарию».",
        reply_markup=step3_keyboard(),
    )
    await callback.answer()


@router.message(CarouselStates.step2_photo, F.photo)
async def car_step2_photo(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    photo_paths = list(data.get("photo_paths", []))
    if len(photo_paths) >= 10:
        await message.answer("Максимум 10 фото. Нажми «Перейти к настройкам» или «Изменить фото».", reply_markup=step2_keyboard(True, data.get("mode", "with")))
        return
    session_id = data.get("session_id") or str(uuid.uuid4())
    temp_dir = TEMP_BASE / session_id
    temp_dir.mkdir(parents=True, exist_ok=True)
    file = await bot.get_file(message.photo[-1].file_id)
    path = temp_dir / f"photo_{len(photo_paths)}.jpg"
    await bot.download_file(file.file_path, path)
    photo_paths.append(str(path))
    await state.update_data(photo_paths=photo_paths, session_id=session_id)
    await message.answer(
        f"Фото получено ({len(photo_paths)}). Если всё верно — нажми «Перейти к настройкам». Иначе — «Изменить фото».",
        reply_markup=step2_keyboard(True, data.get("mode", "with")),
    )


# ---------- Шаг 3 → Шаг 4 ----------
@router.callback_query(F.data == "car:to_scenario", CarouselStates.step3_settings)
async def car_to_scenario(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CarouselStates.step4_scenario)
    await callback.message.answer(
        "Шаг 4. Сценарий\n\n"
        "Опиши услугу и ТЗ: название, город, телефон, ключевые пункты для слайдов. "
        "Можешь нажать «Ввести текст» и отправить сообщение с текстом.",
        reply_markup=step4_keyboard(),
    )
    await callback.answer()


# ---------- Шаг 4: Подсказка от ИИ ----------
@router.callback_query(F.data == "car:ai_hint", CarouselStates.step4_scenario)
async def car_ai_hint(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    status = await callback.message.answer("⏳ Генерирую пример сценария…")
    try:
        sample = await asyncio.to_thread(
            get_sample_brief, "оздоровительная услуга для центра"
        )
        await callback.message.bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=status.message_id,
            text=(
                "✨ <b>Пример сценария от ИИ</b>\n\n"
                "Скопируй текст ниже, при необходимости отредактируй и отправь сюда одним сообщением:\n\n"
                f"<blockquote>{sample}</blockquote>"
            ),
            parse_mode="HTML",
        )
    except Exception as e:
        await callback.message.bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=status.message_id,
            text=f"❌ Не удалось обратиться к ИИ: {e}. Проверь config/.env (API ключи).",
        )


# ---------- Шаг 4: ввод текста сценария ----------
@router.callback_query(F.data == "car:scenario_text", CarouselStates.step4_scenario)
async def car_scenario_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Напиши сценарий в следующем сообщении: услуга, город, телефон, буллеты для слайдов.",
        reply_markup=nav_back_keyboard(3),
    )
    await callback.answer()


@router.message(CarouselStates.step4_scenario, F.text)
async def car_step4_text(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    photo_paths = data.get("photo_paths", [])
    session_id = data.get("session_id") or str(uuid.uuid4())
    brief_text = (message.text or "").strip()
    if not brief_text:
        await message.answer(
            "Отправь текст ТЗ: услуга, город, телефон, буллеты.",
            reply_markup=step4_keyboard(),
        )
        return
    mode = data.get("mode", "with")
    if mode == "with" and not photo_paths:
        await message.answer(
            "Сначала пришли фото на шаге 2, затем вернись сюда и введи текст.",
            reply_markup=step4_keyboard(),
        )
        return
    # Режим «без персонажа» без фото: создаём заглушку в temp/session_id
    if not photo_paths:
        from PIL import Image
        temp_dir = TEMP_BASE / session_id
        temp_dir.mkdir(parents=True, exist_ok=True)
        placeholder = temp_dir / "photo_0.jpg"
        Image.new("RGB", (100, 100), color=(255, 255, 255)).save(placeholder)
        photo_paths = [str(placeholder)]

    await state.set_state(CarouselStates.processing)
    status_msg = await message.answer(
        "⏳ ИИ дополняет описание…" if len(brief_text) < BRIEF_MIN_LENGTH else "⏳ Запускаю генерацию…"
    )
    # Короткий текст — дополняем через ИИ перед парсером
    if len(brief_text) < BRIEF_MIN_LENGTH:
        try:
            brief_text = await asyncio.to_thread(expand_brief, brief_text)
            await status_msg.edit_text("⏳ Запускаю генерацию…")
        except Exception:
            await status_msg.edit_text("⏳ Запускаю генерацию…")
    try:
        ok = await run(
            photo_paths=photo_paths,
            raw_text=brief_text,
            user_id=message.chat.id,
            session_id=session_id,
            bot=bot,
            status_msg_id=status_msg.message_id,
            run_vision=False,
        )
        if not ok:
            await message.answer("Что-то пошло не так. Попробуй ещё раз или нажми «Главная».", reply_markup=main_menu_keyboard())
    finally:
        await state.clear()
    return


# ---------- Защита: во время генерации не принимаем новый ввод ----------
@router.message(CarouselStates.processing)
async def car_processing_guard(message: Message):
    await message.answer("⏳ Карусель ещё генерируется, подожди…")


# Режим «с персонажем»: текст пришёл, фото уже в state — запускаем пайплайн
# (обработка с фото уже в _download_photos_and_run выше; для with+photo мы попадаем в ветку с file_ids)
# Нужно убедиться, что при with+photo мы не заходим в branch "if not file_ids". Мы уже проверили: if not file_ids and mode == "with" -> return. И если file_ids есть, идём в _download_photos_and_run. Но _download_photos_and_run принимает file_ids — это list of file_id (telegram), а не paths. So we need to download them. So the existing _download_photos_and_run is correct. We call it at the end when file_ids is not empty. Good.

