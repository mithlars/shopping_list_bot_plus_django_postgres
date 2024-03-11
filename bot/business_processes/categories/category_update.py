import copy
from typing import Any, Dict, Tuple

from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from requests import Response

from bot.business_processes.categories.utils.categories_menu_keyboard import categories_menu_keyboard_builder, \
    categories_menu_keyboard_buttons
from bot.business_processes.lists.utils.lits_details_api import get_lists_detail_api
from bot.business_processes.purchases.utils.list_menu_keyboard import list_menu_keyboard_buttons
from bot.constants import django_address, buttons_styles
from bot.create_bot import MyBot

from bot.api.django_auth import update_last_request_time, django_auth
from bot.translate import transl

category_update_router = Router()


class UpdateCategoryStart:

    @staticmethod
    async def categories_data_processing(list_of_categories: list) -> Tuple[str, InlineKeyboardMarkup]:
        message_text = "Выберите категорию для редактирования:\n"
        number = 1
        builder = InlineKeyboardBuilder()
        for category_dict in list_of_categories:
            message_text += f"{number}. {category_dict['name']}"
            if category_dict['description'] != '' and category_dict['description'] is not None:
                message_text += f" ({category_dict['description']}).\n"
            else:
                message_text += "\n"

            builder.add(InlineKeyboardButton(text=f"{number}", callback_data=f"category_update {category_dict['id']}"))
            number += 1
        builder.adjust(6)
        keyboard = builder.as_markup(resize_keyboard=True)
        return message_text, keyboard

    @staticmethod
    @update_last_request_time(django_auth)
    async def categories_read_for_update_api(telegram_user_id: int) -> Tuple[str, InlineKeyboardMarkup]:
        url = f"{django_address}/categories/"
        data = {"telegram_user_id": telegram_user_id}
        response = django_auth.session.get(url=url, data=data)
        message_text, keyboard = await UpdateCategoryStart.categories_data_processing(response.json())
        return message_text, keyboard

    @staticmethod
    async def categories_read_for_update(telegram_user_id: int):
        keyboard = await categories_menu_keyboard_builder(telegram_user_id)
        list_name = await get_lists_detail_api(telegram_user_id)
        list_message_text = f"""Категории списка \n*"{list_name}"*:"""
        await MyBot.bot.send_message(chat_id=telegram_user_id, text=list_message_text,
                                     reply_markup=keyboard, parse_mode='Markdown')

        message_text, keyboard = await UpdateCategoryStart.categories_read_for_update_api(telegram_user_id)
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

    kb = [[KeyboardButton(text="Без изменений"), KeyboardButton(text="✏️🗂️Отмена")]]
    stop_same_kb = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    @staticmethod
    @category_update_router.callback_query(lambda c: c.data and c.data.startswith('category_update'))
    async def choose_category_for_update_handler(callback: CallbackQuery, state: FSMContext):
        telegram_user_id = callback.from_user.id
        await state.set_state(StatesUpdateCategory.name)

        category_id = callback.data.split(" ")[1]
        category_data = await UpdateCategoryFMS.get_category_api(telegram_user_id, category_id)
        category_ald_name = category_data.get('name')
        category_ald_description = category_data.get('description', '')
        await state.update_data(category_id=category_id,
                                category_ald_name=category_ald_name,
                                category_ald_description=category_ald_description)

        await MyBot.bot.send_message(chat_id=telegram_user_id,
                                     text='Введите новое имя для категории',
                                     reply_markup=UpdateCategoryFMS.stop_same_kb)

        await MyBot.bot.send_message(chat_id=telegram_user_id,
                                     text=f"`{category_ald_name}`",
                                     parse_mode='MarkdownV2')

    @staticmethod
    @category_update_router.message(F.text == '✏️🗂️Отмена')
    async def state_cancel_handler(message: Message, state: FSMContext):
        telegram_user_id = message.from_user.id
        await state.clear()
        await UpdateCategoryStart.categories_read_for_update(telegram_user_id)
        # await CategoriesRead.categories_read_and_menu(telegram_user_id)

    @staticmethod
    @category_update_router.message(StatesUpdateCategory.name)
    async def update_category_name_handler(message: Message, state: FSMContext):
        if message.text == "Без изменений":
            data = await state.get_data()
            await state.update_data(name=data["category_ald_name"])
        else:
            await state.update_data(name=message.text)
        await state.set_state(StatesUpdateCategory.description)
        kb = copy.deepcopy(UpdateCategoryFMS.kb)
        kb[0].append(KeyboardButton(text="Без описания"))
        stop_same_kb = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        await MyBot.bot.send_message(chat_id=message.chat.id,
                                     text="Теперь введите новое описание",
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
        category_data = await state.get_data()
        if message.text == "Без изменений":
            category_data["description"] = category_data["category_ald_description"]
        elif message.text == "Без описания":
            category_data["description"] = ""
        else:
            category_data["description"] = message.text
        await state.clear()
        if (category_data['name'] == category_data["category_ald_name"]
                and category_data["description"] == category_data["category_ald_description"]):
            await MyBot.bot.send_message(chat_id=telegram_user_id,
                                         text="Вы решили оставить данные категории без изменений.",
                                         reply_markup=ReplyKeyboardRemove())
            await UpdateCategoryStart.categories_read_for_update(telegram_user_id)
            # await CategoriesRead.categories_read_and_menu(telegram_user_id)
        else:
            response = await UpdateCategoryFMS.category_update_api(telegram_user_id, category_data)
            if response.status_code != 200:
                await MyBot.bot.send_message(chat_id=telegram_user_id, text="Что-то пошло не так")
            await UpdateCategoryStart.categories_read_for_update(telegram_user_id)
            # await CategoriesRead.categories_read_and_menu(telegram_user_id)
