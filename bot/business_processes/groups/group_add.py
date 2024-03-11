from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from bot.business_processes.groups.group_change_current import GroupChangeCurrentStart
from bot.business_processes.groups.utils.groups_menu_keyboard import groups_menu_keyboard_buttons
from bot.constants import django_address, buttons_styles
from bot.create_bot import MyBot
from bot.api.django_auth import update_last_request_time, django_auth
from bot.translate import transl


# from bot.business_processes.groups.utils.groups_menu_keyboard import GroupsRead


class GroupAddAPI:

    @staticmethod
    async def get_next_order_number_api(telegram_user_id: int) -> int:
        url = f"{django_address}/groups/get_order_number/"
        data = {"telegram_user_id": telegram_user_id}
        request = django_auth.session.get(url=url, data=data)
        order_number = request.json()['order_number']
        return order_number

    @staticmethod
    @update_last_request_time(django_auth)
    async def add_new_group_api(
            telegram_user_id: int,
            new_group_name: str,
            new_group_description: str,
            order_number: int
    ) -> str:
        """Create new category"""

        url = f"{django_address}/groups/add/"
        data = {
            "telegram_user_id": telegram_user_id,
            "name": new_group_name,
            "description": new_group_description,
            "order_number": order_number
        }
        request = await django_auth.session.post(url=url, data=data)
        return request.status_code


class NewGroupState(StatesGroup):
    name = State()
    description = State()


group_add_router = Router()


class GroupAdd:

    @staticmethod
    @group_add_router.message(
        lambda message:
        any(message.text == groups_menu_keyboard_buttons(lang)[button_style]['add']
            for lang in transl.keys() for button_style in buttons_styles)
    )
    async def add_new_group_handler(message: Message, state: FSMContext):
        kb = [[KeyboardButton(text="➕🗃️Отмена")]]
        stop_kb = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        await state.set_state(NewGroupState.name)
        await MyBot.bot.send_message(message.chat.id, 'Введите имя новой группы', reply_markup=stop_kb)

    @staticmethod
    @group_add_router.message(F.text == '➕🗃️Отмена')
    async def state_cancel_handler(message: Message, state: FSMContext):
        telegram_user_id = message.from_user.id
        await state.clear()
        await GroupChangeCurrentStart.change_current_group(telegram_user_id)
        # await GroupsRead.groups_read_and_main_menu(telegram_user_id)

    @staticmethod
    @group_add_router.message(NewGroupState.name)
    async def add_name_for_new_group_handler(message: Message, state: FSMContext):
        kb = [[KeyboardButton(text="Без описания"), KeyboardButton(text="➕🗃️Отмена")]]
        stop_kb = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        await state.update_data(name=message.text, description="")
        await state.set_state(NewGroupState.description)
        await MyBot.bot.send_message(message.chat.id, "Теперь введите описание", reply_markup=stop_kb)

    @staticmethod
    @group_add_router.message(NewGroupState.description)
    async def add_description_for_new_group_handler(message: Message, state: FSMContext):
        telegram_user_id = message.from_user.id
        if message.text != "Без описания":
            await state.update_data(description=message.text)
        new_group_data = await state.get_data()
        await state.clear()
        order_number = await GroupAddAPI.get_next_order_number_api(telegram_user_id)
        status = await GroupAddAPI.add_new_group_api(
            telegram_user_id,
            new_group_data['name'],
            new_group_data['description'],
            order_number
        )
        if status == 201:
            message_text = (f"Новая группа *\"{new_group_data['name']}\"* создана.\n"
                            f"Описание: *\"{new_group_data['description']}\"*\n")
        else:
            message_text = "Что-то пошло не так."
        await MyBot.bot.send_message(chat_id=telegram_user_id,
                                     text=message_text,
                                     reply_markup=ReplyKeyboardRemove(),
                                     parse_mode='Markdown')
        #  Чтение списка категорий:
        await GroupChangeCurrentStart.change_current_group(telegram_user_id)
        # await GroupsRead.groups_read_and_main_menu(telegram_user_id)
