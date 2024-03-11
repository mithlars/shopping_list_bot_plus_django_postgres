from typing import Dict, Any, Tuple

from aiogram import types, Router, F
from aiogram.types import InlineKeyboardButton, KeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from bot.business_processes.lists.utils.lists_menu_keyboard import lists_menu_keyboard_buttons
from bot.business_processes.lists.utils.lits_details_api import get_lists_detail_api
from bot.business_processes.purchases.utils.list_menu_keyboard import list_menu_keyboard_builder, \
    list_menu_keyboard_buttons
from bot.constants import django_address, buttons_styles
from bot.create_bot import MyBot
from bot.api.django_auth import django_auth, update_last_request_time
from bot.emoji import emoji
from bot.translate import transl


class ListDataProcessing:

    @staticmethod
    async def data_to_text_and_keyboard(list_data: list) -> Tuple[str, InlineKeyboardMarkup]:
        message_text = ""
        number_count = 1
        builder = InlineKeyboardBuilder()
        for category_dict in list_data:
            category_name = category_dict["name"]
            purchases_list = category_dict["purchases"]
            if purchases_list:
                message_text += f"____{category_name}\n"
                for purchase_dict in purchases_list:
                    message_text += f"{number_count}. {purchase_dict['name']}"
                    if purchase_dict['description']:
                        message_text += f" ({purchase_dict['description']})\n"
                    else:
                        message_text += "\n"
                    builder.add(InlineKeyboardButton(text=f"{number_count}",
                                                     callback_data=f"del_pur {purchase_dict['id']}"))
                    number_count += 1
        if message_text == "":
            message_text = "Список (категории группы) пока пуст(ы)."
        keyboard = builder.as_markup(resize_keyboard=True)
        return message_text, keyboard


class ListReadAPI:

    @staticmethod
    @update_last_request_time(django_auth)
    async def get_hole_list(telegram_user_id: int) -> Tuple[str, InlineKeyboardMarkup]:
        """Read one single list with categories and their purchases."""
        url = f"{django_address}/lists/list_or_group/"
        data = {"telegram_user_id": telegram_user_id}
        response = django_auth.session.get(url=url, data=data)
        message_text, keyboard = await ListDataProcessing.data_to_text_and_keyboard(response.json())
        return message_text, keyboard


list_read_router = Router()


class ListRead:

    @staticmethod
    async def get_current_lists_purchases_list(telegram_user_id: int):
        """
                Функция получает от функции get_hole_list тексты сообщений:
            'о списке' и второе с его содержимым и клавиатуру для удаления позиций списка
        """
        # Запрос возвращает имя списка для сообщения:
        list_name = await get_lists_detail_api(telegram_user_id)
        list_message_text = f"Список \"{list_name}\":"

        # Отправка сообщения "Список {list_name}:" с выводом основной клавиатуры:
        await MyBot.bot.send_message(chat_id=telegram_user_id,
                                     text=list_message_text,
                                     reply_markup=await list_menu_keyboard_builder(telegram_user_id))

        # Запрос возвращает текст сообщения с содержимым списка или группы и клавиатуру удаления позиций:
        message_text, keyboard = await ListReadAPI.get_hole_list(telegram_user_id)

        # Отправка сообщения с содержимым списка и inline-клавиатурой для удаления позиций:
        await MyBot.bot.send_message(chat_id=telegram_user_id,
                                     text=message_text,
                                     reply_markup=keyboard)

    @staticmethod
    @list_read_router.message(
        lambda message:
        any(message.text == list_menu_keyboard_buttons(lang)[button_style]['reload']
            for lang in transl.keys() for button_style in buttons_styles)
        or any(message.text == lists_menu_keyboard_buttons(lang)[button_style]['back']
               for lang in transl.keys() for button_style in buttons_styles)
    )
    async def list_of_purchases_handler(message: types.Message):
        """ Handler-функция для вывода списка с клавиатурой для удаления позиций """
        await ListRead.get_current_lists_purchases_list(message.from_user.id)
