from aiogram import Router
from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# from bot.api.django_auth import django_auth, update_last_request_time
# from bot.create_bot import MyBot


# class GroupsDataProcessing:
#
#     @staticmethod
#     async def data_processing(groups_data: list) -> str:
#         message_text = ''
#         number = 1
#         for group in groups_data:
#             group_name = group['name']
#             group_description = group.get('description', '')
#             message_text += f"{number}. {group_name}"
#             number += 1
#             if group_description != '':
#                 message_text += f" ({group_description})\n"
#             else:
#                 message_text += '\n'
#         if message_text == "":
#             message_text += "Ни одной категории пока не создано."
#         return message_text
#
#
# class GroupsAPI:
#
#     @staticmethod
#     @update_last_request_time(django_auth)
#     async def get_lists_detail_api(telegram_user_id: int) -> str:
#         url = f"{django_address}/lists/detail/"
#         data = {"telegram_user_id": telegram_user_id}
#         response = django_auth.session.get(url=url, data=data)
#         list_name = response.json()['name']
#         return list_name
#
#     @staticmethod
#     @update_last_request_time(django_auth)
#     async def get_groups_for_current_list_api(telegram_user_id: int) -> str:
#         url = f"{django_address}/groups/"
#         data = {"telegram_user_id": telegram_user_id}
#         response = django_auth.session.get(url=url, data=data)
#         message_text = await GroupsDataProcessing.data_processing(response.json())
#         return message_text
#
#
# class GroupsMainMenuKeyboard:
#
#     @staticmethod
async def groups_main_menu_keyboard_builder():
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="🔀🗃️"),
        KeyboardButton(text="✏️🗃️"),
        KeyboardButton(text="➕🗃️"),
        # KeyboardButton(text="⬆⬇🗃️"),
        KeyboardButton(text="❌️🗃️"),
        KeyboardButton(text="↩️📋")  # ,Назад
    )
    builder.adjust(6)
    return builder.as_markup(resize_keyboard=True)


groups_main_menu_router = Router()


# class GroupsRead:
#
#     @staticmethod
#     async def groups_read_and_main_menu(telegram_user_id: int):
#         #  Отправка сообщения "Список {list_name}:"
#         list_name = await GroupsAPI.get_lists_detail_api(telegram_user_id)
#         text_list_name = f"Группы списка \n\"{list_name}\":"
#         keyboard = await GroupsMainMenuKeyboard.groups_main_menu_keyboard_builder()
#         await MyBot.bot.send_message(chat_id=telegram_user_id, text=text_list_name, reply_markup=keyboard)
#         message_text = await GroupsAPI.get_groups_for_current_list_api(telegram_user_id)
#         await MyBot.bot.send_message(chat_id=telegram_user_id, text=message_text)
#
#     @staticmethod
#     @groups_main_menu_router.message(
#         (F.text.startswith("🗃️Gr")) |
#         (F.text.startswith("🗃️")) |
#         (F.text.startswith("🔄🗃️")) |
#         (F.text.startswith("🗃️Groups"))
#     )
#     async def groups_read_and_main_menu_header(message: Message):
#         telegram_user_id = message.from_user.id
#         await GroupsRead.groups_read_and_main_menu(telegram_user_id)
