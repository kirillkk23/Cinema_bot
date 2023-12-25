import asyncio
import logging
import sys
from os import getenv
import aiohttp


from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.markdown import hbold

# Bot token can be obtained via https://t.me/BotFather
TOKEN = getenv("bot_token")
API_TOKEN = getenv("api_token")
# KINOPOISK_COOKIE = os.getenv("Kinopoisk_coockie")
# USER_AGENT = os.getenv("User_agent")
# import requests
# headers = {"X-API-KEY": API_TOKEN}
# resp = requests.get("https://api.kinopoisk.dev/v1.4/movie/34567", headers=headers)
# print(resp.text)
# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher()

def expand_film(raw_data):
    film_name = raw_data['docs'][0]['name']
    film_desc = response.json()['docs'][0]['description']
    film_short_desc = response.json()['docs'][0]['shortDescription']
    rating_kp = response.json()['docs'][0]['rating']['kp']
    rating_imdb = response.json()['docs'][0]['rating']['imdb']
    url_poster = response.json()['docs'][0]['poster']['url']

async def get_film_kinopoisk(film_name: str):
    url = f'https://api.kinopoisk.dev/v1.4/movie/search?page=1&limit=10&query={film_name}'
    headers = {'accept': 'application/json', 'X-API-KEY': 'TJ60QMS-0PF465Y-H6TRPMH-TCKCB9W'}
    async with aiohttp.request('GET', url, headers=headers) as response:
        kp_resp = await response.json()
        raw_film_data = kp_resp["docs"][0]
        return expand_film(raw_film_data)

loop = asyncio.get_event_loop()
response = loop.run_until_complete(make_request())
print(response)



@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    await message.answer(f'{hbold(message.from_user.full_name)}, Привет! '
                         'Я бот, который выдает ссылки на просмотр фильмов.'
                         'Какой фильм ты хочешь посмотреть?')


@dp.message()
async def get_film(message: types.Message) -> None:
    """
    Handler will forward receive a message back to the sender

    By default, message handler will handle all message types (like a text, photo, sticker etc.)
    """
    #try:
    text = message.text
    print(text)
    if not text:
        await message.answer('Иди нахуй, долбоёб!!!')
    else:

    await message.send_copy(chat_id=message.chat.id)
    # except TypeError:
    #     # But not all the types is supported to be copied so need to handle it
    #     await message.answer("Nice try!")


async def main() -> None:
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
