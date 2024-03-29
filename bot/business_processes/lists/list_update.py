from typing import Any, Dict

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, ReplyKeyboardRemove, KeyboardButton, \
    ReplyKeyboardMarkup
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.create_bot import MyBot

from bot.api.django_auth import update_last_request_time, django_auth
from .list_change_current import ListChangeCurrent
from .utils.lists_menu_keyboard import lists_menu_keyboard_buttons
from ...constants import django_address, buttons_styles
from ...emoji import emoji
from ...translate import transl

from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __

list_update_router = Router()


class UpdateListStart:

    @staticmethod
    async def data_processing(list_of_lists: list) -> Dict[str, Any]:
        message_text = _("Choose list for edit\n")
        number = 1
        builder = InlineKeyboardBuilder()
        current_list_data = list_of_lists.pop()
        for list_dict in list_of_lists:
            list_dict_fields = list_dict['fields']
            if list_dict_fields['name'] == current_list_data['name']:
                message_text += f"*{number}. {list_dict_fields['name']}*"
            else:
                message_text += f"{number}. {list_dict_fields['name']}"
            if list_dict_fields['description']:
                if list_dict_fields['description'] == current_list_data['description']:
                    message_text += f" *({list_dict_fields['description']}).*\n"
                else:
                    message_text += f" ({list_dict_fields['description']}).\n"
            else:
                message_text += "\n"
            builder.add(InlineKeyboardButton(text=f"{number}",
                                             callback_data=f"update_list, "
                                                           f"{list_dict['pk']}, "
                                                           f"{list_dict_fields['name']}, "
                                                           f"{list_dict_fields['description']}"))
            number += 1
        builder.adjust(5)
        message_text_and_keyboard = {
            "text": message_text,
            "keyboard": builder.as_markup(resize_keyboard=True)
        }
        return message_text_and_keyboard

    @staticmethod
    @update_last_request_time(django_auth)
    async def users_lists_read_api(telegram_user_id: int) -> Dict[str, Any]:
        url = f"{django_address}/lists/users_lists/"
        data = {"telegram_user_id": telegram_user_id}
        response = django_auth.session.get(url=url, data=data)
        text_and_keyboard = await UpdateListStart.data_processing(response.json())
        return text_and_keyboard

    @staticmethod
    @list_update_router.message(
        lambda message:
        any(message.text == lists_menu_keyboard_buttons(lang)[button_style]['edit']
            for lang in transl.keys() for button_style in buttons_styles)
    )
    async def choose_list_for_update_handler(message: Message):
        telegram_user_id = message.from_user.id
        text_and_keyboard = await UpdateListStart.users_lists_read_api(telegram_user_id)
        text = text_and_keyboard['text']
        keyboard = text_and_keyboard['keyboard']
        await MyBot.bot.send_message(chat_id=telegram_user_id, text=text, reply_markup=keyboard, parse_mode='Markdown')


class StatesUpdateList(StatesGroup):
    name = State()
    description = State()


class UpdateListFMS:

    @staticmethod
    @list_update_router.callback_query(lambda c: c.data and c.data.startswith('update_list'))
    async def choose_list_for_update_handler(callback: CallbackQuery, state: FSMContext):
        await state.set_state(StatesUpdateList.name)

        kb = [[KeyboardButton(text=_("No changes")),
               KeyboardButton(text=emoji['edit'] + emoji['lists'] + _("Cancel"))]]
        stop_same_kb = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

        ald_lists_data = callback.data.split(", ")[1:]
        await state.update_data(list_id=ald_lists_data[0],
                                list_ald_name=ald_lists_data[1],
                                list_ald_description=ald_lists_data[2])

        await MyBot.bot.send_message(chat_id=callback.from_user.id,
                                     text=_("Input new name for the list"),
                                     reply_markup=stop_same_kb)

        await MyBot.bot.send_message(chat_id=callback.message.chat.id,
                                     text=f"`{ald_lists_data[1]}`",
                                     parse_mode='MarkdownV2')

    @staticmethod
    @list_update_router.message(F.text.replace(f"{emoji['edit']}{emoji['lists']}", "") == __('Cancel'))
    async def state_cancel_handler(message: Message, state: FSMContext):
        telegram_user_id = message.from_user.id
        await state.clear()
        await ListChangeCurrent.change_current_list(telegram_user_id)

    @staticmethod
    @list_update_router.message(StatesUpdateList.name)
    async def update_list_name_handler(message: Message, state: FSMContext):

        kb = [[KeyboardButton(text=_("No changes")),
               KeyboardButton(text=_("Without description")),
               KeyboardButton(text=emoji['edit'] + emoji['lists'] + _("Cancel"))]]
        stop_same_kb = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

        if message.text == _("No changes"):
            data = await state.get_data()
            await state.update_data(name=data["list_ald_name"])
        else:
            await state.update_data(name=message.text)
        await state.set_state(StatesUpdateList.description)
        await MyBot.bot.send_message(chat_id=message.chat.id,
                                     text=_("Now input new description"),
                                     reply_markup=stop_same_kb)

    @staticmethod
    @update_last_request_time(django_auth)
    async def list_update_api(telegram_user_id: int, data: Dict[str, Any]) -> None:
        url = f"{django_address}/lists/create_update_new_list/"
        data["telegram_user_id"] = telegram_user_id
        await django_auth.session.put(url=url, data=data)

    @staticmethod
    @list_update_router.message(StatesUpdateList.description)
    async def update_list_description_handler(message: Message, state: FSMContext):
        telegram_user_id = message.from_user.id
        list_data = await state.get_data()
        if message.text == _("No changes"):
            list_data["description"] = list_data["list_ald_description"]
        elif message.text == _("Without description"):
            list_data["description"] = ""
        else:
            list_data["description"] = message.text

        await state.clear()
        if (list_data['name'] == list_data["list_ald_name"]
                and list_data["description"] == list_data["list_ald_description"]):
            await MyBot.bot.send_message(chat_id=telegram_user_id,
                                         text=_("Your chose is leave the list without changes"),
                                         reply_markup=ReplyKeyboardRemove())
            await ListChangeCurrent.change_current_list(telegram_user_id)
        else:
            await UpdateListFMS.list_update_api(telegram_user_id, list_data)
            await ListChangeCurrent.change_current_list(telegram_user_id)
