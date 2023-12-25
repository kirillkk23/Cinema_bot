import asyncio
import logging
import re
import sys
from os import getenv
import aiohttp
from aiogram.types import InlineKeyboardMarkup

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.markdown import hbold

TOKEN = getenv("BOT_TOKEN")
dp = Dispatcher()


async def get_watch_link(film_id):
    url = f'http://api.vokino.tv/v2/online/filmix?id={film_id}&token=linux_820015859ecbfbe0ef29a6acc09aada6_905714'
    async with aiohttp.request('get', url) as resp:
        data = await resp.json()
        return data['channels'][0]['stream_url']




async def create_answer(film: dict) -> str:
    link = await get_watch_link(film["details"]["id"])

    ans = f'{film["details"]["name"]}\n' \
          f'{film["details"]["about"]}\n' \
          f'KP:{film["details"]["rating_kp"]} IMDB:{film["details"]["rating_imdb"]}'\
          f'Смотреть фильм тут: {link}'

    return ans


async def get_film_kinopoisk(film_name: str):
    url = f'https://api.kinopoisk.dev/v1.4/movie/search?page=1&limit=10&query={film_name}'
    headers = {'accept': 'application/json', 'X-API-KEY': 'TJ60QMS-0PF465Y-H6TRPMH-TCKCB9W'}
    async with aiohttp.request('GET', url, headers=headers) as response:
        kp_resp = await response.json()
        film = kp_resp["docs"][0]
        if prepare_film_name(film['name']) == film_name or prepare_film_name(film['alternativeName']) == film_name:
            return film


async def get_film_vokino(film_name: str):
    url = f'http://api.vokino.tv/v2/list?name={film_name}'
    async with (aiohttp.request('GET', url) as response):
        vokino_resp = await response.json()
        film = vokino_resp["channels"][0]
        if prepare_film_name(film["details"]['name']) == film_name or \
            prepare_film_name(film["details"]['originalname']) == film_name:
            return film


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    await message.answer(f'{hbold(message.from_user.full_name)}, Привет! '
                         'Я бот, который выдает ссылки на просмотр фильмов.'
                         'Какой фильм ты хочешь посмотреть?')


def prepare_film_name(name):
    return re.sub(r'[^\w\s]', '', name.lower()).replace('ё', 'е')


@dp.message()
async def get_film(message: types.Message) -> None:
    """
    Handler will forward receive a message back to the sender

    By default, message handler will handle all message types (like a text, photo, sticker etc.)
    """
    # try:
    film = prepare_film_name(message.text)
    if not film:
        await message.answer('Не нашли такой фильм.')
    else:
        film = await get_film_vokino(film)
        if not film:
            await message.answer('Не нашли такой фильм.')
        answer_msg = await create_answer(film)
        await message.answer(answer_msg)


async def main() -> None:
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
