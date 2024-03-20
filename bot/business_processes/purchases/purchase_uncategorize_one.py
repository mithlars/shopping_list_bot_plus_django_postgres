from typing import Tuple

from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from requests import Response

from bot.api.django_auth import django_auth, update_last_request_time
from bot.business_processes.purchases.purchases_delete_and_list_menu import ListRead
from bot.business_processes.purchases.utils.list_menu_keyboard import list_menu_keyboard_buttons
from bot.constants import django_address, buttons_styles
from bot.create_bot import MyBot
from bot.translate import transl

from aiogram.utils.i18n import gettext as _

purchase_uncategorize_one_router = Router()


class PurchaseUncategorizeOneStart:

    @staticmethod
    async def data_processing(list_data: list, blank_category_id: int) -> Tuple[str, InlineKeyboardMarkup]:
        message_text = ""
        number_count = 1
        builder = InlineKeyboardBuilder()
        for category_dict in list_data:
            if category_dict['id'] != blank_category_id:
                category_name = category_dict["name"]
                purchases_list = category_dict["purchases"]
                if purchases_list:
                    message_text += f"____{category_name}\n"
                    for purchase_dict in purchases_list:
                        message_text += f"{number_count}. {purchase_dict['name']}"
                        purchase_description = purchase_dict.get('description', '')
                        if purchase_description != '' and purchase_description is not None:
                            message_text += f" ({purchase_description})\n"
                        else:
                            message_text += "\n"
                        callback_data = f"uncategorize_purchase {purchase_dict['id']} {category_dict['id']}"
                        builder.add(InlineKeyboardButton(text=f"{number_count}", callback_data=callback_data))
                        number_count += 1
        if message_text == "":
            message_text = _("List (group) is steel empty")
        builder.add(InlineKeyboardButton(text=_("Cancel"),
                                         callback_data=f"uncategorize_purchase stop stop"))
        keyboard = builder.as_markup(resize_keyboard=True)
        return message_text, keyboard

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
    async def get_purchase_choice_text_and_keyboard_api(telegram_user_id: int) -> Tuple[str, InlineKeyboardMarkup]:
        url = f"{django_address}/lists/list_or_group/"  # TODO: Что делать, если в группе нет blank-категории?
        data = {"telegram_user_id": telegram_user_id}
        response = django_auth.session.get(url=url, data=data)
        blank_category_id = await PurchaseUncategorizeOneStart.get_blank_category_api(telegram_user_id)
        message_text, keyboard = await PurchaseUncategorizeOneStart.data_processing(response.json(), blank_category_id)
        return message_text, keyboard

    @staticmethod
    async def uncategorize_choice(telegram_user_id: int):
        """
                Method is getting text with purchases and inline-keyboard to choose purchase for changing category for.
            and sending message to user with this text and keyboard
        """
        message_text, keyboard = await (PurchaseUncategorizeOneStart.
                                        get_purchase_choice_text_and_keyboard_api(telegram_user_id))
        await MyBot.bot.send_message(chat_id=telegram_user_id, text=message_text, reply_markup=keyboard)

    @staticmethod
    @purchase_uncategorize_one_router.message(
        lambda message:
        any(message.text == list_menu_keyboard_buttons(lang)[button_style]['from_category']
            for lang in transl.keys() for button_style in buttons_styles)
        )
    async def categorize_one_start_handler(message: Message):
        telegram_user_id = message.from_user.id
        await PurchaseUncategorizeOneStart.uncategorize_choice(telegram_user_id)


class PurchaseUncategorize:
    @staticmethod
    @update_last_request_time(django_auth)
    async def get_purchases_categories_api(telegram_user_id: int, purchase_id: str) -> list:
        url = f"{django_address}/purchases/categories/"  # TODO: url
        data = {
            "telegram_user_id": telegram_user_id,
            "purchase_id": purchase_id
        }
        response = django_auth.session.get(url=url, data=data)
        return response.json()['categories_ids']

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
    async def uncategorize_api(telegram_user_id: int, purchase_id: str, category_from_id: str) -> Response:
        url = f"{django_address}/categories/purchases_update/"
        data = {
            "telegram_user_id": telegram_user_id,
            "purchase_id": purchase_id,
            "category_from_id": category_from_id
        }
        purchases_categories_list = await (
            PurchaseUncategorize.get_purchases_categories_api(telegram_user_id, purchase_id))
        blank_category_id = await PurchaseUncategorize.get_blank_category_api(telegram_user_id)
        if len(purchases_categories_list) == 1:
            data["category_to_id"] = blank_category_id
        response = await django_auth.session.put(url=url, data=data)
        return response

    @staticmethod
    @purchase_uncategorize_one_router.callback_query(lambda c: c.data and c.data.startswith("uncategorize_purchase"))
    async def choose_category_handler(callback: CallbackQuery):
        telegram_user_id = callback.from_user.id
        purchase_id, category_from_id = callback.data.split(" ")[1:]
        if purchase_id == "stop":
            await MyBot.bot.send_message(chat_id=telegram_user_id, text=_("OK"))
            await ListRead.get_current_lists_purchases_list(telegram_user_id)
        else:
            response = await PurchaseUncategorize.uncategorize_api( telegram_user_id, purchase_id, category_from_id)
            if response.status_code != 200:
                await MyBot.bot.send_message(chat_id=telegram_user_id, text=_("Somthing went rong"))
            await ListRead.get_current_lists_purchases_list(telegram_user_id)
