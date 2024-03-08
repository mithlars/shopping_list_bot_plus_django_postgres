from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from bot.emoji import emoji

"""
    classes structure:
        CategoriesRead -- is accountable for handle business-processes start command 
           \                 and for presenting categories options menu
            `--categories_read_and_menu_handler() -- is handling request message for categories menu
                `--categories_read_and_menu() -- sends message with list of categories and categories menu keyboard
        
        CategoriesKeyboards -- is accountable for functions which builds keyboards 
            `--categories_keyboard_builder() -- builds main reply-keyboard for categories menu 
        
        CategoriesAPI -- is accountable for API-functions to make requests to Django-service 
            `--get_categories_for_current_list() -- requests from Django list of categories for current user's list
            `--get_lists_detail_api() -- requests from Django details of users current list for the message
        
        CategoriesDataProcessing -- is accountable for processing data got from Django service 
            `--data_processing() -- does message-text from list of user's current's list categories list 
"""


# class CategoriesDataProcessing:
#     """ is accountable for processing data got from Django service """
#
#     @staticmethod
#     async def data_processing(categories: list) -> str:
#         """ does message-text from list of user's current's list categories list """
#         message_text = ''
#         number = 1
#         for category in categories:
#             category_name = category['name']
#             category_description = category.get('description', '')
#             message_text += f"{number}. {category_name}"
#             number += 1
#             if category_description != '' and category_description is not None:
#                 message_text += f" ({category_description})\n"
#             else:
#                 message_text += '\n'
#         return message_text
#
#
# class CategoriesAPI:
#     """ is accountable for API-functions to make requests to Django-service """
#
#     @staticmethod
#     @update_last_request_time(django_auth)
#     async def get_lists_detail_api(telegram_user_id: int) -> str:
#         """ requests from Django details of users current list for the message """
#         url = f"{django_address}/lists/detail/"
#         data = {"telegram_user_id": telegram_user_id}
#         response = django_auth.session.get(url=url, data=data)
#         list_text = response.json()['name']
#         list_description = response.json().get('description', "")
#         if list_description != "" and list_description is not None:
#             list_text += f" ({list_description})"
#         return list_text
#
#     @staticmethod
#     @update_last_request_time(django_auth)
#     async def get_categories_for_current_list(telegram_user_id: int) -> str:
#         """ requests from Django list of categories for current user's list """
#         url = f"{django_address}/categories/"
#         data = {"telegram_user_id": telegram_user_id}
#         response = django_auth.session.get(url=url, data=data)
#         message_text = await CategoriesDataProcessing.data_processing(response.json())
#         return message_text
#
#
# class CategoriesKeyboards:
#     """ is accountable for functions which builds keyboards  """
#
#     @staticmethod
async def categories_keyboard_builder():
    """ builds main reply-keyboard for categories menu """
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="✏️🗂️"),
        KeyboardButton(text="➕🗂️"),
        KeyboardButton(text="⬆⬇🗂️"),
        KeyboardButton(text=emoji['delete'] + emoji['categories']),
        KeyboardButton(text="🧹🗂️"),
        KeyboardButton(text="↩️📋")
    )
    builder.adjust(3, 5)
    return builder.as_markup(resize_keyboard=True)
#
#
# categories_read_router = Router()
#
#
# class CategoriesRead:
#     """ Is accountable for handle business-processes start command and for presenting categories options menu """
#
#     @staticmethod
#     async def categories_read_and_menu(telegram_user_id: int):
#         """ Sends message with list of categories and categories menu keyboard """
#
#         #  Sending message with name of user's current list:"
#         list_name = await CategoriesAPI.get_lists_detail_api(telegram_user_id)
#         list_text = f"""Категории списка \n*"{list_name}"*:"""
#         await MyBot.bot.send_message(chat_id=telegram_user_id, text=list_text, parse_mode='Markdown')
#
#         #  Sending message with categories list and categories main menu keyboard
#         keyword = await CategoriesKeyboards.categories_keyboard_builder()
#         text = await CategoriesAPI.get_categories_for_current_list(telegram_user_id)
#         await MyBot.bot.send_message(chat_id=telegram_user_id, text=text, reply_markup=keyword)
#
#     @staticmethod
#     @categories_read_router.message((F.text == "🔄🗂️") |
#                                     (F.text == "🗂️Категории") |
#                                     (F.text == "🗂️Categories") |
#                                     (F.text == "🗂️Cat") |
#                                     (F.text == "🗂️"))
#     async def categories_read_and_menu_handler(message: Message):
#         """ is handling request message for categories menu """
#         telegram_user_id = message.from_user.id
#         await CategoriesRead.categories_read_and_menu(telegram_user_id)
