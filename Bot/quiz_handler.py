import asyncio
from aiogram import Router
import urllib.parse
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, FSInputFile, InlineKeyboardMarkup, \
    InlineKeyboardButton
from aiogram.filters import Command
from Bot.questions import questions, animals, animal_info
from Bot.utils import get_animal_image
import os

router = Router()

user_data = {}
question_idx = 0
user_scores = {animal: 0 for animal in animal_info}
# Режим обратной связи для каждого пользователя
user_feedback = {}
waiting_for_feedback = {}
is_feedback_mode = {}  # Новый словарь для отслеживания состояния обратной связи
async def send_animal_image(message: Message, animal_name: str):
    try:
        image_path = get_animal_image(animal_name)

        if not os.path.exists(image_path):
            await message.answer("Изображение не найдено.")
            return

        image = FSInputFile(image_path)
        await message.answer_photo(image)
    except Exception:
        await message.answer("Произошла ошибка при отправке изображения.")


# Функция для отправки вопроса
async def ask_question(message: Message, idx: int):
    global question_idx
    try:
        question = questions[idx]
        buttons = [KeyboardButton(text=answer) for answer in question["answers"]]
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, keyboard=[buttons])

        # Инструкция к вопросу
        await message.answer("Внимательно читайте вопрос и выберите один из вариантов ответа.", reply_markup=None)
        await message.answer(question["question"], reply_markup=markup)
    except KeyError:
        await message.answer("Произошла ошибка с вопросами.")


@router.message(Command("start"))
async def command_start_handler(message: Message):
    try:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        button = KeyboardButton(text="Начать викторину")
        markup.add(button)
        await message.answer("Привет! Хочешь узнать своё тотемное животное? Нажми 'Начать викторину', чтобы начать.",
                             reply_markup=markup)
        await message.answer(
            "Бот задаст вам несколько вопросов, на основе которых будет определено ваше тотемное животное. Подсказки и помощь будут всегда доступны.")
    except Exception as e:
        await message.answer(f"Произошла ошибка при обработке команды /start: {str(e)}")


@router.message(Command("quiz"))
async def start_quiz(message: Message):
    global question_idx, user_data, user_scores
    try:
        user_data = {}
        user_scores = {key: 0 for key in user_scores}
        question_idx = 0

        await message.answer("Начинаем викторину! Ответьте на несколько вопросов, и мы определим ваше тотемное животное.")
        await ask_question(message, question_idx)
    except Exception as e:
        await message.answer(f"Произошла ошибка при запуске викторины: {str(e)}")



@router.message()
async def process_answer(message: Message):
    global question_idx, user_scores
    try:
        user_answer = message.text
        current_question = questions[question_idx]
        if user_answer in current_question["answers"]:
            answer_idx = current_question["answers"].index(user_answer)
            animal = animals[answer_idx]
            user_scores[animal] += 1

        question_idx += 1

        if question_idx < len(questions):
            await ask_question(message, question_idx)
        else:
            most_likely_animal = max(user_scores, key=user_scores.get)
            # описание животного
            animal_description = animal_info[most_likely_animal]["description"]
            await message.answer(f"Ваше тотемное животное — {most_likely_animal} 🦄")
            await message.answer(animal_description)

            # Отправка изображения
            await send_animal_image(message, most_likely_animal)
            await message.answer(f"Поздравляем, у вас {user_scores[most_likely_animal]} баллов!")
            markup = ReplyKeyboardMarkup(resize_keyboard=True,
                                         keyboard=[[KeyboardButton(text="Пройти викторину снова")]])
            await message.answer(
                "Хотите пройти викторину снова? Нажмите 'Пройти викторину снова', чтобы начать заново.",
                reply_markup=markup)

            # Информация о программе опеки
            await asyncio.sleep(1)
            await message.answer(
                "Если вам понравилось узнать о своем тотемном животном, возможно, вам будет интересно "
                "принять участие в программе опеки животных Московского зоопарка. "
                "Эта программа позволяет поддержать уход за животными и защитить их популяции. "
                "Подробнее вы можете узнать на сайте: https://moscowzoo.ru/about/guardianship"
            )

            share_message = f"Моё тотемное животное — {most_likely_animal} 🦄\n"
            share_message += f"Результаты викторины: {user_scores[most_likely_animal]} баллов\n"
            share_message += "Пройдите викторину и узнайте своё тотемное животное! 👇\n"
            share_message += "https://t.me/ZOO_Bot"

            encoded_message = urllib.parse.quote(share_message)
            vk_share_url = f"https://vk.com/share.php?title={encoded_message}"
            tg_share_url = f"https://t.me/share/url?url={encoded_message}"
            wa_share_url = f"https://wa.me/?text={encoded_message}"

            inline_markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Поделиться в VK", url=vk_share_url)],
                [InlineKeyboardButton(text="Поделиться в Telegram", url=tg_share_url)],
                [InlineKeyboardButton(text="Поделиться в WhatsApp", url=wa_share_url)]
            ])
            await message.answer(
                "Поделитесь результатами викторины с друзьями! Это просто: выберите нужный сервис и поделитесь.",
                reply_markup=inline_markup)

            question_idx = 0
            user_scores = {key: 0 for key in user_scores}

    except Exception as e:
        await message.answer(f"Произошла ошибка при обработке ответа: {str(e)}")

# Начать сбор отзыва
@router.message(lambda message: message.text == "Оставить отзыв")
async def handle_feedback_request(message: Message):
    user_id = message.from_user.id
    is_feedback_mode[user_id] = True  # Включаем режим обратной связи
    await message.answer("Пожалуйста, напишите свой отзыв. Мы будем рады услышать ваше мнение!")

# Обработка текста отзыва
@router.message(lambda message: is_feedback_mode.get(message.from_user.id, False))
async def collect_feedback(message: Message):
    user_id = message.from_user.id
    user_feedback[user_id] = message.text
    is_feedback_mode[user_id] = False  # Выключаем режим обратной связи
    await message.answer("Спасибо за ваш отзыв! Мы ценим ваше мнение.")