from typing import Tuple

from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from requests import Response

from bot.api.django_auth import django_auth, update_last_request_time
from bot.business_processes.lists.utils.lits_details_api import get_lists_detail_api
from bot.create_bot import MyBot
from bot.emoji import emoji

category_purify_router = Router()


class CategoryPurifyStart:

    @staticmethod
    async def categories_data_processing(categories_data: list, message_text) -> Tuple[str, InlineKeyboardMarkup]:
        builder = InlineKeyboardBuilder()
        number = 1
        for category_dict in categories_data:
            message_text += f"{number}. {category_dict['name']}"
            category_description = category_dict.get('description', None)
            if category_description:
                message_text += f" ({category_description})\n"
            else:
                message_text += '\n'

            builder.add(InlineKeyboardButton(text=f"{number}", callback_data=f"purify_category {category_dict['id']}"))
            number += 1
        builder.adjust(6)
        purify_keyboard = builder.as_markup(resize_keyboard=True)
        return message_text, purify_keyboard

    @staticmethod
    @update_last_request_time(django_auth)
    async def categories_for_purifying_api(telegram_user_id: int) -> Tuple[str, InlineKeyboardMarkup]:
        list_name = await get_lists_detail_api(telegram_user_id)
        message_text = "Какую категорию из списка \"{list_name}\" Вы хотите очистить?\n".format(list_name=list_name)
        url = f'{django_address}/categories/'
        data = {"telegram_user_id": telegram_user_id}
        request = django_auth.session.get(url=url, data=data)
        message_text, purify_keyboard = \
            await CategoryPurifyStart.categories_data_processing(request.json(), message_text)
        return message_text, purify_keyboard

    @staticmethod
    async def category_purify_start(telegram_user_id: int):
        message_text, purify_keyboard = await CategoryPurifyStart.categories_for_purifying_api(telegram_user_id)
        await MyBot.bot.send_message(chat_id=telegram_user_id, text=message_text, reply_markup=purify_keyboard)

    @staticmethod
    @category_purify_router.message(F.text == emoji['clean'] + emoji['categories'])
    async def category_purify_start_handler(message: Message):
        telegram_user_id = message.from_user.id
        await CategoryPurifyStart.category_purify_start(telegram_user_id)


class CategoryPurifyDecision:

    @staticmethod
    async def category_data_processing(category_data: dict) -> Tuple[str, InlineKeyboardMarkup]:
        message_text = (f"Вы уверены, что хотите удалить позиции категории?\n"
                        f"____{category_data['name']}\n")
        number = 1
        for purchase in category_data['purchases']:
            message_text += f"{number}. {purchase['name']}"
            if purchase['description']:
                message_text += f" ({purchase['description']})\n"
            else:
                message_text += '\n'

        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="Да, я хочу удалить позиции этой категории!",
                                         callback_data=f"category_purify_decision OK {category_data['id']}"))
        builder.add(InlineKeyboardButton(text="Нет, я передумал удалять позиции категории!",
                                         callback_data=f"category_purify_decision Cancel {category_data['id']}"))
        builder.adjust(1)
        purify_decision_keyboard = builder.as_markup(resize_keyboard=True)
        return message_text, purify_decision_keyboard

    @staticmethod
    @update_last_request_time(django_auth)
    async def category_purify_content_api(telegram_user_id: int, category_id: int) -> Tuple[str, InlineKeyboardMarkup]:
        url = f'{django_address}/categories/get_one/'
        data = {
            "telegram_user_id": telegram_user_id,
            "category_id": category_id
        }
        response = django_auth.session.get(url=url, data=data)
        message_text, decision_keyboard = await CategoryPurifyDecision.category_data_processing(response.json())
        return message_text, decision_keyboard

    @staticmethod
    @category_purify_router.callback_query(lambda c: c.data and c.data.startswith("purify_category"))
    async def category_purify_decision_handler(callback: CallbackQuery):
        telegram_user_id = callback.from_user.id
        category_id = int(callback.data.split(' ')[1])
        message_text, decision_keyboard = \
            await CategoryPurifyDecision.category_purify_content_api(telegram_user_id, category_id)
        await MyBot.bot.send_message(chat_id=telegram_user_id, text=message_text, reply_markup=decision_keyboard)


class CategoryPurify:
    """

    """  # TODO: Documentation.

    @staticmethod
    @update_last_request_time(django_auth)
    async def category_purify_api(telegram_user_id: int, category_id: int) -> Response:
        url = f'{django_address}/categories/purify/'
        data = {
            "telegram_user_id": telegram_user_id,
            'category_id': category_id
        }
        response = await django_auth.session.put(url=url, data=data)
        return response

    @staticmethod
    @category_purify_router.callback_query(lambda c: c.data and c.data.startswith('category_purify_decision'))
    async def category_purify_handler(callback: CallbackQuery):
        telegram_user_id = callback.from_user.id
        decision, category_id = callback.data.split(' ')[1:]

        if decision == "Cancel":
            text = "OK"
            await MyBot.bot.send_message(chat_id=telegram_user_id, text=text)

        else:
            response = await CategoryPurify.category_purify_api(telegram_user_id, category_id)

            if response.status_code == 404:
                text = response.json()['error']
                await MyBot.bot.send_message(chat_id=telegram_user_id, text=text)

            elif response.status_code != 200:
                text = "Что-то пошло не так..."
                await MyBot.bot.send_message(chat_id=telegram_user_id, text=text)

        await CategoryPurifyStart.category_purify_start(telegram_user_id)