from typing import Tuple

from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder
from requests import Response

from bot.api.django_auth import django_auth, update_last_request_time
from bot.business_processes.lists.lists_read_and_menu import ListsReadAndMenu
from bot.business_processes.lists.utils.lits_details_api import get_lists_detail_api
from bot.constants import django_address
from bot.create_bot import MyBot

list_delete_router = Router()


class ListDeleteStart:
    """
            Class handles message "📦❌" and starts process of deleting lists with sending
        listing of lists ond inline keyboard for choice list to delete.
    """

    @staticmethod
    async def join_data(message_text: str, text_own: str, text_shared: str, buttons_own: list, buttons_shared: list
                        ) -> Tuple[str, InlineKeyboardMarkup]:
        builder = InlineKeyboardBuilder()
        count_own, count_shared = 0, 0
        if text_own != "_____Собственные списки:\n":  # If there is own lists
            message_text += text_own  # add own lists text part to final message text
            count_own = len(text_own.splitlines()) - 2  # count buttons for own lists
        if text_shared != "_____Списки других пользователей:\n":
            message_text += text_shared  # add shared lists text part to final message text
            count_shared = len(text_shared.splitlines()) - 2  # count buttons for shared lists
        adjust = []
        if count_own > 0:
            for button in buttons_own:
                builder.add(button)  # Adding own lists buttons to keyboard
            i = 1
            while i <= count_own // 5:  # Processing *args of keys lines in keyboard with width in 5 buttons
                adjust.append(5)
                i += 1
            adjust.append(count_own % 5)  # Last line of own lists buttons width arg for keyboard
        if count_shared > 0:
            for button in buttons_shared:
                builder.add(button)  # Adding shared lists buttons to keyboard
            i = 1
            while i <= count_shared // 5:  # Processing *args of keys lines in keyboard with width in 5 buttons
                adjust.append(5)
                i += 1
            adjust.append(count_shared % 5)  # Last line of shared lists buttons width arg for keyboard
        builder.adjust(*adjust)  # Set the inline-keyboard lines widths
        keyboard = builder.as_markup(resize_keyboard=True)
        return message_text, keyboard

    @staticmethod
    async def data_to_text_and_keyboard(list_of_lists: list, profile_id: int) -> Tuple[str, InlineKeyboardMarkup]:
        """
            Function returns message text with list of lists and keyboard for choice list to delete
        """
        message_text = "Выберите список для удаления:\n"
        text_own = "\n\_\_\_\_\_Собственные списки:\n"
        number_own = 1
        buttons_own = []
        number_shared = 1
        buttons_shared = []
        text_shared = "\n\_\_\_\_\_Списки других пользователей:\n"
        # builder = InlineKeyboardBuilder()
        current_list_data = list_of_lists.pop()  # To highlight current list in bold
        for list_dict in list_of_lists:
            list_dict_fields = list_dict['fields']
            if list_dict_fields['owner'] == profile_id:
                number = number_own
            else:
                number = number_shared
            if list_dict_fields['name'] == current_list_data['name']:  # check is it current list
                text = f"*{number}. {list_dict_fields['name']}*"  # highlighting list name by stars
            else:
                text = f"{number}. {list_dict_fields['name']}"  # adding not highlighted list name cos it is not current
            if list_dict_fields['description']:  # is there is description for next list?
                if list_dict_fields['description'] == current_list_data['description']:  # check is it current list
                    text += f" *({list_dict_fields['description']})*.\n"  # highlighting list description by stars
                else:  # adding not highlighted list description cos it is not current:
                    text += f" ({list_dict_fields['description']}).\n"
            else:
                text += ".\n"
            # Making inline-buttons and assembly message text parts for own and shared lists:
            if list_dict_fields['owner'] == profile_id:
                number_own += 1
                button_text = f"❌️{number}"
                buttons_own.append(
                    InlineKeyboardButton(text=button_text, callback_data=f"delete_list, {list_dict['pk']}"))
                text_own += text
            else:
                number_shared += 1
                button_text = f"🙈{number}"
                buttons_shared.append(
                    InlineKeyboardButton(text=button_text, callback_data=f"delete_list, {list_dict['pk']}"))
                text_shared += text
        # Assembling keyboard and final message text:
        message_text, keyboard = \
            await ListDeleteStart.join_data(message_text, text_own, text_shared, buttons_own, buttons_shared)
        message_text += ("\n Свои списки можно удалить полностью (❌️), "
                         "а к спискам других пользователей можно только удалить доступ (🙈)")
        return message_text, keyboard

    @staticmethod
    @update_last_request_time(django_auth)
    async def get_user_profile_id_api(telegram_user_id: int) -> int:
        url = f'{django_address}/profiles/get_one/'
        data = {"telegram_user_id": telegram_user_id}
        response = django_auth.session.get(url=url, data=data)
        profile_id = response.json()['id']
        return profile_id

    @staticmethod
    async def get_lists_and_delete_keyboard_api(telegram_user_id: int) -> Tuple[str, InlineKeyboardMarkup]:
        """
                Function requests from Django listing of lists data without related objects.
            Then requests data_to_text_and_keyboard function to pars data to message text
            and keyboard.
            Then returns message text and keyboard
        """
        url = f'{django_address}/lists/users_lists/'
        data = {"telegram_user_id": telegram_user_id}
        response = django_auth.session.get(url=url, data=data)
        profile_id = await ListDeleteStart.get_user_profile_id_api(telegram_user_id)
        text_lists, delete_keyboard = await ListDeleteStart.data_to_text_and_keyboard(response.json(), profile_id)
        return text_lists, delete_keyboard

    @staticmethod
    @list_delete_router.message(F.text == '📦❌')
    async def list_delete_start_handler(message: Message):
        """
                Requests from get_lists_and_delete_keyboard_api function message text with listing of lists
            and inline delete keyboard.
        """
        telegram_user_id = message.from_user.id
        text_lists, delete_keyboard = await ListDeleteStart.get_lists_and_delete_keyboard_api(telegram_user_id)
        #  Отправка сообщения со списком категорий и inline-клавиатурой для удаления категорий:
        await MyBot.bot.send_message(
            chat_id=telegram_user_id, text=text_lists, reply_markup=delete_keyboard, parse_mode='Markdown'
        )


