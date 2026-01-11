from aiogram import Router,F
from aiogram.types import Message,CallbackQuery,KeyboardButton,InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder,InlineKeyboardBuilder
import asyncio
import aiohttp
from aiogram.fsm.state import State,StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters.callback_data import CallbackData
from secret_data import API_KEY

router = Router()

API_URL = "https://ws.audioscrobbler.com/2.0"

class Find_music(StatesGroup):
    name_track = State()

class Music_data(CallbackData,prefix = "music"):
    artist:str
    track_name:str

def get_duration(data:dict):
    if not data["track"]["duration"]:
        duration = "Нейзвестно"
        return duration
    duration = int(data["track"]["duration"])//1000
    minutes = duration//60
    seconds = duration%60
    if seconds<10:
        duration = f"{minutes}:0{seconds}"
    else:
        duration = f"{minutes}:{seconds}"
    return duration

def get_tags(data:dict):
    tags = data["track"].get("toptags",{}).get("tag",[])
    if isinstance(tags,dict):
        tags = [tags]
    if not tags:
        return "неизвестно"
    genres = [tag["name"] for tag in tags[:3]]
    return ",".join(genres)

def get_release(data:dict):
    release = data["track"].get("wiki",{}).get("published")
    if release and isinstance(release,str):
        return release.split(",")[0]
    else: 
        return "неизвестно"

def get_image(data:dict):
    image = image = data["track"]["album"]
    if image and image.get("image"):
        return data["track"]["album"]["image"][-1]["#text"]
    else:
        return "неизвестно"

@router.message(Command("start"))
async def handler1(message:Message,state:FSMContext):
    await message.answer("Здраствуйте, чтобы найти информацию по музыке, пожалуйста, введите её название!")
    await state.set_state(Find_music.name_track)

@router.message(Find_music.name_track)
async def handleer2(message:Message,state:FSMContext):
    async with aiohttp.ClientSession() as session:
        params = {
        "method": "track.search",
        "track": message.text,
        "api_key": API_KEY,
        "format": "json"
        }
        try:
            async with session.get(url = API_URL,params = params) as response:
                response.raise_for_status()
                data = await response.json()
                if not data.get("results",{}).get("trackmatches",{}).get("track"):
                    await message.answer("К сожалению мы ничего не смогли найти:(")
                    await state.clear() 
                    return  

            music_data = data["results"]["trackmatches"]["track"]

            builder = InlineKeyboardBuilder()
            for track in music_data[:7]:
                 builder.row(InlineKeyboardButton(text = track.get("artist"),callback_data=Music_data(
                     track_name = message.text,
                     artist = track.get("artist")).pack()))
            await message.answer("Вот предположительные варинаты того что вы искали:",reply_markup = builder.as_markup())
        except Exception as e:
            await message.answer("Произошла ошибка извините")
            print(e)
        finally:
            await state.clear()

@router.callback_query(Music_data.filter())
async def handelr3(callback:CallbackQuery,callback_data:Music_data):
    async with aiohttp.ClientSession() as session:
        params = {
        "artist":callback_data.artist,
        "method": "track.getInfo",
        "track": callback_data.track_name,
        "api_key": API_KEY,
        "format": "json"
        }
        try:
            async with session.get(url = API_URL,params = params) as response:
                response.raise_for_status()
                data = await response.json()
            if "track" in data:
                duration = get_duration(data)
                release = get_release(data)
                tags = get_tags(data)
                image = get_image(data)
                await callback.message.answer_photo(image)
                await callback.message.answer(f"{callback_data.artist} опубликовал {callback_data.track_name} - {release}. {callback_data.track_name} длится - {duration} и его жанры {tags} ")
            else:
                await callback.message.answer("Извините не удалось найти информацию")
        except Exception as e:
            await callback.message.answer("Извните произошла ошибка")
            print(e) 
