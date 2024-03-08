from aiogram import Router
from bot.api.django_auth import django_auth, update_last_request_time
from bot.business_processes.lists.utils.lists_menu_keyboard import lists_menu_keyboard
from bot.constants import django_address

from bot.create_bot import MyBot


class UsersListsDataProcessing:

    @staticmethod
    async def users_lists_data_processing(list_of_lists: list) -> str:
        message_text = "Ваши списки:\n"
        number = 1
        current_list_data = list_of_lists.pop()
        for list_dict in list_of_lists:
            list_dict_fields = list_dict['fields']
            if list_dict_fields['name'] == current_list_data['name']:
                message_text += f"*{number}. {list_dict_fields['name']}*"
            else:
                message_text += f"{number}. {list_dict_fields['name']}"
            if list_dict_fields['description']:
                if list_dict_fields['description'] == current_list_data['description']:
                    message_text += f" *({list_dict_fields['description']}).*\n"
                else:
                    message_text += f" ({list_dict_fields['description']}).\n"
            else:
                message_text += "\n"
            number += 1
        return message_text


class UsersListsReadAPI:

    @staticmethod
    @update_last_request_time(django_auth)
    async def users_lists_read_api(telegram_user_id: int) -> str:
        url = f"{django_address}/lists/users_lists/"
        data = {"telegram_user_id": telegram_user_id}
        response = django_auth.session.get(url=url, data=data)
        message_text = await UsersListsDataProcessing.users_lists_data_processing(response.json())
        return message_text


lists_menu_router = Router()


class ListsReadAndMenu:

    @staticmethod
    async def lists_read_and_menu(telegram_user_id: int):
        keyboard = await lists_menu_keyboard(telegram_user_id)
        message_text = await UsersListsReadAPI.users_lists_read_api(telegram_user_id)
        await MyBot.bot.send_message(telegram_user_id, message_text, reply_markup=keyboard, parse_mode='Markdown')
