from typing import Tuple

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, \
    ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from requests import Response

from bot.api.django_auth import django_auth, update_last_request_time

from bot.create_bot import MyBot

from ..lists.lists_share_and_menu import ListsShareStart
from ..lists.utils.share_menu_keyboard import share_menu_keyboard_buttons
from ...constants import django_address, buttons_styles
from ...translate import transl

manage_friends_router = Router()


class FriendsList:

    @staticmethod
    async def processing_data(friends_data: list) -> Tuple[str, InlineKeyboardMarkup]:
        builder = InlineKeyboardBuilder()
        message_text = 'Ваше окружение:\n'
        number = 1
        for friend in friends_data:
            friend_id = friend['pk']
            friend_firstname = friend['fields']['telegram_firstname']
            friend_lastname = friend['fields']['telegram_lastname']

            message_text += f"{number}. {friend_firstname} {friend_lastname}\n"
            builder.add(InlineKeyboardButton(text=f"{number}", callback_data=f"delete_friend {friend_id}"))

            number += 1
        builder.add(InlineKeyboardButton(text="Добавить", callback_data=f"add_friend"))
        builder.adjust(6, -1)
        keyboard = builder.as_markup(resize_keyboard=True)
        if message_text == 'Ваше окружение:\n':
            message_text = "В вашем окружении никого нет."
        else:
            message_text += "\n(нажмите номер пользователя для удаления из окружения)"
        return message_text, keyboard

    @staticmethod
    @update_last_request_time(django_auth)
    async def friends_list_api(telegram_user_id: int) -> Tuple[str, InlineKeyboardMarkup]:
        url = f"{django_address}/profiles/get_friends/"
        data = {"telegram_user_id": telegram_user_id}
        response = django_auth.session.get(url=url, data=data)
        return await FriendsList.processing_data(response.json())

    @staticmethod
    async def friends_list(telegram_user_id):
        message_text, keyboard = await FriendsList.friends_list_api(telegram_user_id)
        await MyBot.bot.send_message(chat_id=telegram_user_id, text=message_text, reply_markup=keyboard)

    @staticmethod
    @manage_friends_router.message(
        lambda message:
        any(message.text == share_menu_keyboard_buttons(lang)[button_style]['surrounding']
            for lang in transl.keys() for button_style in buttons_styles)
        # F.text == "Окружение"
    )
    async def friends_list_handler(message: Message):
        telegram_user_id = message.from_user.id
        await FriendsList.friends_list(telegram_user_id)


class DeleteFriend:

    @staticmethod
    @update_last_request_time(django_auth)
    async def delete_friend_api(telegram_user_id: int, friend_id: str) -> Response:
        url = f"{django_address}/profiles/delete_friend/"
        data = {
            "telegram_user_id": telegram_user_id,
            "friend_id": friend_id
        }
        response = await django_auth.session.delete(url=url, data=data)
        return response

    @staticmethod
    @manage_friends_router.callback_query(lambda c: c.data and c.data.startswith("delete_friend"))
    async def delete_friend_handler(callback: CallbackQuery):
        telegram_user_id = callback.from_user.id
        friend_id = callback.data.split(" ")[1]
        response = await DeleteFriend.delete_friend_api(telegram_user_id, friend_id)
        if response.status_code != 200:
            await MyBot.bot.send_message(chat_id=telegram_user_id, text="Что-то пошло не так...")
        await FriendsList.friends_list(telegram_user_id)
    # TODO: Доделать DeleteFriend.
    #  1. Удалить доступы
    #  2. Удалить из окружения


class AddFriendByCommand:

    @staticmethod
    @update_last_request_time(django_auth)
    async def add_remove_friend_api(telegram_user_id: int, move: str = "add",
                                    friend_username: str = None, friend_id: str = None) -> Response:
        url = f"{django_address}/profiles/update_friends/"
        data = {
            "telegram_user_id": telegram_user_id,
            "move": move,
            "friend_username": friend_username,
            "friend_id": friend_id
        }
        response = await django_auth.session.put(url=url, data=data)
        return response

    @staticmethod
    @manage_friends_router.message(F.text.startswith("Добавить в друзья пользователя"))
    async def add_user_to_friends_handler(message: Message):
        telegram_user_id = message.from_user.id
        friend_id = message.text.split(':')[1]
        response = await AddFriendByCommand.add_remove_friend_api(telegram_user_id, friend_id=friend_id)
        if response.status_code != 200:
            await MyBot.bot.send_message(chat_id=telegram_user_id, text="Что-то пошло не так...")
        await ListsShareStart.lists_share_start(telegram_user_id)





