import os
import requests
from aiogram import Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InputFile
from aiogram.filters import Command
from questions import animal_info, animals, questions

router = Router()

# Путь к папке для сохранения изображений
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
    if not os.path.exists(image_path):  # Проверяем, скачано ли уже изображение
        image_url = animal_info[animal_name]["image_url"]
        download_image(image_url, image_path)
    return image_path

user_data = {}
question_idx = 0
user_scores = {animal: 0 for animal in animal_info}

# Словарь для хранения отзывов пользователей
user_feedback = {}
# Флаг, который отслеживает, оставляет ли пользователь отзыв
waiting_for_feedback = {}

# Функция для отправки вопроса
async def ask_question(message: Message, idx: int):
    global question_idx
    question = questions[idx]
    buttons = [KeyboardButton(text=answer) for answer in question["answers"]]
    markup = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[buttons])
    await message.answer(question["question"], reply_markup=markup)

@router.message(Command("start"))
async def command_start_handler(message: Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[])
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

    if message.text == "Оставить отзыв" or (message.from_user.id in waiting_for_feedback and waiting_for_feedback[message.from_user.id]):
        return
    user_answer = message.text
    current_question = questions[question_idx]

    if user_answer in current_question["answers"]:
        answer_idx = current_question["answers"].index(user_answer)
        animal = animals[answer_idx]
        user_scores[animal] += 1

    # Переход к следующему вопросу
    question_idx += 1

    if question_idx < len(questions):
        await ask_question(message, question_idx)
    else:
        most_likely_animal = max(user_scores, key=user_scores.get)

        #описание животного
        animal_description = animal_info[most_likely_animal]["description"]
        animal_image_path = get_animal_image(most_likely_animal)
        await message.answer(f"Ваше тотемное животное — {most_likely_animal} 🦄")
        await message.answer(animal_description)

        # Проверка, существует ли изображение
        if os.path.exists(animal_image_path):
            print(f"Изображение для {most_likely_animal} существует, отправляем...")

            try:
                with open(animal_image_path, 'rb') as image_file:
                    image = InputFile(image_file, filename=f"{most_likely_animal}.png")
                    await message.answer_photo(image)
            except Exception as e:
                await message.answer("Ошибка при отправке изображения.")
                print(f"Ошибка при отправке изображения: {e}")
        else:
            await message.answer("Изображение не найдено.")
        await message.answer(f"Поздравляем, у вас {user_scores[most_likely_animal]} баллов!")

        #Перезапуск викторины
        markup = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
            [KeyboardButton(text="Пройти викторину снова")],
            [KeyboardButton(text="Оставить отзыв")]
        ])
        await message.answer("Хотите пройти викторину снова?", reply_markup=markup)

        #Информацию о программе опеки
        await message.answer(
            "Если вам понравилось узнать о своем тотемном животном, возможно, вам будет интересно "
            "принять участие в программе опеки животных Московского зоопарка. "
            "Эта программа позволяет поддержать уход за животными и защитить их популяции. "
            "Подробнее вы можете узнать на сайте: https://moscowzoo.ru/about/guardianship"
        )

        question_idx = 0
        user_scores = {key: 0 for key in user_scores}

    # "Оставить отзыв"
    @router.message()
    async def handle_feedback(message: Message):
        user_id = message.from_user.id
        if message.text == "Оставить отзыв":
            waiting_for_feedback[user_id] = True
            await message.answer("Пожалуйста, напишите свой отзыв. Мы будем рады услышать ваше мнение!")

        elif user_id in waiting_for_feedback and waiting_for_feedback[user_id]:
            user_feedback[user_id] = message.text
            waiting_for_feedback[user_id] = False
            await message.answer("Спасибо за ваш отзыв! Мы ценим ваше мнение.")
            markup = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
                [KeyboardButton(text="Пройти викторину снова")]
            ])
            await message.answer("Хотите пройти викторину снова?", reply_markup=markup)