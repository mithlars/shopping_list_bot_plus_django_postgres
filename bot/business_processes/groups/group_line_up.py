from typing import Tuple

from aiogram import Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from requests import Response

from bot.api.django_auth import django_auth, update_last_request_time
from bot.constants import django_address
from bot.create_bot import MyBot

from aiogram.utils.i18n import gettext as _

group_lineup_router = Router()


class GroupLineUpStart:

    @staticmethod
    async def groups_data_processing(list_of_groups: list) -> Tuple[str, InlineKeyboardMarkup]:
        message_text = _("Choose group to edit categories lineup:\n")
        number = 1
        builder = InlineKeyboardBuilder()
        for group_dict in list_of_groups:
            message_text += f"{number}. {group_dict['name']}"
            if group_dict['description'] != '' and group_dict['description'] is not None:
                message_text += f" ({group_dict['description']}).\n"
            else:
                message_text += "\n"

            builder.add(InlineKeyboardButton(text=f"{number}",
                                             callback_data=f"group_lineup;:{group_dict['id']};:{group_dict['name']}"))
            number += 1
        builder.adjust(6)
        keyboard = builder.as_markup(resize_keyboard=True)
        return message_text, keyboard

    @staticmethod
    @update_last_request_time(django_auth)
    async def groups_read_for_lineup_api(telegram_user_id: int) -> Tuple[str, InlineKeyboardMarkup]:
        url = f"{django_address}/groups/"
        data = {"telegram_user_id": telegram_user_id}
        response = django_auth.session.get(url=url, data=data)
        message_text, keyboard = await GroupLineUpStart.groups_data_processing(response.json())
        return message_text, keyboard

    @staticmethod
    @group_lineup_router.callback_query(lambda c: c.data and c.data == "group_lineup")
    async def groups_read_for_lineup_handler(callback: CallbackQuery):
        telegram_user_id = callback.from_user.id
        message_text, keyboard = await GroupLineUpStart.groups_read_for_lineup_api(telegram_user_id)
        await MyBot.bot.send_message(chat_id=telegram_user_id, text=message_text, reply_markup=keyboard)


class GroupLineUpCategories:

    @staticmethod
    async def categories_data_processing(list_of_categories: list, group_id: str, groups_categories: list
                                         ) -> InlineKeyboardMarkup:
        number = 1
        builder = InlineKeyboardBuilder()
        for category_dict in list_of_categories:
            text = ''
            if category_dict['id'] in groups_categories:
                text += "✅ "
                move = "exclude"
            else:
                text += "⬜ "
                move = "include"
            text += f"{number}. {category_dict['name']}"
            if category_dict['description'] != '' and category_dict['description'] is not None:
                text += f" ({category_dict['description']})."
            builder.add(InlineKeyboardButton(
                text=text,
                callback_data=f"category_add_to_group {move} {category_dict['id']} {group_id}")
            )
            number += 1
        builder.adjust(1)
        keyboard = builder.as_markup(resize_keyboard=True)
        return keyboard

    @staticmethod
    @update_last_request_time(django_auth)
    async def get_groups_categories_list_api(telegram_user_id: int, group_id: str) -> list:
        url = f"{django_address}/groups/categories/"
        data = {
            "telegram_user_id": telegram_user_id,
            "group_id": group_id
        }
        response = django_auth.session.get(url=url, data=data)
        return response.json()['list']

    @staticmethod
    @update_last_request_time(django_auth)
    async def categories_read_for_group_api(telegram_user_id: int, group_id: str, groups_categories: list
                                            ) -> InlineKeyboardMarkup:
        url = f"{django_address}/categories/"
        data = {"telegram_user_id": telegram_user_id}
        response = django_auth.session.get(url=url, data=data)
        keyboard = \
            await GroupLineUpCategories.categories_data_processing(response.json(), group_id, groups_categories)
        return keyboard

    @staticmethod
    @group_lineup_router.callback_query(lambda c: c.data and c.data.startswith("group_lineup;:"))
    async def categories_read_for_group_handler(callback: CallbackQuery):
        telegram_user_id = callback.from_user.id
        print(f"{callback.data = }")
        group_id, group_name = callback.data.split(';:')[1:]
        groups_categories = await GroupLineUpCategories.get_groups_categories_list_api(telegram_user_id, group_id)
        keyboard = \
            await GroupLineUpCategories.categories_read_for_group_api(telegram_user_id, group_id, groups_categories)
        message_text = _("Select the categories that will be displayed in the group") + f" \"{group_name}\":"
        await MyBot.bot.send_message(chat_id=telegram_user_id,
                                     text=message_text,
                                     reply_markup=keyboard)


class GroupLineUpCategory:

    @staticmethod
    @update_last_request_time(django_auth)
    async def category_in_to_group_api(telegram_user_id: int, category_id: str, group_id: str, move: str
                                       ) -> Response:
        url = f"{django_address}/groups/category_in_out/"
        data = {
            "telegram_user_id": telegram_user_id,
            "category_id": category_id,
            "group_id": group_id,
            "move": move
        }
        response = await django_auth.session.put(url=url, data=data)
        return response

    @staticmethod
    @group_lineup_router.callback_query(lambda c: c.data and c.data.startswith("category_add_to_group "))
    async def category_in_to_group_handler(callback: CallbackQuery):
        telegram_user_id = callback.from_user.id
        message_id = callback.message.message_id
        move, category_id, group_id = callback.data.split(' ')[1:]
        response = \
            await GroupLineUpCategory.category_in_to_group_api(telegram_user_id, category_id, group_id, move)
        if response.status_code == 200:
            groups_categories = await GroupLineUpCategories.get_groups_categories_list_api(telegram_user_id, group_id)
            keyboard = \
                await GroupLineUpCategories.categories_read_for_group_api(telegram_user_id, group_id, groups_categories)
            await MyBot.bot.edit_message_reply_markup(chat_id=telegram_user_id,
                                                      message_id=message_id,
                                                      reply_markup=keyboard)
        else:
            message_text = _("Somthing went rong")
            await MyBot.bot.send_message(chat_id=telegram_user_id, text=message_text)
