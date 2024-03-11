from typing import Dict, Any

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from bot.business_processes.options.utils.get_profiles_options_api import get_profiles_options_api
from bot.emoji import emoji
from bot.translate import transl


def list_menu_keyboard_buttons(lang: str) -> Dict[str, Dict]:
    buttons_long = transl[lang]['list_menu']['buttons']
    buttons_short = transl[lang]['list_menu']['buttons_short']
    buttons = {
        'pics': {  # ["🔄📋", "✏️📋️", "➡️📁", "📁➡️", "🗃️", "🗂️", "📦", "🛠️"],
            'reload': emoji['reload'] + emoji['list'],
            'edit': emoji['edit'] + emoji['list'],
            'to_category': emoji['right'] + emoji['categories'],
            'from_category': emoji['categories'] + emoji['right'],
            'groups': emoji['groups'],
            'categories': emoji['categories'],
            'lists': emoji['lists'],
            'options': emoji['options']
        },
        'text': {  # ["reload📋", "edit️📋", "to category", "from category", "Groups", "Categories", "Lists", "Options"],
            'reload': buttons_long['reload'] + emoji['list'],
            'edit': buttons_long['edit'] + emoji['list'],
            'to_category': buttons_long['to_category'],
            'from_category': buttons_long['from_category'],
            'groups': buttons_long['groups'],
            'categories': buttons_long['categories'],
            'lists': buttons_long['lists'],
            'options': buttons_long['options']
        },
        'both': {  # ["🔄📋rld", "✏️📋️chg", "➡️📁ToCat", "📁➡️FrCat", "🗃️Gr.", "🗂️Cats", "📦Lists", "🛠️Opt."]
            'reload': emoji['reload'] + emoji['list'] + buttons_short['reload'],
            'edit': emoji['edit'] + emoji['list'] + buttons_short['edit'],
            'to_category': emoji['right'] + emoji['categories'] + buttons_short['to_category'],
            'from_category': emoji['categories'] + emoji['right'] + buttons_short['from_category'],
            'groups': emoji['groups'] + buttons_short['groups'],
            'categories': emoji['categories'] + buttons_short['categories'],
            'lists': emoji['lists'] + buttons_short['lists'],
            'options': emoji['options'] + buttons_short['options']
        },
    }
    return buttons


async def list_menu_keyboard_builder(telegram_user_id: int) -> ReplyKeyboardMarkup:
    options = await get_profiles_options_api(telegram_user_id)
    lang = options["telegram_language"]
    buttons = list_menu_keyboard_buttons(lang)
    builder = ReplyKeyboardBuilder()
    style = options["telegram_buttons_style"]
    for button_text in buttons[style].values():
        builder.add(KeyboardButton(text=button_text))
    builder.adjust(4)
    return builder.as_markup(resize_keyboard=True)
