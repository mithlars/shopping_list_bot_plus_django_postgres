from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from requests import Response

from bot.create_bot import MyBot
from bot.api.django_auth import update_last_request_time, django_auth
from .list_change_current import ListChangeCurrent

from .utils.lists_menu_keyboard import lists_menu_keyboard_buttons
from ...constants import django_address, buttons_styles
from ...emoji import emoji
from ...translate import transl

from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __


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
        kb = [[KeyboardButton(text=_("{add}{lists}Cancel").format(add=emoji['add'], lists=emoji['lists']))]]
        stop_kb = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        await state.set_state(StatesNewList.name)
        await MyBot.bot.send_message(message.chat.id, _("Input new list name"), reply_markup=stop_kb)

    @staticmethod
    @list_create_router.message(F.text.replace(f"{emoji['add']}{emoji['lists']}", "") == __("Cancel"))
    async def state_cancel_handler(message: Message, state: FSMContext):
        telegram_user_id = message.from_user.id
        await state.clear()
        await ListChangeCurrent.change_current_list(telegram_user_id)

    @staticmethod
    @list_create_router.message(StatesNewList.name)
    async def add_name_for_new_list_handler(message: Message, state: FSMContext):
        kb = [[KeyboardButton(text=_("Without description")),
               KeyboardButton(text=_("{add}{lists}Cancel").format(add=emoji['add'], lists=emoji['lists']))]]
        stop_kb = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        await state.update_data(name=message.text, description="")
        await state.set_state(StatesNewList.description)
        await MyBot.bot.send_message(message.chat.id, _("Now input description"), reply_markup=stop_kb)

    @staticmethod
    @list_create_router.message(StatesNewList.description)
    async def add_description_for_new_list_handler(message: Message, state: FSMContext):
        telegram_user_id = message.from_user.id
        if message.text != _("Without description"):
            await state.update_data(description=message.text)
        data = await state.get_data()
        new_list_name = data['name']
        new_list_description = data["description"]
        await state.clear()
        response = await ListCreateAPI.create_new_list(telegram_user_id, new_list_name, new_list_description)
        if response.status_code != 200:
            await MyBot.bot.send_message(chat_id=telegram_user_id, text=_("Somthing went rong"))
        else:
            message_text = _("New list *\"{new_list_name}\"* is created.\nDescription: *\"{new_list_description}\"*\n")\
                            .format(new_list_name=new_list_name, new_list_description=new_list_description)
            await MyBot.bot.send_message(chat_id=telegram_user_id, text=message_text, parse_mode='Markdown')
        #  Чтение списка списков:
        await ListChangeCurrent.change_current_list(telegram_user_id)
