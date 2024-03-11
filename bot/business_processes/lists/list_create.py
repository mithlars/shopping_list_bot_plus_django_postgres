from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from requests import Response

from bot.create_bot import MyBot
from bot.api.django_auth import update_last_request_time, django_auth

from .lists_read_and_menu import ListsReadAndMenu
from .utils.lists_menu_keyboard import lists_menu_keyboard_buttons
from ...constants import django_address, buttons_styles
from ...translate import transl


class ListCreateAPI:
    @staticmethod
    @update_last_request_time(django_auth)
    async def create_new_list(telegram_user_id: int, new_list_name: str, new_list_description: str) -> Response:
        """Create new list"""
        url = f"{django_address}/lists/create_update_new_list/"
        data = {
            "telegram_user_id": telegram_user_id,
            "name": new_list_name,
            "description": new_list_description
        }
        response = await django_auth.session.post(url=url, data=data)
        return response


class StatesNewList(StatesGroup):
    name = State()
    description = State()


list_create_router = Router()


class ListCreateHandler:

    @staticmethod
    @list_create_router.message(
        lambda message:
        any(message.text == lists_menu_keyboard_buttons(lang)[button_style]['add']
            for lang in transl.keys() for button_style in buttons_styles)
    )
    async def create_new_list_handler(message: Message, state: FSMContext):
        kb = [[KeyboardButton(text="➕📦Отмена")]]
        stop_kb = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        await state.set_state(StatesNewList.name)
        await MyBot.bot.send_message(message.chat.id, 'Введите имя нового списка', reply_markup=stop_kb)

    @staticmethod
    @list_create_router.message(F.text == '➕📦Отмена')
    async def state_cancel_handler(message: Message, state: FSMContext):
        telegram_user_id = message.from_user.id
        await state.clear()
        await ListsReadAndMenu.lists_read_and_menu(telegram_user_id)

    @staticmethod
    @list_create_router.message(StatesNewList.name)
    async def add_name_for_new_list_handler(message: Message, state: FSMContext):
        kb = [[KeyboardButton(text="Без описания"), KeyboardButton(text="➕📦Отмена")]]
        stop_kb = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        await state.update_data(name=message.text, description="")
        await state.set_state(StatesNewList.description)
        await MyBot.bot.send_message(message.chat.id, "Теперь введите описание", reply_markup=stop_kb)

    @staticmethod
    @list_create_router.message(StatesNewList.description)
    async def add_description_for_new_list_handler(message: Message, state: FSMContext):
        telegram_user_id = message.from_user.id
        if message.text != "Без описания":
            await state.update_data(description=message.text)
        data = await state.get_data()
        new_list_name = data['name']
        new_list_description = data["description"]
        await state.clear()
        response = await ListCreateAPI.create_new_list(telegram_user_id, new_list_name, new_list_description)
        if response.status_code != 200:
            await MyBot.bot.send_message(chat_id=telegram_user_id, text="Что-то пошло не так...")
        else:
            message_text = f"Новый список *\"{new_list_name}\"* создан.\nОписание: *\"{new_list_description}\"*\n"
            await MyBot.bot.send_message(chat_id=telegram_user_id, text=message_text, parse_mode='Markdown')
        #  Чтение списка списков:
        await ListsReadAndMenu.lists_read_and_menu(telegram_user_id)
