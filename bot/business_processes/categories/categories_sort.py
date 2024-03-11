from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from requests import Response

from bot.api.django_auth import django_auth, update_last_request_time
from bot.business_processes.categories.category_update import UpdateCategoryStart
from bot.business_processes.categories.utils.categories_menu_keyboard import categories_menu_keyboard_buttons
from bot.business_processes.options.utils.get_profiles_options_api import get_profiles_options_api
from bot.constants import django_address, buttons_styles
from bot.create_bot import MyBot
from bot.emoji import emoji
from bot.translate import transl

categories_sort_router = Router()


class CategoriesSortStart:

    @staticmethod
    async def categories_sort_data_processing(categories_data: list, lang: str) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        # First category button:
        first_category = categories_data.pop(0)
        description = first_category.get('description', None)

        text = f"{first_category['name']}"
        if description:
            text += f" ({description}) ⬇"
        else:
            text += ' ⬇'
        builder.row(
            InlineKeyboardButton(text=text, callback_data=f"categories_sort {first_category['id']} down {lang}")
        )

        # Get last category:
        last_category = categories_data.pop()

        # Ather categories buttons:
        for category in categories_data:

            description = category.get('description', None)
            text = f"⬆ {category['name']}"
            if description:
                text += f" ({description})"

            builder.row(
                InlineKeyboardButton(text=text, callback_data=f"categories_sort {category['id']} up {lang}"),
                InlineKeyboardButton(text="⬇", callback_data=f"categories_sort {category['id']} down {lang}"),
            )

        # Last category button:
        description = last_category.get('description', None)
        text = f"⬆ {last_category['name']}"
        if description:
            text += f" ({description})"
        builder.row(InlineKeyboardButton(text=text, callback_data=f"categories_sort {last_category['id']} up {lang}"))

        sort_keyboard = builder.as_markup()
        return sort_keyboard

    @staticmethod
    @update_last_request_time(django_auth)
    async def categories_sort_api(telegram_user_id: int, lang: str) -> InlineKeyboardMarkup | bool:
        url = f'{django_address}/categories/'
        data = {"telegram_user_id": telegram_user_id}
        response = django_auth.session.get(url=url, data=data)
        if len(response.json()) > 1:
            sort_keyboard = await CategoriesSortStart.categories_sort_data_processing(response.json(), lang)
            return sort_keyboard
        else:
            return False

    @staticmethod
    @categories_sort_router.message(
        lambda message:
        any(message.text == categories_menu_keyboard_buttons(lang)[button_style]['sort']
            for lang in transl.keys() for button_style in buttons_styles)
    )
    async def categories_sort_handler(message: Message):
        telegram_user_id = message.from_user.id
        # options = await get_profiles_options_api(telegram_user_id)
        # lang = options['telegram_language']
        lang = 'en'
        categories_text = transl[lang]['categories']['sort']['choose_move']
        # categories_text = 'Select actions to modify categorization:'
        sort_keyboard = await CategoriesSortStart.categories_sort_api(telegram_user_id, lang)
        if sort_keyboard:
            await MyBot.bot.send_message(chat_id=telegram_user_id, text=categories_text, reply_markup=sort_keyboard)
        else:
            message_text = transl[lang]['categories']['sort']['not_enough']
            # message_text = 'Too few categories to sort.'
            await MyBot.bot.send_message(chat_id=telegram_user_id, text=message_text)
            await UpdateCategoryStart.categories_read_for_update(telegram_user_id)


class CategoriesSortMove:

    @staticmethod
    @update_last_request_time(django_auth)
    async def categories_sort_move_api(telegram_user_id: int, category_id: int, move: str) -> Response:
        url = f'{django_address}/categories/sort/'
        data = {
            "telegram_user_id": telegram_user_id,
            "category_id": category_id,
            "move": move
        }
        response = await django_auth.session.put(url=url, data=data)
        return response

    @staticmethod
    @categories_sort_router.callback_query(lambda c: c.data and c.data.startswith("categories_sort"))
    async def categories_sort_callback_handler(callback: CallbackQuery):
        telegram_user_id = callback.from_user.id
        message_id = callback.message.message_id
        category_id, move, lang = callback.data.split(' ')[1:]
        response = await CategoriesSortMove.categories_sort_move_api(telegram_user_id, category_id, move)
        if response.status_code != 200:
            trouble_message = transl[lang]['errors']['smt_rong']
            # trouble_message = "Something went wrong"
            await MyBot.bot.send_message(chat_id=telegram_user_id, text=trouble_message)
            await UpdateCategoryStart.categories_read_for_update(telegram_user_id)
        else:
            sort_keyboard = await CategoriesSortStart.categories_sort_api(telegram_user_id)
            await MyBot.bot.edit_message_reply_markup(chat_id=telegram_user_id,
                                                      message_id=message_id,
                                                      reply_markup=sort_keyboard)
