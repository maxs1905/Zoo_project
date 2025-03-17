import os
import requests
from aiogram import Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InputFile
from aiogram.filters import Command
from questions import animal_info, animals, questions  # Убедитесь, что этот файл правильно импортирован

router = Router()

# Путь к папке для сохранения изображений
IMAGE_FOLDER = "images"

# Создайте папку images, если она еще не существует
if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

# Функция для скачивания изображения
def download_image(url, save_path):
    # Отправляем GET-запрос на URL изображения
    response = requests.get(url)
    if response.status_code == 200:
        # Открываем файл для записи в бинарном режиме и записываем данные
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"Изображение сохранено как {save_path}")
    else:
        print(f"Ошибка скачивания изображения: {response.status_code}")

# Скачиваем изображение для каждого животного, если оно еще не сохранено
def get_animal_image(animal_name):
    image_path = os.path.join(IMAGE_FOLDER, f"{animal_name.replace(' ', '_').lower()}.png")
    if not os.path.exists(image_path):  # Проверяем, скачано ли уже изображение
        image_url = animal_info[animal_name]["image_url"]
        download_image(image_url, image_path)
    return image_path

user_data = {}
question_idx = 0
user_scores = {animal: 0 for animal in animal_info}  # Счетчики баллов для каждого животного

# Функция для отправки вопроса
async def ask_question(message: Message, idx: int):
    global question_idx
    question = questions[idx]

    # Создаем список кнопок с текстами ответов
    buttons = [KeyboardButton(text=answer) for answer in question["answers"]]  # Без животных

    # Формируем клавиатуру с кнопками
    markup = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[buttons])

    # Отправляем вопрос с клавиатурой
    await message.answer(question["question"], reply_markup=markup)

# Обработчик команды /start
@router.message(Command("start"))
async def command_start_handler(message: Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[])
    button = KeyboardButton(text="Начать викторину")
    markup.add(button)
    await message.answer("Привет! Хочешь узнать своё тотемное животное? Нажми 'Начать викторину'", reply_markup=markup)

# Обработчик команды /quiz для начала викторины
@router.message(Command("quiz"))
async def start_quiz(message: Message):
    global question_idx, user_data, user_scores
    user_data = {}  # Сброс данных пользователя
    user_scores = {key: 0 for key in user_scores}  # Сброс баллов
    question_idx = 0  # Сброс индекса вопроса
    await ask_question(message, question_idx)

# Обработчик ответа пользователя
@router.message()
async def process_answer(message: Message):
    global question_idx, user_scores

    # Получаем ответ пользователя
    user_answer = message.text
    current_question = questions[question_idx]

    # Находим индекс ответа в списке answers
    if user_answer in current_question["answers"]:
        answer_idx = current_question["answers"].index(user_answer)
        animal = animals[answer_idx]  # Привязываем животное через индекс
        user_scores[animal] += 1

    # Переходим к следующему вопросу
    question_idx += 1

    if question_idx < len(questions):
        await ask_question(message, question_idx)
    else:
        # Определим животное, которое набрало больше всего баллов
        most_likely_animal = max(user_scores, key=user_scores.get)

        # Получаем описание животного
        animal_description = animal_info[most_likely_animal]["description"]
        animal_image_path = get_animal_image(most_likely_animal)  # Получаем путь к изображению

        # Отправляем результат и информацию о животном
        await message.answer(f"Ваше тотемное животное — {most_likely_animal} 🦄")
        await message.answer(animal_description)

        # Проверяем, существует ли изображение
        if os.path.exists(animal_image_path):
            print(f"Изображение для {most_likely_animal} существует, отправляем...")

            try:
                # Теперь отправляем изображение через путь к файлу (передаем его как строку)
                image = InputFile(animal_image_path)
                await message.answer_photo(image)  # Отправляем изображение
            except Exception as e:
                await message.answer("Ошибка при отправке изображения.")
                print(f"Ошибка при отправке изображения: {e}")
        else:
            await message.answer("Изображение не найдено.")

            # Выводим количество баллов
        await message.answer(f"Поздравляем, у вас {user_scores[most_likely_animal]} баллов!")

        # Кнопка для перезапуска викторины
        markup = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[
            KeyboardButton(text="Пройти викторину снова")
        ]])
        await message.answer("Хотите попробовать снова?", reply_markup=markup)

        # Сбросим индексы, чтобы при следующем запуске викторины все снова начиналось с первого вопроса
        question_idx = 0
        user_scores = {key: 0 for key in user_scores}  # Сброс баллов