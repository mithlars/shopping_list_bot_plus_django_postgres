from typing import Tuple

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.api.django_auth import django_auth, update_last_request_time
from bot.business_processes.groups.utils.groups_menu_keyboard import groups_menu_keyboard_builder
from bot.business_processes.lists.utils.lits_details_api import get_lists_detail_api
from bot.business_processes.purchases.utils.list_menu_keyboard import list_menu_keyboard_buttons
from bot.constants import django_address, buttons_styles
from bot.create_bot import MyBot
from bot.translate import transl

group_change_current_router = Router()


class GroupChangeCurrentStart:

    @staticmethod
    async def data_processing(list_of_groups: list, current_group_id: int) -> Tuple[str, InlineKeyboardMarkup]:
        message_text = "Ваши группы:\n"
        number = 1
        builder = InlineKeyboardBuilder()
        for group_dict in list_of_groups:
            if group_dict['id'] == current_group_id:
                message_text += '*'
            message_text += f"{number}. {group_dict['name']}"
            if group_dict['description']:
                message_text += f" ({group_dict['description']})."
            if group_dict['id'] == current_group_id:
                message_text += '*\n'
            else:
                message_text += '\n'
            builder.add(InlineKeyboardButton(text=f"{number}",
                                             callback_data=f"choose_current_group {group_dict['id']}"))
            number += 1
        builder.add(InlineKeyboardButton(text="Весь список", callback_data="choose_current_group "))
        builder.adjust(6)
        keyboard = builder.as_markup(resize_keyboard=True)
        return message_text, keyboard

    @staticmethod
    @update_last_request_time(django_auth)
    async def get_list_of_groups(telegram_user_id: int, current_group_id: int) -> Tuple[str, InlineKeyboardMarkup]:
        url = f"{django_address}/groups/"
        data = {"telegram_user_id": telegram_user_id}
        response = django_auth.session.get(url=url, data=data)
        message_text, keyboard = await GroupChangeCurrentStart.data_processing(response.json(), current_group_id)
        return message_text, keyboard

    @staticmethod
    @update_last_request_time(django_auth)
    async def get_current_group(telegram_user_id: int) -> int:
        url = f"{django_address}/groups/get_current/"
        data = {"telegram_user_id": telegram_user_id}
        response = django_auth.session.get(url=url, data=data)
        return response.json()["current_group"]

    @staticmethod
    async def change_current_group(telegram_user_id: int):
        list_name = await get_lists_detail_api(telegram_user_id)
        list_message_name = f"Группы списка \n\"{list_name}\":"
        keyboard = await groups_menu_keyboard_builder(telegram_user_id)
        await MyBot.bot.send_message(chat_id=telegram_user_id, text=list_message_name, reply_markup=keyboard)

        current_group_id = await GroupChangeCurrentStart.get_current_group(telegram_user_id)
        message_text, keyboard = await GroupChangeCurrentStart.get_list_of_groups(telegram_user_id, current_group_id)
        await MyBot.bot.send_message(chat_id=telegram_user_id,
                                     text=message_text,
                                     reply_markup=keyboard,
                                     parse_mode='Markdown')

    @staticmethod
    @group_change_current_router.message(
        lambda message:
        any(message.text == list_menu_keyboard_buttons(lang)[button_style]['groups']
            for lang in transl.keys() for button_style in buttons_styles)
    )
    async def change_current_group_handler(message: Message):
        telegram_user_id = message.from_user.id
        await GroupChangeCurrentStart.change_current_group(telegram_user_id)


class GroupChangeCurrent:

    @staticmethod
    @update_last_request_time(django_auth)
    async def change_current_api(telegram_user_id: int, new_current_list_id: str) -> int:
        url = f"{django_address}/groups/change_current/"
        data = {
            "telegram_user_id": telegram_user_id,
            "new_current_group_id": new_current_list_id
        }
        response = await django_auth.session.put(url=url, data=data)
        return response.status_code

    @staticmethod
    @group_change_current_router.callback_query(lambda c: c.data and c.data.startswith('choose_current_group'))
    async def choose_current_group_handler(callback: CallbackQuery):
        telegram_user_id = callback.from_user.id
        new_current_group_id = callback.data.split(" ")[1]
        response_status = await GroupChangeCurrent.change_current_api(telegram_user_id, new_current_group_id)
        if response_status != 200:
            await MyBot.bot.send_message(chat_id=telegram_user_id, text='Что-то пошло не так...')
        await GroupChangeCurrentStart.change_current_group(telegram_user_id)
