import copy
from typing import Any, Dict, Tuple

from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    KeyboardButton, ReplyKeyboardMarkup
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from requests import Response

from bot.business_processes.categories.utils.categories_menu_keyboard import categories_menu_keyboard_builder, \
    categories_menu_keyboard_buttons
from bot.business_processes.lists.utils.lits_details_api import get_lists_detail_api
from bot.business_processes.options.utils.get_profiles_options_api import get_profiles_options_api
from bot.business_processes.purchases.utils.list_menu_keyboard import list_menu_keyboard_buttons
from bot.constants import django_address, buttons_styles
from bot.create_bot import MyBot

from bot.api.django_auth import update_last_request_time, django_auth
from bot.emoji import emoji
from bot.translate import transl

category_update_router = Router()


class UpdateCategoryStart:

    @staticmethod
    async def categories_data_processing(list_of_categories: list, lang: str) -> Tuple[str, InlineKeyboardMarkup]:
        update_tr = transl[lang]['categories']['update']
        message_text = f"{update_tr['choose_cat_for_update']}\n"
        number = 1
        builder = InlineKeyboardBuilder()
        for category_dict in list_of_categories:
            message_text += f"{number}. {category_dict['name']}"
            if category_dict['description'] != '' and category_dict['description'] is not None:
                message_text += f" ({category_dict['description']}).\n"
            else:
                message_text += "\n"

            builder.add(InlineKeyboardButton(text=f"{number}",
                                             callback_data=f"category_update {category_dict['id']} {lang}"))
            number += 1
        builder.adjust(6)
        keyboard = builder.as_markup(resize_keyboard=True)
        return message_text, keyboard

    @staticmethod
    @update_last_request_time(django_auth)
    async def categories_read_for_update_api(telegram_user_id: int, lang: str) -> Tuple[str, InlineKeyboardMarkup]:
        url = f"{django_address}/categories/"
        data = {"telegram_user_id": telegram_user_id}
        response = django_auth.session.get(url=url, data=data)
        message_text, keyboard = await UpdateCategoryStart.categories_data_processing(response.json(), lang)
        return message_text, keyboard

    @staticmethod
    async def categories_read_for_update(telegram_user_id: int):
        options = await get_profiles_options_api(telegram_user_id)
        lang = options["telegram_language"]
        keyboard = await categories_menu_keyboard_builder(telegram_user_id)
        list_name = await get_lists_detail_api(telegram_user_id)
        list_message_text = f"""Категории списка \n*"{list_name}"*:"""
        await MyBot.bot.send_message(chat_id=telegram_user_id, text=list_message_text,
                                     reply_markup=keyboard, parse_mode='Markdown')

        message_text, keyboard = await UpdateCategoryStart.categories_read_for_update_api(telegram_user_id, lang)
        await MyBot.bot.send_message(chat_id=telegram_user_id, text=message_text, reply_markup=keyboard)

    @staticmethod
    @category_update_router.message(
        lambda message:
        any(message.text == list_menu_keyboard_buttons(lang)[button_style]['categories']
            for lang in transl.keys() for button_style in buttons_styles)
        or any(message.text == categories_menu_keyboard_buttons(lang)[button_style]['edit']
               for lang in transl.keys() for button_style in buttons_styles)
    )
    async def categories_read_for_update_handler(message: Message):
        telegram_user_id = message.from_user.id
        await UpdateCategoryStart.categories_read_for_update(telegram_user_id)


class StatesUpdateCategory(StatesGroup):
    name = State()
    description = State()