class AddFriendManual:

    class State(StatesGroup):
        friend_username = State()
        friend_id = State()

    @staticmethod
    @manage_friends_router.callback_query(lambda c: c.data and c.data == "add_friend")
    async def add_new_friend_handler(callback: CallbackQuery):
        telegram_user_id = callback.from_user.id
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="User name", callback_data="add_friend_by_username"))
        builder.add(InlineKeyboardButton(text="telegram_id", callback_data="add_friend_by_telegram_id"))
        keyboard = builder.as_markup(resize_keyboard=True)
        text = "Какие данные о пользователе у Вас есть?"
        await MyBot.bot.send_message(chat_id=telegram_user_id, text=text, reply_markup=keyboard)

    stop_keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="➕👨‍👦‍👦‍Отмена")]], resize_keyboard=True)

    @staticmethod
    @manage_friends_router.message(F.text.startswith("➕👨‍👦‍👦‍Отмена"))
    async def state_cancel_handler(message: Message, state: FSMContext):
        telegram_user_id = message.from_user.id
        await state.clear()
        await ListsShareStart.lists_share_start(telegram_user_id)


class AddFriendByUsername:

    @staticmethod
    @manage_friends_router.callback_query(lambda c: c.data and c.data == "add_friend_by_username")
    async def add_new_friend_by_username_handler(callback: CallbackQuery, state: FSMContext):
        telegram_user_id = callback.from_user.id
        await state.set_state(AddFriendManual.State.friend_username)
        await MyBot.bot.send_message(chat_id=telegram_user_id,
                                     text="Пришлите username пользователя:",
                                     reply_markup=AddFriendManual.stop_keyboard)

    @staticmethod
    @manage_friends_router.message(AddFriendManual.State.friend_username)
    async def add_new_friend_by_username_state_handler(message: Message, state: FSMContext):
        await state.clear()
        telegram_user_id = message.from_user.id
        # TODO: если нужно -- отделить username от @ или от ссылки t.me/
        friend_username = message.text
        response = await AddFriendByCommand.add_remove_friend_api(telegram_user_id, friend_username=friend_username)
        if response.status_code == 400:
            message_text = response.json()["error"]
            await MyBot.bot.send_message(chat_id=telegram_user_id, text=message_text)
        elif response.status_code != 200:
            await MyBot.bot.send_message(chat_id=telegram_user_id, text="Что-то пошло не так...")
        await ListsShareStart.lists_share_start(telegram_user_id)


class AddFriendByTelegramID:

    @staticmethod
    @manage_friends_router.callback_query(lambda c: c.data and c.data == "add_friend_by_telegram_id")
    async def add_new_friend_by_id_handler(callback: CallbackQuery, state: FSMContext):
        telegram_user_id = callback.from_user.id
        await state.set_state(AddFriendManual.State.friend_id)
        await MyBot.bot.send_message(chat_id=telegram_user_id,
                                     text="Пришлите telegram_id пользователя:",
                                     reply_markup=AddFriendManual.stop_keyboard)

    @staticmethod
    @manage_friends_router.message(AddFriendManual.State.friend_id)
    async def add_new_friend_by_id_state_handler(message: Message, state: FSMContext):
        await state.clear()
        telegram_user_id = message.from_user.id
        friend_id = message.text
        response = await AddFriendByCommand.add_remove_friend_api(telegram_user_id, friend_id=friend_id)
        if response.status_code == 400:
            message_text = response.json()["error"]
            await MyBot.bot.send_message(chat_id=telegram_user_id, text=message_text)
        elif response.status_code != 200:
            await MyBot.bot.send_message(chat_id=telegram_user_id, text="Что-то пошло не так...")
        await ListsShareStart.lists_share_start(telegram_user_id)


class AddMeToFriends:

    @staticmethod
    @manage_friends_router.message(
        lambda message:
        any(message.text == share_menu_keyboard_buttons(lang)[button_style]['add_me']
            for lang in transl.keys() for button_style in buttons_styles)
        # F.text == "Добавь меня"
    )
    async def add_me_to_friends_handler(callback: CallbackQuery):
        telegram_user_id = callback.from_user.id
        telegram_user_firstname = callback.from_user.first_name
        telegram_user_lastname = callback.from_user.last_name
        message_text = ("Перешлите сообщение-команду ниже другому пользователю "
                        "и попросите его переслать его в чат с ботом, "
                        "чтобы пользователь мог дать Вам доступ к своим спискам:")
        await MyBot.bot.send_message(chat_id=telegram_user_id, text=message_text)
        text = (f"\nДобавить в друзья пользователя {telegram_user_firstname} {telegram_user_lastname}"
                f" с id:{telegram_user_id}")
        await MyBot.bot.send_message(chat_id=telegram_user_id, text=text)
