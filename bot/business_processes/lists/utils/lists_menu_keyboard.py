from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from bot.emoji import emoji
from bot.translate import transl

from bot.business_processes.options.utils.get_profiles_options_api import get_profiles_options_api


async def lists_menu_keyboard(telegram_user_id: int) -> ReplyKeyboardMarkup:
    options = await get_profiles_options_api(telegram_user_id)
    lang = options["telegram_language"]
    buttons = transl[lang]['lists_menu']['buttons']
    buttons_short = transl[lang]['lists_menu']['buttons_short']
    buttons = {
        'pics': [  # 'pics': ["🔀📦", "✏️️📦", "➕📦", "👨‍👦‍👦‍", "📦❌", "📦🧹", "↩️📋"],
            emoji['switch'] + emoji['lists'],
            emoji['edit'] + emoji['lists'],
            emoji['add'] + emoji['lists'],
            emoji['share'],
            emoji['lists'] + emoji['delete'],
            emoji['lists'] + emoji['clean'],
            emoji['back'] + emoji['list']
        ],
        'text': [  # 'text': ["сменить📦", "изменить📦", "создать📦", "доступ", "удалить📦", "очистить📦", "назад"],
            buttons['switch'] + emoji['lists'],
            buttons['edit'] + emoji['lists'],
            buttons['add'] + emoji['lists'],
            buttons['share'],
            buttons['delete'] + emoji['lists'],
            buttons['clean'] + emoji['lists'],
            buttons['back'] + emoji['list']
        ],
        'both': [  # 'both': ["🔀📦обн.", "✏️️📦изм.", "➕📦созд.", "👨‍👦‍👦‍дост.", "📦❌удал.", "📦🧹очис.", "↩️📋"]
            emoji['switch'] + emoji['lists'] + buttons_short['switch'],
            emoji['edit'] + emoji['lists'] + buttons_short['edit'],
            emoji['add'] + emoji['lists'] + buttons_short['add'],
            emoji['share'] + buttons_short['share'],
            emoji['lists'] + emoji['delete'] + buttons_short['delete'],
            emoji['lists'] + emoji['clean'] + buttons_short['clean'],
            emoji['back'] + emoji['list'] + buttons_short['back']
        ],
    }

    style = options["telegram_buttons_style"]
    builder = ReplyKeyboardBuilder()
    for button_text in buttons[style]:
        builder.add(KeyboardButton(text=button_text))
    builder.adjust(4)
    return builder.as_markup(resize_keyboard=True)