class UpdateCategoryFMS:

    @staticmethod
    @update_last_request_time(django_auth)
    async def get_category_api(telegram_user_id: int, category_id: str) -> Dict[str, Any]:
        url = f"{django_address}/categories/get_one/"
        data = {
            "telegram_user_id": telegram_user_id,
            "category_id": category_id
        }
        response = django_auth.session.get(url=url, data=data)
        return response.json()

    @staticmethod
    async def get_stop_keyboard(lang: str, description: bool = False) -> ReplyKeyboardMarkup:
        cancel = transl[lang]['buttons']['cancel']
        no_chngs = transl[lang]['buttons']['no_chngs']
        kb = [[KeyboardButton(text=no_chngs), KeyboardButton(text=f"{emoji['edit']}{emoji['categories']}{cancel}")]]
        if description:
            no_descr = transl[lang]['buttons']['no_descr']
            kb[0].append(KeyboardButton(text=no_descr))
        return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    @staticmethod
    @category_update_router.callback_query(lambda c: c.data and c.data.startswith('category_update'))
    async def choose_category_for_update_handler(callback: CallbackQuery, state: FSMContext):
        telegram_user_id = callback.from_user.id
        await state.set_state(StatesUpdateCategory.name)

        category_id, lang = callback.data.split(" ")[1:]
        update_tr = transl[lang]['categories']['update']
        category_data = await UpdateCategoryFMS.get_category_api(telegram_user_id, category_id)
        category_ald_name = category_data.get('name')
        category_ald_description = category_data.get('description', '')
        await state.update_data(category_id=category_id,
                                category_ald_name=category_ald_name,
                                category_ald_description=category_ald_description,
                                lang=lang)

        await MyBot.bot.send_message(chat_id=telegram_user_id,
                                     text=update_tr['input_new_cat_name'],
                                     reply_markup=await UpdateCategoryFMS.get_stop_keyboard(lang))

        await MyBot.bot.send_message(chat_id=telegram_user_id,
                                     text=f"`{category_ald_name}`",
                                     parse_mode='MarkdownV2')

    @staticmethod
    @category_update_router.message(
        lambda message:
        any(message.text == f"{emoji['edit']}{emoji['categories']}{transl[lang]['buttons']['cancel']}"
            for lang in transl.keys())
    )
    async def state_cancel_handler(message: Message, state: FSMContext):
        telegram_user_id = message.from_user.id
        await state.clear()
        await UpdateCategoryStart.categories_read_for_update(telegram_user_id)

    @staticmethod
    @category_update_router.message(StatesUpdateCategory.name)
    async def update_category_name_handler(message: Message, state: FSMContext):
        data = await state.get_data()
        lang = data['lang']
        update_tr = transl[lang]['categories']['update']
        if message.text == any(transl[language]['buttons']['no_chngs'] for language in transl.keys()):
            await state.update_data(name=data["category_ald_name"])
        else:
            await state.update_data(name=message.text)
        await state.set_state(StatesUpdateCategory.description)
        stop_same_kb = UpdateCategoryFMS.get_stop_keyboard(lang, description=True)
        await MyBot.bot.send_message(chat_id=message.chat.id,
                                     text=update_tr['input_new_cat_descr'],
                                     reply_markup=stop_same_kb)

    @staticmethod
    @update_last_request_time(django_auth)
    async def category_update_api(telegram_user_id: int, data: Dict[str, Any]) -> Response:
        url = f"{django_address}/categories/update/"
        data["telegram_user_id"] = telegram_user_id
        response = await django_auth.session.put(url=url, data=data)
        return response

    @staticmethod
    @category_update_router.message(StatesUpdateCategory.description)
    async def update_category_description_handler(message: Message, state: FSMContext):
        telegram_user_id = message.from_user.id
        options = await get_profiles_options_api(telegram_user_id)
        lang = options["telegram_language"]
        update_tr = transl[lang]['categories']['update']
        errors = transl[lang]['errors']
        category_data = await state.get_data()
        if message.text == any(transl[any_lang]['buttons']['no_chngs'] for any_lang in transl.keys()):
            category_data["description"] = category_data["category_ald_description"]
        elif message.text == any(transl[any_lang]['buttons']['no_descr'] for any_lang in transl.keys()):
            category_data["description"] = ""
        else:
            category_data["description"] = message.text
        await state.clear()
        if (category_data['name'] == category_data["category_ald_name"]
                and category_data["description"] == category_data["category_ald_description"]):
            await MyBot.bot.send_message(chat_id=telegram_user_id,
                                         text=update_tr['your_chs_no_chngs'],
                                         reply_markup=ReplyKeyboardRemove())
            await UpdateCategoryStart.categories_read_for_update(telegram_user_id)
        else:
            response = await UpdateCategoryFMS.category_update_api(telegram_user_id, category_data)
            if response.status_code != 200:
                await MyBot.bot.send_message(chat_id=telegram_user_id, text=errors['smt_rong'])
            await UpdateCategoryStart.categories_read_for_update(telegram_user_id)
