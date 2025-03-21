import os
import requests
from Bot.questions import animal_info

IMAGE_FOLDER = "Bot/images"

# Создать папку images, если не существует
if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)


# Функция для скачивания изображения с обработкой ошибок
def download_image(url, save_path):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Если ответ не успешный, будет вызвана ошибка
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"Изображение сохранено как {save_path}")
    except requests.exceptions.RequestException:
        print(f"Ошибка при скачивании изображения с URL: {url}")


def get_animal_image(animal_name):
    image_path = os.path.join(IMAGE_FOLDER, f"{animal_name.replace(' ', '_').lower()}.png")
    try:
        if not os.path.exists(image_path):
            image_url = animal_info[animal_name]["image_url"]
            download_image(image_url, image_path)
    except KeyError:
        print(f"Ошибка доступа к данным изображения для животного {animal_name}")
    return image_path