class ListDeleteDecision:
    """
            Class handles callback with list_id for delete. gets from Django and
        shows with message what's inside list with inline keyboard to deside delete or not this list.
    """

    @staticmethod
    async def processing_list_data(list_data: list, list_id: str) -> Tuple[str, InlineKeyboardMarkup]:
        text = ''
        number = 1
        for category in list_data:
            text += f"_____{category['name']}\n"
            if len(category['purchases']) == 0:
                text += f"    ..............\n"
            else:
                for purchase in category['purchases']:
                    text += f"{number}. {purchase['name']}"
                    number += 1
                    purchase_description = purchase.get('description', None)
                    if purchase_description is not None:
                        text += f" ({purchase_description})\n"
                    else:
                        text += '\n'

        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="Да, я хочу удалить список!",
                                         callback_data=f"list_delete_decision OK {list_id}"))
        builder.add(InlineKeyboardButton(text="Нет, я передумал удалять список!",
                                         callback_data=f"list_delete_decision Cancel {list_id}"))
        builder.adjust(1)
        keyboard = builder.as_markup(resize_keyboard=True)
        return text, keyboard

    @staticmethod
    @update_last_request_time(django_auth)
    async def get_hale_list_api(telegram_user_id: int, list_id: str) -> Tuple[str, str, InlineKeyboardMarkup]:
        url = f'{django_address}/lists/'
        data = {
            "telegram_user_id": telegram_user_id,
            "list_id": list_id
        }
        list_name = await get_lists_detail_api(telegram_user_id, list_id)
        response = django_auth.session.get(url=url, data=data)
        message_text, deside_keyboard = await ListDeleteDecision.processing_list_data(response.json(), list_id)
        return list_name, message_text, deside_keyboard

    @staticmethod
    @list_delete_router.callback_query(lambda c: c.data and c.data.startswith('delete_list'))
    async def delete_list_sure_question_handler(callback: CallbackQuery):
        telegram_user_id = callback.from_user.id
        data = callback.data.split(" ")
        list_id = data[1]
        list_name, text_list, keyboard = await ListDeleteDecision.get_hale_list_api(telegram_user_id, list_id)
        list_message_name = f"Вы уверены, что хотите удалить список \n\"{list_name}\":\nВот его содержимое:"
        # Сообщение с именем списка, удаляет reply-клавиатуру:
        await MyBot.bot.send_message(chat_id=telegram_user_id, text=list_message_name, reply_markup=ReplyKeyboardRemove())
        # Сообщение со списком категорий и их позициями, с inline-клавиатурой подтверждения:
        await MyBot.bot.send_message(chat_id=telegram_user_id, text=text_list, reply_markup=keyboard)


class ListDelete:
    """
            Class handles decision about delete chosen list and delete it or not.
        Then redirect to lists main menu.
    """

    @staticmethod
    @update_last_request_time(django_auth)
    async def list_delete_api(telegram_user_id: int, list_id: int) -> Response:
        url = f'{django_address}/lists/detail/'
        data = {
            "telegram_user_id": telegram_user_id,
            'list_id': list_id
        }
        response = await django_auth.session.delete(url=url, data=data)
        return response

    @staticmethod
    @list_delete_router.callback_query(lambda c: c.data and c.data.startswith('list_delete_decision'))
    async def list_delete_or_not_handler(callback: CallbackQuery):
        telegram_user_id = callback.from_user.id
        data = callback.data.split(' ')[1:]
        decision = data[0]
        list_id = int(data[1])

        if decision == "Cancel":
            text = "OK"
            await MyBot.bot.send_message(chat_id=telegram_user_id, text=text)

        else:
            response = await ListDelete.list_delete_api(telegram_user_id, list_id)

            if response.status_code == 406:
                text = response.json()['error']
                await MyBot.bot.send_message(chat_id=telegram_user_id, text=text)

            elif response.status_code != 200:
                text = "Что-то пошло не так..."
                await MyBot.bot.send_message(chat_id=telegram_user_id, text=text)

        await ListsReadAndMenu.lists_read_and_menu(telegram_user_id)
