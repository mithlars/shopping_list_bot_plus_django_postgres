from typing import Tuple

from aiogram import F, Router
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from requests import Response

from bot.api.django_auth import django_auth, update_last_request_time
from bot.business_processes.groups.utils.groups_menu_keyboard import groups_main_menu_keyboard_builder
from .group_change_current import GroupChangeCurrentStart
from ..lists.utils.lits_details_api import get_lists_detail_api
from ...constants import django_address
from ...create_bot import MyBot


class GroupDeleteDataProcessing:

    @staticmethod
    async def data_to_text_and_keyboard(groups_data: list) -> Tuple[str, InlineKeyboardMarkup]:
        """
                Функция-parser, принимает ответ от Django, парсит его в текст сообщения
            со списком категорий и клавиатуру для выбора категории на удаление.
        """
        message_text = ""
        number = 1
        builder = InlineKeyboardBuilder()
        for group_dict in groups_data:
            group_name = group_dict["name"]
            group_description = group_dict.get('description', '')
            if len(group_dict['categories']) == 0:
                message_text += f"*"
            message_text += f"{number}. {group_name}"
            if group_description != '':
                message_text += f" ({group_description})"
            if len(group_dict['categories']) == 0:
                message_text += f"*\n"
            else:
                message_text += "\n"
            builder.add(InlineKeyboardButton(text=f"{number}",
                                             callback_data=f"del_group {group_dict['id']}"))
            number += 1
        keyboard = builder.as_markup(resize_keyboard=True)
        if message_text == "":
            message_text = "Список групп пока пуст."
        return message_text, keyboard


class GroupsAPI:

    @staticmethod
    @update_last_request_time(django_auth)
    async def delete_group_api(telegram_user_id: int, group_id: int) -> Response:
        """ API-запрос в Django на удаление группы. """

        url = f"{django_address}/groups/delete/"
        data = {
            "telegram_user_id": telegram_user_id,
            "group_id": group_id
        }
        response = await django_auth.session.delete(url=url, data=data)
        return response

    @staticmethod
    @update_last_request_time(django_auth)
    async def get_groups_for_current_list_api(telegram_user_id: int) -> Tuple[str, InlineKeyboardMarkup]:
        """
                API-запрос в Django на список групп.
            Группы запрашиваются с категориями, чтобы подсветить пустые, как готовые к удалению.
            Ответ проходит через функцию-parser, которая возвращает готовый текст сообщения
            и inline-клавиатуру для выбора группы для удаления.
        """
        url = f"{django_address}/groups/"
        data = {"telegram_user_id": telegram_user_id}
        response = django_auth.session.get(url=url, data=data)
        message_text, keyboard = await GroupDeleteDataProcessing.data_to_text_and_keyboard(response.json())
        return message_text, keyboard


group_delete_router = Router()


class GroupDelete:

    @staticmethod
    async def group_delete(telegram_user_id: int):
        """
                Функция получает от функции get_hole_list тексты сообщений:
            'о списке' и второе с его содержимым и клавиатуру для удаления позиций списка
        """
        list_name = await get_lists_detail_api(telegram_user_id)
        text_categories, delete_keyboard = await GroupsAPI.get_groups_for_current_list_api(telegram_user_id)

        list_message_name = (f"""Удаление категорий списка *"{list_name}"*\n"""
                             f"""(можно удалить только *пустые категории*):""")
        main_keyboard = await groups_main_menu_keyboard_builder()
        #  Отправка сообщения "Список {list_name}:" с выводом основной клавиатуры:
        await MyBot.bot.send_message(chat_id=telegram_user_id,
                                     text=list_message_name,
                                     reply_markup=main_keyboard,
                                     parse_mode='Markdown')

        #  Отправка сообщения со списком категорий и inline-клавиатурой для удаления категорий:
        await MyBot.bot.send_message(chat_id=telegram_user_id,
                                     text=text_categories,
                                     reply_markup=delete_keyboard,
                                     parse_mode='Markdown')

    @staticmethod
    @group_delete_router.message(F.text == "❌️🗃️")
    async def group_delete_start_handler(message: Message):
        """ Handler-функция для вывода списка с клавиатурой для выбора группу для удаления """
        await GroupDelete.group_delete(message.from_user.id)

    @staticmethod
    @group_delete_router.callback_query(lambda c: c.data and c.data.startswith('del_group'))
    async def categories_delete_handler(callback: CallbackQuery):
        """ Handler-функция парсит inline-запрос, дает команду на удаления категории. """
        telegram_user_id = callback.from_user.id
        group_id = int(callback.data.split(" ")[1])
        response = await GroupsAPI.delete_group_api(telegram_user_id, group_id)

        if response.status_code == 406:
            message_text = response.json()['error']
            await MyBot.bot.send_message(chat_id=telegram_user_id, text=message_text, parse_mode='Markdown')
            await GroupDelete.group_delete(telegram_user_id)
        elif response.status_code != 200:
            message_text = "Что-то пошло не так"
            await MyBot.bot.send_message(chat_id=telegram_user_id, text=message_text, parse_mode='Markdown')
            await GroupDelete.group_delete(telegram_user_id)
        else:
            message_text = f"Группа {response.json()['name']} удалена"
            await MyBot.bot.send_message(chat_id=telegram_user_id, text=message_text)
            await GroupChangeCurrentStart.change_current_group(telegram_user_id)
            # await GroupsRead.groups_read_and_main_menu(telegram_user_id)

