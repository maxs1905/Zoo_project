import os
import requests
import asyncio
import urllib.parse
from aiogram import Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from questions import animal_info, animals, questions

router = Router()

IMAGE_FOLDER = "images"

# Создать папку images
if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

# Функция для скачивания изображения
def download_image(url, save_path):
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"Изображение сохранено как {save_path}")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка скачивания изображения: {e}")

def get_animal_image(animal_name):
    image_path = os.path.join(IMAGE_FOLDER, f"{animal_name.replace(' ', '_').lower()}.png")
    if not os.path.exists(image_path):
        image_url = animal_info[animal_name]["image_url"]
        download_image(image_url, image_path)
    return image_path

user_data = {}
question_idx = 0
user_scores = {animal: 0 for animal in animal_info}

user_feedback = {}
waiting_for_feedback = {}

# Функция для отправки изображения
async def send_animal_image(message: Message, animal_name: str):
    image_path = get_animal_image(animal_name)

    if not os.path.exists(image_path):
        await message.answer("Изображение не найдено.")
        return

    try:
        image = FSInputFile(image_path)
        await message.answer_photo(image)
    except Exception as e:
        print(f"Ошибка при отправке изображения: {e}")
        await message.answer("Произошла ошибка при отправке изображения.")

# Функция для отправки вопроса
async def ask_question(message: Message, idx: int):
    global question_idx
    question = questions[idx]
    buttons = [KeyboardButton(text=answer) for answer in question["answers"]]
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, keyboard=[buttons])  # Исправлено
    await message.answer(question["question"], reply_markup=markup)

@router.message(Command("start"))
async def command_start_handler(message: Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    button = KeyboardButton(text="Начать викторину")
    markup.add(button)
    await message.answer("Привет! Хочешь узнать своё тотемное животное? Нажми 'Начать викторину'", reply_markup=markup)

@router.message(Command("quiz"))
async def start_quiz(message: Message):
    global question_idx, user_data, user_scores
    user_data = {}
    user_scores = {key: 0 for key in user_scores}
    question_idx = 0
    await ask_question(message, question_idx)

@router.message()
async def process_answer(message: Message):
    global question_idx, user_scores

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
        markup = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
            [KeyboardButton(text="Пройти викторину снова")],
        ])
        await message.answer("Хотите пройти викторину снова?", reply_markup=markup)

        # Информация о программе опеки
        await asyncio.sleep(1)  # Пауза в 1 секунду перед отправкой информации об опеке

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
        await message.answer("Поделитесь результатами викторины с друзьями!", reply_markup=inline_markup)

        question_idx = 0
        user_scores = {key: 0 for key in user_scores}

# Начать сбор отзыва
@router.message(lambda message: message.text == "Оставить отзыв")
async def handle_feedback_request(message: Message):
    user_id = message.from_user.id
    waiting_for_feedback[user_id] = True
    await message.answer("Пожалуйста, напишите свой отзыв. Мы будем рады услышать ваше мнение!")

# Обработка текста отзыва
@router.message(lambda message: waiting_for_feedback.get(message.from_user.id, False))
async def collect_feedback(message: Message):
    user_id = message.from_user.id
    user_feedback[user_id] = message.text
    waiting_for_feedback[user_id] = False
    await message.answer("Спасибо за ваш отзыв! Мы ценим ваше мнение.")



