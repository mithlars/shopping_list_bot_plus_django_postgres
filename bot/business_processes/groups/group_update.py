import copy
from typing import Tuple, Dict, Any

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, KeyboardButton, \
    ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder
from requests import Response

from bot.api.django_auth import django_auth, update_last_request_time
from bot.business_processes.groups.group_change_current import GroupChangeCurrentStart
from bot.constants import django_address
from bot.create_bot import MyBot

# from bot.business_processes.groups.utils.groups_menu_keyboard import GroupsRead

group_update_router = Router()


class GroupUpdateStart:

    @staticmethod
    async def groups_data_processing(list_of_groups: list) -> Tuple[str, InlineKeyboardMarkup]:
        message_text = "Выберите категорию для редактирования:\n"
        number = 1
        builder = InlineKeyboardBuilder()
        for group_dict in list_of_groups:
            message_text += f"{number}. {group_dict['name']}"
            if group_dict['description'] != '' and group_dict['description'] is not None:
                message_text += f" ({group_dict['description']}).\n"
            else:
                message_text += "\n"

            builder.add(InlineKeyboardButton(text=f"{number}", callback_data=f"group_update {group_dict['id']}"))
            number += 1
        builder.adjust(6)
        keyboard = builder.as_markup(resize_keyboard=True)
        return message_text, keyboard

    @staticmethod
    @update_last_request_time(django_auth)
    async def groups_read_for_update_api(telegram_user_id: int) -> Tuple[str, InlineKeyboardMarkup]:
        url = f"{django_address}/groups/"
        data = {"telegram_user_id": telegram_user_id}
        response = django_auth.session.get(url=url, data=data)
        message_text, keyboard = await GroupUpdateStart.groups_data_processing(response.json())
        return message_text, keyboard

    @staticmethod
    @group_update_router.callback_query(lambda c: c.data and c.data == "group_update")
    async def groups_read_for_update_handler(callback: CallbackQuery):
        telegram_user_id = callback.from_user.id
        message_text, keyboard = await GroupUpdateStart.groups_read_for_update_api(telegram_user_id)
        await MyBot.bot.send_message(chat_id=telegram_user_id, text=message_text, reply_markup=keyboard)


class GroupUpdateState(StatesGroup):
    name = State()
    description = State()


class GroupUpdateFMS:

    @staticmethod
    @update_last_request_time(django_auth)
    async def get_group_api(telegram_user_id: int, group_id: str) -> Dict[str, Any]:
        url = f"{django_address}/groups/get_one/"
        data = {
            "telegram_user_id": telegram_user_id,
            "group_id": group_id
        }
        response = django_auth.session.get(url=url, data=data)
        return response.json()

    kb = [[KeyboardButton(text="Без изменений"), KeyboardButton(text="✏️🗃️Отмена")]]
    stop_same_kb = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    @staticmethod
    @group_update_router.callback_query(lambda c: c.data and c.data.startswith('group_update'))
    async def choose_group_for_update_handler(callback: CallbackQuery, state: FSMContext):
        telegram_user_id = callback.from_user.id
        await state.set_state(GroupUpdateState.name)

        group_id = callback.data.split(" ")[1]
        group_data = await GroupUpdateFMS.get_group_api(telegram_user_id, group_id)
        group_ald_name = group_data.get('name')
        group_ald_description = group_data.get('description', '')
        await state.update_data(group_id=group_id,
                                group_ald_name=group_ald_name,
                                group_ald_description=group_ald_description)
        await MyBot.bot.send_message(chat_id=telegram_user_id,
                                     text='Введите новое имя для группы',
                                     reply_markup=GroupUpdateFMS.stop_same_kb)

        await MyBot.bot.send_message(chat_id=telegram_user_id,
                                     text=f"`{group_ald_name}`",
                                     parse_mode='MarkdownV2')

    @staticmethod
    @group_update_router.message(F.text.startswith('✏️🗃️Отмена'))
    async def state_cancel_handler(message: Message, state: FSMContext):
        telegram_user_id = message.from_user.id
        await state.clear()
        await GroupChangeCurrentStart.change_current_group(telegram_user_id)
        # await GroupsRead.groups_read_and_main_menu(telegram_user_id)

    @staticmethod
    @group_update_router.message(GroupUpdateState.name)
    async def update_group_name_handler(message: Message, state: FSMContext):
        if message.text == "Без изменений":
            data = await state.get_data()
            await state.update_data(name=data["group_ald_name"])
        else:
            await state.update_data(name=message.text)
        kb = copy.deepcopy(GroupUpdateFMS.kb)
        kb[0].append(KeyboardButton(text="Без описания"))
        stop_same_kb = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        await state.set_state(GroupUpdateState.description)
        await MyBot.bot.send_message(chat_id=message.chat.id,
                                     text="Теперь введите новое описание",
                                     reply_markup=stop_same_kb)

    @staticmethod
    @update_last_request_time(django_auth)
    async def group_update_api(telegram_user_id: int, data: Dict[str, Any]) -> Response:
        url = f"{django_address}/groups/update/"
        data["telegram_user_id"] = telegram_user_id
        response = await django_auth.session.put(url=url, data=data)
        return response

    @staticmethod
    @group_update_router.message(GroupUpdateState.description)
    async def update_group_description_handler(message: Message, state: FSMContext):
        telegram_user_id = message.from_user.id
        group_data = await state.get_data()
        if message.text == "Без изменений":
            group_data["description"] = group_data["group_ald_description"]
        elif message.text == "Без описания":
            group_data["description"] = ""
        else:
            group_data["description"] = message.text

        await state.clear()
        if (group_data['name'] == group_data["group_ald_name"]
                and group_data["description"] == group_data["group_ald_description"]):
            await MyBot.bot.send_message(chat_id=telegram_user_id,
                                         text="Вы решили оставить данные категории без изменений.",
                                         reply_markup=ReplyKeyboardRemove())
            await GroupChangeCurrentStart.change_current_group(telegram_user_id)
            # await GroupsRead.groups_read_and_main_menu(telegram_user_id)
        else:
            response = await GroupUpdateFMS.group_update_api(telegram_user_id, group_data)
            if response.status_code != 200:
                await MyBot.bot.send_message(chat_id=telegram_user_id, text="Что-то пошло не так")
            await GroupChangeCurrentStart.change_current_group(telegram_user_id)
            # await GroupsRead.groups_read_and_main_menu(telegram_user_id)
