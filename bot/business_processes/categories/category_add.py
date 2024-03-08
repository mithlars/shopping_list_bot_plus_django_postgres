from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from bot.business_processes.categories.category_update import UpdateCategoryStart
from bot.business_processes.options.utils.get_profiles_options_api import get_profiles_options_api
from bot.constants import django_address
from bot.create_bot import MyBot
from bot.api.django_auth import update_last_request_time, django_auth
from bot.emoji import emoji
from bot.translate import transl


# from bot.business_processes.categories.utils.categories_menu_keyboard import CategoriesRead


class CategoryAddAPI:

    @staticmethod
    async def get_next_order_number_api(telegram_user_id: int) -> int:
        url = f"{django_address}/categories/get_order_number/"
        data = {"telegram_user_id": telegram_user_id}
        request = django_auth.session.get(url=url, data=data)
        return request.json()['order_number']

    @staticmethod
    @update_last_request_time(django_auth)
    async def add_new_category_api(
            telegram_user_id: int,
            new_category_name: str,
            new_category_description: str,
            order_number: int
    ) -> str:
        """Create new category"""

        url = f"{django_address}/categories/add/"
        data = {
            "telegram_user_id": telegram_user_id,
            "name": new_category_name,
            "description": new_category_description,
            "order_number": order_number
        }
        request = await django_auth.session.post(url=url, data=data)
        return request.status_code


class StatesNewCategory(StatesGroup):
    name = State()
    description = State()


category_add_router = Router()


class CategoryAddHandler:

    @staticmethod
    @category_add_router.message(F.text == emoji['add'] + emoji['categories'])
    async def add_new_category_handler(message: Message, state: FSMContext):
        telegram_user_id = message.chat.id
        # options = await get_profiles_options_api(telegram_user_id)
        # lang = options["telegram_language"]
        lang = 'en'
        cancel = transl[lang]['buttons']['cancel']
        # cancel = 'Cancel'
        cancel_button = emoji['add'] + emoji['categories'] + cancel
        kb = [[KeyboardButton(text=cancel_button)]]
        stop_kb = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        await state.set_state(StatesNewCategory.name)
        input_name = transl[lang]['categories']['add']['input_name']
        # input_name = 'Add new category name'
        await MyBot.bot.send_message(chat_id=telegram_user_id, text=input_name, reply_markup=stop_kb)

    @staticmethod
    # @category_add_router.message(
    #     lambda message: any(
    #         f"{emoji['add']}{emoji['categories']}{transl[lang]['buttons']['cancel']}"
    #         == message.text for lang in transl.keys()
    #     )
    # )  # TODO: Переделать: transl['en']
    @category_add_router.message(F.text == f"{emoji['add']}{emoji['categories']}{transl['en']['buttons']['cancel']}")
    async def state_cancel_handler(message: Message, state: FSMContext):
        telegram_user_id = message.from_user.id
        await state.clear()
        await UpdateCategoryStart.categories_read_for_update(telegram_user_id)

    @staticmethod
    @category_add_router.message(StatesNewCategory.name)
    async def add_name_for_new_category_handler(message: Message, state: FSMContext):
        telegram_user_id = message.chat.id
        # options = await get_profiles_options_api(telegram_user_id)
        # lang = options["telegram_language"]
        lang = 'en'
        cancel_button = emoji['add'] + emoji['categories'] + transl[lang]['buttons']['cancel']
        no_descr_button = transl[lang]['buttons']['no_description']
        kb = [[KeyboardButton(text=no_descr_button), KeyboardButton(text=cancel_button)]]
        stop_kb = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        await state.update_data(name=message.text, description="")
        await state.set_state(StatesNewCategory.description)
        input_description = transl[lang]['add']['input_description']
        await MyBot.bot.send_message(chat_id=telegram_user_id, text=input_description, reply_markup=stop_kb)

    @staticmethod
    @category_add_router.message(StatesNewCategory.description)
    async def add_description_for_new_category_handler(message: Message, state: FSMContext):
        telegram_user_id = message.from_user.id
        # options = await get_profiles_options_api(telegram_user_id)
        # lang = options["telegram_language"]
        lang = 'en'
        no_description = transl[lang]['buttons']['no_description']
        if message.text != no_description:
            await state.update_data(description=message.text)
        new_category_data = await state.get_data()
        await state.clear()
        order_number = await CategoryAddAPI.get_next_order_number_api(telegram_user_id)
        status = await CategoryAddAPI.add_new_category_api(
            telegram_user_id,
            new_category_data['name'],
            new_category_data['description'],
            order_number
        )
        if status == 201:
            categories = transl[lang]['categories']['add']
            new_category = categories['new']
            created = categories['created']
            description = categories['description']
            message_text = (f"{new_category} *\"{new_category_data['name']}\"* {created}.\n"
                            f"{description}: *\"{new_category_data['description']}\"*\n")
        else:
            message_text = transl[lang]['errors']['smt_rong']
        await MyBot.bot.send_message(chat_id=telegram_user_id,
                                     text=message_text,
                                     reply_markup=ReplyKeyboardRemove(),
                                     parse_mode='Markdown')
        #  Чтение списка категорий:
        await UpdateCategoryStart.categories_read_for_update(telegram_user_id)
        # await CategoriesRead.categories_read_and_menu(telegram_user_id)
