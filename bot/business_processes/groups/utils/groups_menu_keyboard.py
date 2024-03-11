from typing import Dict

from aiogram import Router
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from bot.business_processes.options.utils.get_profiles_options_api import get_profiles_options_api
from bot.emoji import emoji
from bot.translate import transl


def groups_menu_keyboard_buttons(lang: str) -> Dict[str, Dict]:
    buttons_long = transl[lang]['groups_menu']['buttons']
    buttons_short = transl[lang]['groups_menu']['buttons_short']
    buttons = {
        'pics': {  # 'pics': ["🔀🗃️", "✏️🗃️", "➕🗃️", "⬆⬇🗃️", "❌️🗃️", "↩️📋"],
            'switch': emoji['switch'] + emoji['groups'],
            'edit':   emoji['edit'] + emoji['groups'],
            'add':    emoji['add'] + emoji['groups'],
            # 'sort':   emoji['sort'] + emoji['groups'],
            'delete': emoji['delete'] + emoji['groups'],
            'back':   emoji['back'] + emoji['list']
        },
        'text': {  # 'text': ["изменить🗃️", "создать🗃️", "сортировать🗃️", "удалить🗃️", "назад📋"],
            'switch': buttons_long['switch'] + emoji['groups'],
            'edit':   buttons_long['edit'] + emoji['groups'],
            'add':    buttons_long['add'] + emoji['groups'],
            # 'sort':   buttons_long['sort'] + emoji['groups'],
            'delete': buttons_long['delete'] + emoji['groups'],
            'back':   buttons_long['back'] + emoji['list']
        },
        'both': {  # 'both': ["✏️🗃️изм.", "➕🗃️созд.", "⬆⬇🗃️сорт.", "❌🗃️удал.", "↩️📋"]
            'switch': emoji['switch'] + emoji['groups'] + buttons_short['switch'],
            'edit':   emoji['edit'] + emoji['groups'] + buttons_short['edit'],
            'add':    emoji['add'] + emoji['groups'] + buttons_short['add'],
            # 'sort':   emoji['sort'] + emoji['groups'] + buttons_short['sort'],
            'delete': emoji['delete'] + emoji['groups'] + buttons_short['delete'],
            'back':   emoji['back'] + emoji['list'] + buttons_short['back']
        },
    }  # TODO: Доделать сортировку групп
    return buttons


async def groups_menu_keyboard_builder(telegram_user_id: int) -> ReplyKeyboardMarkup:
    options = await get_profiles_options_api(telegram_user_id)
    lang = options["telegram_language"]
    buttons = groups_menu_keyboard_buttons(lang)
    style = options["telegram_buttons_style"]
    builder = ReplyKeyboardBuilder()
    for button_text in buttons[style].values():
        builder.add(KeyboardButton(text=button_text))
    if style == list(buttons.keys())[0]:
        builder.adjust(6)
    else:
        builder.adjust(3)
    return builder.as_markup(resize_keyboard=True)
