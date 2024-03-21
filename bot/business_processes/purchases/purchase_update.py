from typing import Dict, Any

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, KeyboardButton, \
    ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder
from requests import Response
from typing_extensions import Tuple

from bot.api.django_auth import django_auth, update_last_request_time
from bot.business_processes.purchases.purchase_delete_and_list_menu import ListRead
from bot.business_processes.purchases.utils.list_menu_keyboard import list_menu_keyboard_buttons
from bot.constants import django_address, buttons_styles
from bot.create_bot import MyBot
from bot.emoji import emoji
from bot.translate import transl

from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __

purchase_update_router = Router()


class PurchaseUpdateStart:

    @staticmethod
    async def data_processing(list_data: list) -> Tuple[str, InlineKeyboardMarkup]:
        message_text = _("Choose position to edit:\n")  # Выберите позицию для редактирования:\n
        number = 1
        builder = InlineKeyboardBuilder()
        for category_dict in list_data:
            category_name = category_dict["name"]
            category_description = category_dict.get('description', '')
            purchases_list = category_dict["purchases"]
            if purchases_list:
                message_text += f"____{category_name}"
                if category_description != '' and category_description is not None:
                    message_text += f"({category_description})\n"
                else:
                    message_text += "\n"
                for purchase_dict in purchases_list:
                    message_text += f"{number}. {purchase_dict['name']}"
                    purchase_description = purchase_dict.get('description', '')
                    if purchase_description != '' and purchase_description is not None:
                        message_text += f" ({purchase_description})\n"
                    else:
                        message_text += "\n"
                    builder.add(InlineKeyboardButton(text=f"{number}",
                                                     callback_data=f"purchase_update {purchase_dict['id']}"))
                    number += 1
        if message_text == "":
            message_text = _("List (group) is steel empty")
        builder.add(InlineKeyboardButton(text=_("Cancel"), callback_data=f"purchase_update stop"))
        keyboard = builder.as_markup(resize_keyboard=True)
        return message_text, keyboard

    @staticmethod
    @update_last_request_time(django_auth)
    async def get_list_api(telegram_user_id):
        url = f"{django_address}/lists/list_or_group/"
        data = {"telegram_user_id": telegram_user_id}
        response = django_auth.session.get(url=url, data=data)
        message_text, keyboard = await PurchaseUpdateStart.data_processing(response.json())
        return message_text, keyboard

    @staticmethod
    @purchase_update_router.message(
        lambda message:
        any(message.text == list_menu_keyboard_buttons(lang)[button_style]['edit']
            for lang in transl.keys() for button_style in buttons_styles)
    )
    async def categories_read_for_update_handler(message: Message):
        telegram_user_id = message.from_user.id
        message_text, keyboard = await PurchaseUpdateStart.get_list_api(telegram_user_id)
        await MyBot.bot.send_message(chat_id=telegram_user_id, text=message_text, reply_markup=keyboard)


class StatesPurchaseUpdate(StatesGroup):
    name = State()
    description = State()


