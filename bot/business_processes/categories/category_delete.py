from typing import Tuple

from aiogram import F, Router
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from requests import Response

from bot.api.django_auth import django_auth, update_last_request_time
from .category_update import UpdateCategoryStart
from .utils.categories_menu_keyboard import categories_keyboard_builder
from ..lists.utils.lits_details_api import get_lists_detail_api
from ..options.utils.get_profiles_options_api import get_profiles_options_api
from ...constants import django_address
from ...create_bot import MyBot
from ...emoji import emoji
from ...translate import transl


class CategoryDeleteDataProcessing:

    @staticmethod
    async def data_to_text_and_keyboard(list_data: list, blank_category: int, lang: str
                                        ) -> Tuple[str, InlineKeyboardMarkup]:
        """
                Функция-parser, принимает ответ от Django, парсит его в текст сообщения
            со списком категорий и клавиатуру для выбора категории на удаление.
        """
        message_text = ""
        number_count = 1
        builder = InlineKeyboardBuilder()
        for category_dict in list_data:
            category_name = category_dict["name"]
            category_description = category_dict.get('description', '')
            if len(category_dict['purchases']) == 0 and category_dict['id'] != blank_category:
                message_text += f"*"
            message_text += f"{number_count}. {category_name}"
            if category_description != '' and category_description is not None:
                message_text += f" ({category_description})"
            if len(category_dict['purchases']) == 0 and category_dict['id'] != blank_category:
                message_text += f"*\n"
            else:
                message_text += "\n"
            builder.add(InlineKeyboardButton(text=f"{number_count}",
                                             callback_data=f"del_category {category_dict['id']} {lang}"))
            number_count += 1
        keyboard = builder.as_markup(resize_keyboard=True)
        return message_text, keyboard


class CategoriesAPI:

    @staticmethod
    @update_last_request_time(django_auth)
    async def get_blank_category_api(telegram_user_id: int) -> int:
        url = f"{django_address}/categories/get_blank/"
        data = {"telegram_user_id": telegram_user_id}
        response = django_auth.session.get(url=url, data=data)
        blank_category_id = response.json()["id"]
        return blank_category_id

    @staticmethod
    @update_last_request_time(django_auth)
    async def delete_category_api(telegram_user_id: int, category_id: int) -> Response:
        """ API-запрос в Django на удаление категории. """

        url = f"{django_address}/categories/delete/"
        data = {
            "telegram_user_id": telegram_user_id,
            "category_id": category_id
        }
        response = await django_auth.session.delete(url=url, data=data)
        return response

    @staticmethod
    @update_last_request_time(django_auth)
    async def get_categories_for_current_list_api(telegram_user_id: int, lang: str) -> Tuple[str, InlineKeyboardMarkup]:
        """
                API-запрос в Django на список категорий.
            Категории запрашиваются с позициями, чтобы подсветить пустые, как готовые к удалению.
            Ответ проходит через функцию-parser.
            Функция возвращает готовый текст сообщения и inline-клавиатуру для выбора категории на удаление.
        """
        url = f"{django_address}/lists/"  # TODO: Переделать на список категорий только с id позиций, без prefetch
        data = {"telegram_user_id": telegram_user_id}
        response = django_auth.session.get(url=url, data=data)
        blank_category = await CategoriesAPI.get_blank_category_api(telegram_user_id)
        message_text, keyboard = \
            await CategoryDeleteDataProcessing.data_to_text_and_keyboard(response.json(), blank_category, lang)
        return message_text, keyboard


categories_delete_router = Router()


class CategoriesDelete:

    @staticmethod
    async def categories_delete(telegram_user_id: int):
        """
                Функция получает от функции get_hole_list тексты сообщений:
            'о списке' и второе с его содержимым и клавиатуру для удаления позиций списка
        """
        # options = await get_profiles_options_api(telegram_user_id)
        # lang = options["telegram_language"]
        lang = 'en'

        #  Отправка сообщения "Список {list_name}:" с выводом основной клавиатуры:
        del_cat_from = transl[lang]['categories']['delete']['del_cat_from']
        list_name = await get_lists_detail_api(telegram_user_id)
        empty_only = transl[lang]['categories']['delete']['empty_only']
        list_message_text = f"{del_cat_from} \"{list_name}\"\n({empty_only}):"
        main_keyboard = await categories_keyboard_builder()
        await MyBot.bot.send_message(chat_id=telegram_user_id,
                                     text=list_message_text,
                                     reply_markup=main_keyboard,
                                     parse_mode='Markdown')

        text_categories, delete_keyboard = \
            await CategoriesAPI.get_categories_for_current_list_api(telegram_user_id, lang)
        #  Отправка сообщения со списком категорий и inline-клавиатурой для удаления категорий:
        await MyBot.bot.send_message(chat_id=telegram_user_id,
                                     text=text_categories,
                                     reply_markup=delete_keyboard,
                                     parse_mode='Markdown')

    @staticmethod
    @categories_delete_router.message(F.text == emoji['delete'] + emoji['categories'])
    async def categories_delete_start_handler(message: Message):
        """ Handler-функция для вывода списка с клавиатурой для выбора категории для удаления """
        await CategoriesDelete.categories_delete(message.from_user.id)

    @staticmethod
    @categories_delete_router.callback_query(F.data.startswith('del_category'))
    async def categories_delete_handler(callback: CallbackQuery):
        """ Handler-функция парсит inline-запрос, дает команду на удаления категории. """
        telegram_user_id = callback.from_user.id
        category_id, lang = callback.data.split(" ")[1:]
        response = await CategoriesAPI.delete_category_api(telegram_user_id, category_id)
        if response.status_code != 200:
            if response.json()['error'] == 'base_category':
                cat = transl[lang]['categories']['vocabulary']['Category']
                cat_name = response.json()['name']
                is_base_cant_be_delete = transl[lang]['categories']['delete']['is_base_cant_be_delete']
                message_text = f"{cat} *\"{cat_name}\"*\n {is_base_cant_be_delete}"
            elif response.json()['error'] == 'not_empty':
                message_text = transl[lang]['categories']['delete']['can_delete_only_empty']
                # message_text = 'You may delete only empty category.'
            else:
                message_text = response.json()['error']
            await MyBot.bot.send_message(chat_id=telegram_user_id, text=message_text, parse_mode='Markdown')
            await CategoriesDelete.categories_delete(telegram_user_id)
        else:
            cat = transl[lang]['categories']['vocabulary']['Category']
            deleted = transl[lang]['categories']['delete']['deleted']
            message_text = f"{cat} {response.json()['name']} {deleted}"
            await MyBot.bot.send_message(chat_id=telegram_user_id, text=message_text)
            await UpdateCategoryStart.categories_read_for_update(telegram_user_id)
