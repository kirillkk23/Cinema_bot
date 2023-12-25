import os
import json

from bs4 import BeautifulSoup
from typing import Any, Optional
from aiohttp import ClientSession
from aiogram import Bot, types
from aiogram.dispatcher.dispatcher import Dispatcher#, FSMContext
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_TOKEN = os.getenv("API_TOKEN")
KINOPOISK_COOKIE = os.getenv("Kinopoisk_coockie")
USER_AGENT = os.getenv("User_agent")

storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=storage)
KEYBOARD: types.ReplyKeyboardMarkup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
KEYBOARD.add("Найти фильм", "Найти сериал")


class Film(StatesGroup):
    name = State()


class Serial(StatesGroup):
    name = State()
    season = State()
    episode = State()


async def get_url_to_watch(url_to_description: str, film_id: str, title_type: str) -> tuple[str, bool]:
    async with ClientSession(cookies=json.loads(KINOPOISK_COOKIE), headers={'User-Agent': USER_AGENT}, ) as session:
        async with session.get(url=url_to_description) as response:
            soup = BeautifulSoup(await response.text(), 'html.parser')
            title_data_info = str(soup.findAll("script", {"id": "__NEXT_DATA__"})[0].contents[0])
            title_data_info_dict: dict[str, Any] = json.loads(title_data_info)
            title_hd_code: Optional[str] = ''
            for name, film_dict in title_data_info_dict['props']['apolloState']['data'].items():
                if name.startswith(title_type) and str(film_id) in name:
                    title_hd_code = film_dict['contentId']
            return f'https://hd.kinopoisk.ru/film/{title_hd_code}', title_hd_code is not None


async def get_title_info_by_name(film_name: str) -> Optional[dict[str, Any]]:
    url: str = 'https://kinopoiskapiunofficial.tech/api/v2.1/films/search-by-keyword'
    params: dict[str, Any] = {"keyword": film_name}
    async with ClientSession(headers={'X-API-KEY': API_TOKEN}) as session:
        async with session.get(url=url, params=params) as response:
            title_json = await response.json()
            try:
                return title_json["films"][0]
            except KeyError:
                return None


async def is_repeat_or_title_type_change(message: types.Message, state: FSMContext) -> bool:  # type: ignore
    if message.text == "Найти сериал":
        await process_name_serial_text(message, state)
    elif message.text == "Найти фильм":
        await process_name_film(message, state)
    else:
        return False
    return True


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message) -> None:
    await message.answer("Привет!\nЯ бот, который поможет тебе хорошо провести вечер за экраном:)",
                         reply_markup=KEYBOARD)


@dp.message_handler(commands=['help'])
async def send_welcome(message: types.Message) -> None:
    await message.answer("""
    Команды:
    \\help  - Выводит вспомогательную информацию
    \\start - Бот здоровается с вами
    
Текст:
    'Найти фильм' - по названию найдёт фильм на кинопоиске, если он окажется и
    на кинопоискHD, то даст ссылку на просмотр, 
    иначе только пиратский сайт
    'Найти сериал' - по названию найдёт 
    сериал на кинопоиске, спросит сезон и серию 
    и если он окажется и на кинопоискHD, то даст ссылку на просмотр, 
    иначе только пиратский сайт
    """)


@dp.message_handler(Text(equals="Найти фильм"))
async def process_name_film(message: types.Message, state: FSMContext) -> None:
    await message.answer("Какой фильм найти для вас?")
    await Film.name.set()


@dp.message_handler(Text(equals="Найти сериал"))
async def process_name_serial_text(message: types.Message, state: FSMContext) -> None:
    await message.answer("Какой сериал найти для вас?")
    await Serial.name.set()


@dp.message_handler(state=Serial.name)
async def process_name_serial(message: types.Message, state: FSMContext) -> None:
    if not await is_repeat_or_title_type_change(message, state):
        async with state.proxy() as data:
            data['name'] = message.text
        await message.answer("Какой сезон?")
        await Serial.next()


@dp.message_handler(state=Serial.season)
async def process_seasone_serial(message: types.Message, state: FSMContext) -> None:
    if not await is_repeat_or_title_type_change(message, state):
        async with state.proxy() as data:
            data['season'] = message.text
        await message.answer("Какой эпизод?")
        await Serial.next()


@dp.message_handler(state=Serial.episode)
async def process_episode_series(message: types.Message, state: FSMContext) -> None:
    if not await is_repeat_or_title_type_change(message, state):
        async with state.proxy() as data:
            data['episode'] = message.text
        await find_series(message, state)


async def find_title(title_name: str, message: types.Message, title_type: str, season_episode: str = '') -> None:
    title_info: dict[str, Any] = await get_title_info_by_name(title_name)
    print(title_info)
    if title_info is None:
        await message.reply(f"Не нашлось такого {'фильма' if title_type == 'Film' else 'сериала'}")
    else:
        title_id = title_info['filmId']
        kinopoisk_url = f'https://www.kinopoisk.ru/film/{title_id}'
        kinopoisk_hd_url, can_watch_on_kinopoiskhd = await get_url_to_watch(kinopoisk_url, title_id, title_type)
        kinopoisk_hd_url = f"{kinopoisk_hd_url}?watch={season_episode}"

        inline_buttons = InlineKeyboardMarkup(row_width=1)
        if can_watch_on_kinopoiskhd:
            inline_buttons.add(InlineKeyboardButton("Смотреть на КинопоискHD", kinopoisk_hd_url))
        inline_buttons.add(InlineKeyboardButton("Смотреть на пиратском сайте", kinopoisk_url.replace('ru', 'gg')))
        await message.answer_photo(title_info['posterUrlPreview'], reply_markup=KEYBOARD)

        film_info = f'''<b>Средняя оценка на кинопоиске:</b> {title_info['rating']} \n\n<b>Описание:</b>\n{title_info['description']}'''
        await message.answer(film_info, reply_markup=inline_buttons, parse_mode="HTML")


@dp.message_handler(state=Film.name)
async def find_film(message: types.Message, state: FSMContext) -> None:
    if not await is_repeat_or_title_type_change(message, state):
        await find_title(message.text, message, 'Film')
        await state.finish()


@dp.message_handler(state=Serial.episode)
async def find_series(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        serial_name: str = data['name']
        serial_season: str = data['season']
        serial_episode: str = data['episode']
    await find_title(serial_name, message, 'TvSeries', f'&season={serial_season}&episode={serial_episode}')
    await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