class PurchaseUpdateFMS:

    @staticmethod
    @update_last_request_time(django_auth)
    async def get_purchase_api(telegram_user_id, purchase_id) -> Dict[str, Any]:
        url = f"{django_address}/purchases/detail/"
        data = {
            "telegram_user_id": telegram_user_id,
            "purchase_id": purchase_id
        }
        response = django_auth.session.get(url=url, data=data)
        return response.json()

    @staticmethod
    @purchase_update_router.callback_query(lambda c: c.data and c.data.startswith('purchase_update'))
    async def choose_purchase_for_update_handler(callback: CallbackQuery, state: FSMContext):
        telegram_user_id = callback.from_user.id
        await state.set_state(StatesPurchaseUpdate.name)

        kb = [[KeyboardButton(text=_("No changes")), KeyboardButton(text=emoji['edit'] + _("Cancel"))]]
        stop_same_kb = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

        purchase_id = callback.data.split(" ")[1]
        if purchase_id == "stop":
            await MyBot.bot.send_message(chat_id=telegram_user_id, text=_("OK"))
            await ListRead.get_current_lists_purchases_list(telegram_user_id)
        else:
            purchase_data = await PurchaseUpdateFMS.get_purchase_api(telegram_user_id, purchase_id)
            purchase_ald_name = purchase_data.get('name')
            purchase_ald_description = purchase_data.get('description', "")
            if purchase_ald_description is None:
                purchase_ald_description = ""

            await state.update_data(purchase_id=purchase_id,
                                    purchase_ald_name=purchase_ald_name,
                                    purchase_ald_description=purchase_ald_description)

            await MyBot.bot.send_message(chat_id=telegram_user_id,
                                         text=_("Input new name for new list position"),
                                         reply_markup=stop_same_kb)

            await MyBot.bot.send_message(chat_id=telegram_user_id,
                                         text=f"`{purchase_ald_name}`",
                                         parse_mode='MarkdownV2')

    @staticmethod
    @purchase_update_router.message(F.text.replace(emoji['edit'], "") == __("Cancel"))
    async def state_cancel_handler(message: Message, state: FSMContext):
        telegram_user_id = message.from_user.id
        await state.clear()
        await ListRead.get_current_lists_purchases_list(telegram_user_id)

    @staticmethod
    @purchase_update_router.message(StatesPurchaseUpdate.name)
    async def update_purchase_name_handler(message: Message, state: FSMContext):
        kb = [[KeyboardButton(text=_("No changes")),
               KeyboardButton(text=_("Without description")),
               KeyboardButton(text=emoji['edit'] + _("Cancel"))]]
        stop_same_kb = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

        telegram_user_id = message.from_user.id
        data = await state.get_data()
        purchase_ald_description = data.get("purchase_ald_description", "")
        if message.text == _("No changes"):
            await state.update_data(name=data["purchase_ald_name"])
        else:
            await state.update_data(name=message.text)
        await state.set_state(StatesPurchaseUpdate.description)
        await MyBot.bot.send_message(chat_id=telegram_user_id,
                                     text=_("Now input new description"),
                                     reply_markup=stop_same_kb)
        if purchase_ald_description != "":
            await MyBot.bot.send_message(chat_id=telegram_user_id,
                                         text=f"`{purchase_ald_description}`",
                                         parse_mode='MarkdownV2')

    @staticmethod
    @update_last_request_time(django_auth)
    async def purchase_update_api(telegram_user_id: int, data: Dict[str, Any]) -> Response:
        url = f"{django_address}/purchases/detail/"
        data["telegram_user_id"] = telegram_user_id
        response = await django_auth.session.put(url=url, data=data)
        return response

    @staticmethod
    @purchase_update_router.message(StatesPurchaseUpdate.description)
    async def update_category_description_handler(message: Message, state: FSMContext):
        telegram_user_id = message.from_user.id
        purchase_data = await state.get_data()
        if message.text == _("No changes"):
            purchase_data["description"] = purchase_data["purchase_ald_description"]
        elif message.text == _("Without description"):
            purchase_data["description"] = ""
        else:
            purchase_data["description"] = message.text

        await state.clear()
        if (purchase_data['name'] == purchase_data["purchase_ald_name"]
                and purchase_data["description"] == purchase_data["purchase_ald_description"]):
            await MyBot.bot.send_message(chat_id=telegram_user_id,
                                         text=_("Your chose is leave the list position without changes"),
                                         reply_markup=ReplyKeyboardRemove())
            await ListRead.get_current_lists_purchases_list(telegram_user_id)
        else:
            response = await PurchaseUpdateFMS.purchase_update_api(telegram_user_id, purchase_data)
            if response.status_code != 200:
                await MyBot.bot.send_message(chat_id=telegram_user_id, text=_("Somthing went rong"))
            await ListRead.get_current_lists_purchases_list(telegram_user_id)
