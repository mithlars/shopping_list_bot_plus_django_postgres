from typing import Dict

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from bot.emoji import emoji
from bot.translate import transl

from bot.business_processes.options.utils.get_profiles_options_api import get_profiles_options_api

def lists_menu_keyboard_buttons(lang: str) -> Dict[str, Dict]:
    buttons_long = transl[lang]['lists_menu']['buttons']
    buttons_short = transl[lang]['lists_menu']['buttons_short']
    buttons = {
        'pics': {  # 'pics': ["🔀📦", "✏️️📦", "➕📦", "👨‍👦‍👦‍", "📦❌", "📦🧹", "↩️📋"],
            'switch': emoji['switch'] + emoji['lists'],
            'edit': emoji['edit'] + emoji['lists'],
            'add': emoji['add'] + emoji['lists'],
            'share': emoji['share'],
            'delete': emoji['lists'] + emoji['delete'],
            'clean': emoji['lists'] + emoji['clean'],
            'back': emoji['back'] + emoji['list']
        },
        'text': {  # 'text': ["сменить📦", "изменить📦", "создать📦", "доступ", "удалить📦", "очистить📦", "назад"],
            'switch': buttons_long['switch'] + emoji['lists'],
            'edit': buttons_long['edit'] + emoji['lists'],
            'add': buttons_long['add'] + emoji['lists'],
            'share': buttons_long['share'],
            'delete': buttons_long['delete'] + emoji['lists'],
            'clean': buttons_long['clean'] + emoji['lists'],
            'back': buttons_long['back'] + emoji['list']
        },
        'both': {  # 'both': ["🔀📦смен.", "✏️️📦изм.", "➕📦созд.", "👨‍👦‍👦‍дост.", "📦❌удал.", "📦🧹очис.", "↩️📋"]
            'switch': emoji['switch'] + emoji['lists'] + buttons_short['switch'],
            'edit': emoji['edit'] + emoji['lists'] + buttons_short['edit'],
            'add': emoji['add'] + emoji['lists'] + buttons_short['add'],
            'share': emoji['share'] + buttons_short['share'],
            'delete': emoji['lists'] + emoji['delete'] + buttons_short['delete'],
            'clean': emoji['lists'] + emoji['clean'] + buttons_short['clean'],
            'back': emoji['back'] + emoji['list'] + buttons_short['back']
        },
    }
    return buttons


async def lists_menu_keyboard(telegram_user_id: int) -> ReplyKeyboardMarkup:
    options = await get_profiles_options_api(telegram_user_id)
    lang = options["telegram_language"]
    buttons = lists_menu_keyboard_buttons(lang)
    style = options["telegram_buttons_style"]
    builder = ReplyKeyboardBuilder()
    for button_text in buttons[style].values():
        builder.add(KeyboardButton(text=button_text))
    builder.adjust(4)
    return builder.as_markup(resize_keyboard=True)