from typing import Dict

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from bot.business_processes.options.utils.get_profiles_options_api import get_profiles_options_api
from bot.emoji import emoji
from bot.translate import transl

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


def categories_menu_keyboard_buttons(lang: str) -> Dict[str, Dict]:
    buttons_long = transl[lang]['categories_menu']['buttons']
    buttons_short = transl[lang]['categories_menu']['buttons_short']
    buttons = {
        'pics': {  # 'pics': ["✏️🗂️", "➕🗂️", "⬆⬇🗂️", '❌🗂️', "🧹🗂️", "↩️📋"],
            'edit': emoji['edit'] + emoji['categories'],
            'add': emoji['add'] + emoji['categories'],
            'sort': emoji['sort'] + emoji['categories'],
            'delete': emoji['delete'] + emoji['categories'],
            'clean': emoji['clean'] + emoji['categories'],
            'back': emoji['back'] + emoji['list']
        },
        'text': {  # 'text': ["изменить🗂️", "создать🗂️", "сортировать🗂️", "удалить🗂️", "очистить🗂️", "назад📋"],
            'edit': buttons_long['edit'] + emoji['categories'],
            'add': buttons_long['add'] + emoji['categories'],
            'sort': buttons_long['sort'] + emoji['categories'],
            'delete': buttons_long['delete'] + emoji['categories'],
            'clean': buttons_long['clean'] + emoji['categories'],
            'back': buttons_long['back'] + emoji['list']
        },
        'both': {  # 'both': ["✏️🗂️изм.", "➕🗂️созд.", "⬆⬇🗂️сорт.", "❌🗂️удал.", "🧹🗂️очис.", "↩️📋"]
            'edit': emoji['edit'] + emoji['categories'] + buttons_short['edit'],
            'add': emoji['add'] + emoji['categories'] + buttons_short['add'],
            'sort': emoji['sort'] + emoji['categories'] + buttons_short['sort'],
            'delete': emoji['delete'] + emoji['categories'] + buttons_short['delete'],
            'clean': emoji['clean'] + emoji['categories'] + buttons_short['clean'],
            'back': emoji['back'] + emoji['list'] + buttons_short['back']
        },
    }
    return buttons


async def categories_menu_keyboard_builder(telegram_user_id: int) -> ReplyKeyboardMarkup:
    """ builds main reply-keyboard for categories menu """
    options = await get_profiles_options_api(telegram_user_id)
    lang = options["telegram_language"]
    buttons = categories_menu_keyboard_buttons(lang)
    style = options["telegram_buttons_style"]
    builder = ReplyKeyboardBuilder()
    for button_text in buttons[style].values():
        builder.add(KeyboardButton(text=button_text))
    builder.adjust(3)
    return builder.as_markup(resize_keyboard=True)
