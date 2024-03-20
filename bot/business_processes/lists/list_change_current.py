from typing import Tuple

from aiogram import Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.api.django_auth import django_auth, update_last_request_time
from bot.business_processes.lists.utils.lists_menu_keyboard import lists_menu_keyboard, lists_menu_keyboard_buttons
from bot.business_processes.lists.utils.share_menu_keyboard import share_menu_keyboard_buttons
from bot.business_processes.purchases.utils.list_menu_keyboard import list_menu_keyboard_buttons
from bot.constants import django_address, buttons_styles
from bot.create_bot import MyBot
from bot.translate import transl


class ListChangeCurrentDataProcessing:

    @staticmethod
    async def data_processing(list_of_lists: list) -> Tuple[str, InlineKeyboardMarkup]:
        message_text = ""
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
                                             callback_data=f"choose_as_current_list {list_dict['pk']}"))
            number += 1
        message_text += _("\nHint:\nTo switch to the list -- press button with it's number:")
        builder.adjust(6)
        keyboard = builder.as_markup(resize_keyboard=True)
        return message_text, keyboard


class ListChangeCurrentAPI:
    # TODO: Сделать этот интерфейс стартовым при переходе в меню списков

    @staticmethod
    @update_last_request_time(django_auth)
    async def get_list_of_lists(telegram_user_id: int) -> Tuple[str, InlineKeyboardMarkup]:
        url = f"{django_address}/lists/users_lists/"
        data = {"telegram_user_id": telegram_user_id}
        response = django_auth.session.get(url=url, data=data)
        message_text, choose_current_keyboard = await ListChangeCurrentDataProcessing.data_processing(response.json())
        return message_text, choose_current_keyboard

    @staticmethod
    @update_last_request_time(django_auth)
    async def change_current(telegram_user_id: int, new_current_list_id: int) -> int:
        url = f"{django_address}/lists/change_current/"
        data = {"telegram_user_id": telegram_user_id,
                "new_current_list_id": new_current_list_id}
        response = await django_auth.session.put(url=url, data=str(data))
        return response.status_code


list_change_current_router = Router()


class ListChangeCurrent:

    @staticmethod
    async def change_current_list(telegram_user_id: int) -> None:
        message_text = _("Your lists:\n")
        keyboard = await lists_menu_keyboard(telegram_user_id)
        await MyBot.bot.send_message(telegram_user_id, message_text, reply_markup=keyboard, parse_mode='Markdown')

        message_text, choose_current_keyboard = await ListChangeCurrentAPI.get_list_of_lists(telegram_user_id)
        await MyBot.bot.send_message(chat_id=telegram_user_id, text=message_text,
                                     reply_markup=choose_current_keyboard, parse_mode='Markdown')

    @staticmethod
    @list_change_current_router.message(
        lambda message:
        any(message.text == list_menu_keyboard_buttons(lang)[button_style]['lists']
            for lang in transl.keys() for button_style in buttons_styles)
        or any(message.text == lists_menu_keyboard_buttons(lang)[button_style]['switch']
               for lang in transl.keys() for button_style in buttons_styles)
        or any(message.text == share_menu_keyboard_buttons(lang)[button_style]['back_to_lists']
               for lang in transl.keys() for button_style in buttons_styles)
    )
    async def change_current_list_handler(message: Message):
        telegram_user_id = message.from_user.id
        await ListChangeCurrent.change_current_list(telegram_user_id)

    @staticmethod
    @list_change_current_router.callback_query(lambda c: c.data and c.data.startswith('choose_as_current_list'))
    async def choose_current_list_handler(callback: CallbackQuery):
        telegram_user_id = callback.from_user.id
        new_current_list_id = int(callback.data.split(" ")[1])
        response_status = await ListChangeCurrentAPI.change_current(telegram_user_id, new_current_list_id)
        if response_status != 200:
            await MyBot.bot.send_message(chat_id=telegram_user_id, text=_('Somthing went rong'))
        await ListChangeCurrent.change_current_list(telegram_user_id)
