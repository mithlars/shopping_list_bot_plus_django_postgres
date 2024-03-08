from typing import Tuple

from aiogram import Router
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery, KeyboardButton, InlineKeyboardMarkup, \
    ReplyKeyboardMarkup
from aiogram import F
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from requests import Response

from bot.api.django_auth import update_last_request_time, django_auth
from bot.business_processes.lists.utils.lits_details_api import get_lists_detail_api
from bot.constants import django_address
from bot.create_bot import MyBot

lists_share_router = Router()


class ListsShareStart:

    @staticmethod
    async def users_lists_data_processing(list_of_lists: list) -> Tuple[str, InlineKeyboardMarkup]:
        message_text = ""
        number = 1
        builder = InlineKeyboardBuilder()
        current_list_data = list_of_lists.pop()
        for list_dict in list_of_lists:
            list_dict_fields = list_dict['fields']
            list_id = list_dict["pk"]
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
            builder.add(
                InlineKeyboardButton(text=f"{number}", callback_data=f"share_list {list_id}")
            )
            number += 1
        builder.adjust(4)
        keyboard = builder.as_markup(resize_keyboard=True)
        if message_text == "":
            message_text = ("У Вас пока нет списков.\nВернитесь в меню списков "
                            "и нажмите \"➕📦\" чтобы создать новый список.")
        return message_text, keyboard

    @staticmethod
    @update_last_request_time(django_auth)
    async def lists_to_share_api(telegram_user_id: int) -> Tuple[str, InlineKeyboardMarkup]:
        url = f"{django_address}/lists/users_lists/"
        data = {"telegram_user_id": telegram_user_id}
        response = django_auth.session.get(url=url, data=data)
        message_text, keyboard = await ListsShareStart.users_lists_data_processing(response.json())
        return message_text, keyboard

    @staticmethod
    async def share_main_keyboard() -> ReplyKeyboardMarkup:
        builder = ReplyKeyboardBuilder()
        button_1 = KeyboardButton(text="Доступ к списку")
        button_2 = KeyboardButton(text="Окружение")
        button_3 = KeyboardButton(text="Добавь меня")
        button_4 = KeyboardButton(text="↩️📦")
        button_5 = KeyboardButton(text="↩️📋")
        builder.add(button_1, button_2, button_3, button_4, button_5)
        builder.adjust(3, 2)
        keyboard = builder.as_markup(resize_keyboard=True)
        return keyboard

    @staticmethod
    async def lists_share_start(telegram_user_id: int):
        message_1_text = "К какому списку Вы хотите дать доступ?:"
        menu_keyboard = await ListsShareStart.share_main_keyboard()
        await MyBot.bot.send_message(chat_id=telegram_user_id, text=message_1_text, reply_markup=menu_keyboard)

        message_2_text, inline_keyboard = await ListsShareStart.lists_to_share_api(telegram_user_id)
        await MyBot.bot.send_message(chat_id=telegram_user_id, text=message_2_text,
                                     reply_markup=inline_keyboard, parse_mode="Markdown")

    @staticmethod
    @lists_share_router.message((F.text == "👨‍👦‍👦‍Sha") |
                                (F.text == "👨‍👦‍👦‍") |
                                (F.text == "доступ"))
    async def lists_share_start_handler(message: Message):
        telegram_user_id = message.from_user.id
        await ListsShareStart.lists_share_start(telegram_user_id)


class ListShareChooseList:

    @staticmethod
    async def processing_data(friends_data: list, list_id: str) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for friend in friends_data:
            friend_id = friend['pk']
            friend_firstname = friend['fields']['telegram_firstname']
            friend_lastname = friend['fields']['telegram_lastname']
            text = f"{friend_firstname} {friend_lastname}"
            if int(list_id) in friend['fields']['lists']:
                text = f"✅  {text}"
                move = "unshare"
            else:
                text = f"⬜  {text}"
                move = "share"
            callback_data = f"share_list_to {friend_id} {move} {list_id}"
            builder.add(InlineKeyboardButton(text=text, callback_data=callback_data))
        builder.adjust(1)
        keyboard = builder.as_markup(resize_keyboard=True)
        return keyboard

    @staticmethod
    @update_last_request_time(django_auth)
    async def get_friends_api(telegram_user_id: int, list_id: str) -> InlineKeyboardMarkup:
        url = f"{django_address}/profiles/get_friends/"
        data = {"telegram_user_id": telegram_user_id}
        response = django_auth.session.get(url=url, data=data)
        friends_keyboard = await ListShareChooseList.processing_data(response.json(), list_id)
        return friends_keyboard

    @staticmethod
    @lists_share_router.callback_query(lambda c: c.data and c.data.startswith("share_list "))
    async def share_list_handler(callback: CallbackQuery):
        telegram_user_id = callback.from_user.id
        list_id = callback.data.split(" ")[1]
        friends_keyboard = await ListShareChooseList.get_friends_api(telegram_user_id, list_id)
        if not friends_keyboard.inline_keyboard:
            message_text = "В Вашем окружении никого нет."
        else:
            list_name = await get_lists_detail_api(telegram_user_id, list_id)
            message_text = f"Выберите кто из Вашего окружения может работать со списком \"{list_name}\":"
        await MyBot.bot.send_message(chat_id=telegram_user_id, text=message_text, reply_markup=friends_keyboard)


class ListShare:

    @staticmethod
    @update_last_request_time(django_auth)
    async def share_list_api(telegram_user_id: int, friend_id: str, move: str, list_id: str) -> Response:
        url = f"{django_address}/lists/update_access/"
        data = {
            "telegram_user_id": telegram_user_id,
            "friend_id": friend_id,
            "move": move,
            "list_id": list_id
        }
        response = await django_auth.session.put(url=url, data=data)
        return response

    @staticmethod
    @lists_share_router.callback_query(lambda c: c.data and c.data.startswith("share_list_to "))
    async def share_list_handler(callback: CallbackQuery):
        telegram_user_id = callback.from_user.id
        message_id = callback.message.message_id
        friend_id, move, list_id = callback.data.split(" ")[1:]
        response = await ListShare.share_list_api(telegram_user_id, friend_id, move, list_id)
        if response.status_code != 200:
            await MyBot.bot.send_message(chat_id=telegram_user_id, text="Что-то пошло не так")
        friends_keyboard = await ListShareChooseList.get_friends_api(telegram_user_id, list_id)
        await MyBot.bot.edit_message_reply_markup(chat_id=telegram_user_id,
                                                  message_id=message_id,
                                                  reply_markup=friends_keyboard)
