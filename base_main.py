import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from Bot.token_data import TOKEN
from Bot.quiz_handler import router

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()
dp.include_router(router)

@dp.message(Command("start"))
async def command_start_handler(message: Message):
    await message.answer("Привеееет! А ты знаешь какое твое тотемное животное? Нет? Тогда используй команду /quiz, чтобы начать викторину.")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())