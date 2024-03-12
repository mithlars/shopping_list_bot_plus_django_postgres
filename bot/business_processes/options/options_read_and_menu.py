from typing import Tuple

from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.api.django_auth import django_auth, update_last_request_time
from bot.business_processes.options.utils.get_profiles_options_api import get_profiles_options_api
from bot.business_processes.purchases.utils.list_menu_keyboard import list_menu_keyboard_buttons
from bot.constants import django_address, buttons_styles
from bot.create_bot import MyBot
from bot.emoji import emoji
from bot.translate import transl

options_router = Router()

"""
    
"""


class ShowOptionsMenu:
    """ class opens options menu looks like messages with inline-switchers """

    @staticmethod
    async def language_switch_menu(language: str) -> Tuple[str, InlineKeyboardMarkup]:
        """ function to switch language """
        # TODO: Переделать. Сделать так, чтобы список языков подтягивался автоматически для всей функции
        message_text_list = [
            "Выберите язык:",
            "1. 'bel', 'Беларуская'",
            "2. 'en', 'English'",
            "3. 'hy', 'Հայերեն'",
            "4. 'ru', 'Русски'",
            "5. 'uk', 'Українська'"
        ]
        if language == "bel":
            message_text_list[1] = f"*{message_text_list[1]}*"
        elif language == 'en':
            message_text_list[2] = f"*{message_text_list[2]}*"
        elif language == 'hy':
            message_text_list[3] = f"*{message_text_list[3]}*"
        elif language == 'ru':
            message_text_list[4] = f"*{message_text_list[4]}*"
        elif language == 'uk':
            message_text_list[5] = f"*{message_text_list[5]}*"
        message_text = "\n".join(message_text_list)

        builder = InlineKeyboardBuilder()
        builder.add(
            # InlineKeyboardButton(text="1", callback_data="switch_language bel"),
            InlineKeyboardButton(text="2", callback_data="switch_language en"),
            # InlineKeyboardButton(text="3", callback_data="switch_language hy"),
            InlineKeyboardButton(text="4", callback_data="switch_language ru"),
            # InlineKeyboardButton(text="5", callback_data="switch_language uk")
        )
        keyboard = builder.as_markup(resize_keyboard=True)
        return message_text, keyboard

    @staticmethod
    async def buttons_style_switcher_menu(telegram_buttons_style: str, lang: str
                                          ) -> Tuple[str, InlineKeyboardMarkup]:
        """ function to switch buttons style """
        message_text = transl[lang]['options']['buttons_style']['message']
        buttons = transl[lang]['list_menu']['buttons']
        buttons_short = transl[lang]['list_menu']['buttons_short']
        text_text = (f"⬜ "
                     f"[{buttons['groups']}] "
                     f"[{buttons['lists']}]")
        pics_text = "⬜ [🗃️] [📦]"
        both_text = (f"⬜ "
                     f"[🗃️{buttons_short['groups']}] "
                     f"[📦{buttons_short['lists']}]")
        if telegram_buttons_style == "text":
            text_text = (f"✅ "
                         f"[{buttons['groups']}] "
                         f"[{buttons['lists']}]")
        elif telegram_buttons_style == "pics":
            pics_text = "✅ [🗃️] [📦]"
        else:
            both_text = (f"✅ "
                         f"[🗃️{buttons_short['groups']}] "
                         f"[📦{buttons_short['lists']}]")
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(text=text_text, callback_data="buttons_style_switch text"),
            InlineKeyboardButton(text=pics_text, callback_data="buttons_style_switch pics"),
            InlineKeyboardButton(text=both_text, callback_data="buttons_style_switch both")
        )
        keyboard = builder.as_markup(resize_keyboard=True)
        return message_text, keyboard

    @staticmethod
    async def tips_switcher_menu(tips_on: bool, lang: str) -> Tuple[str, InlineKeyboardMarkup]:
        """ function to switch "show or hide tips" option """
        message_text = transl[lang]['options']['tips']['message']
        builder = InlineKeyboardBuilder()
        buttons = transl[lang]['options']['tips']['buttons_style']
        if tips_on:
            builder.add(InlineKeyboardButton(text=f"{emoji['on']} {buttons['show']}", callback_data="tips_switch 0"))
        else:
            builder.add(InlineKeyboardButton(text=f"{emoji['off']} {buttons['show']}", callback_data="tips_switch 1"))
        keyboard = builder.as_markup(resize_keyboard=True)
        return message_text, keyboard

    @staticmethod
    @options_router.message(
        lambda message:
        any(message.text == list_menu_keyboard_buttons(lang)[button_style]['options']
            for lang in transl.keys() for button_style in buttons_styles)
        )
    async def options_menu_handler(message: Message):
        telegram_user_id = message.from_user.id
        options = await get_profiles_options_api(telegram_user_id)

        # Tips option:
        # message_text, keyboard = await ShowOptionsMenu.tips_switcher_menu(options['telegram_tips'],
        #                                                                   options['telegram_language'])
        # await MyBot.bot.send_message(chat_id=telegram_user_id, text=message_text, reply_markup=keyboard)

        # Buttons style:
        message_text, keyboard = await ShowOptionsMenu.buttons_style_switcher_menu(options['telegram_buttons_style'],
                                                                                   options['telegram_language'])
        await MyBot.bot.send_message(chat_id=telegram_user_id, text=message_text, reply_markup=keyboard)

        # Language:
        message_text, keyboard = await ShowOptionsMenu.language_switch_menu(options['telegram_language'])
        await MyBot.bot.send_message(chat_id=telegram_user_id, text=message_text,
                                     reply_markup=keyboard, parse_mode='Markdown')


class SwitchOptions:

    @staticmethod
    @update_last_request_time(django_auth)
    async def options_switch_api(telegram_user_id: int, tips_switch_position: str = None,
                                 buttons_style: str = None, language_code: str = None):
        url = f"{django_address}/profiles/options/"
        data = {
            "telegram_user_id": telegram_user_id,
            "telegram_tips": tips_switch_position,
            "telegram_buttons_style": buttons_style,
            "telegram_language": language_code
        }
        await django_auth.session.put(url=url, data=data)

    @staticmethod
    @options_router.callback_query(lambda c: c.data and c.data.startswith("tips_switch "))
    async def switch_tips_option_handler(callback: CallbackQuery):
        telegram_user_id = callback.from_user.id
        message_id = callback.message.message_id
        options = await get_profiles_options_api(telegram_user_id)
        tips_switch_position = callback.data.split(" ")[1]
        if tips_switch_position == options['telegram_tips']:
            pass
        else:
            await SwitchOptions.options_switch_api(telegram_user_id=telegram_user_id,
                                                   tips_switch_position=tips_switch_position)

            options = await get_profiles_options_api(telegram_user_id)
            message_text, keyboard = await ShowOptionsMenu.tips_switcher_menu(options['telegram_tips'],
                                                                              options['telegram_language'])
            await MyBot.bot.edit_message_reply_markup(chat_id=telegram_user_id,
                                                      message_id=message_id,
                                                      reply_markup=keyboard)

    @staticmethod
    @options_router.callback_query(lambda c: c.data and c.data.startswith("buttons_style_switch "))
    async def switch_buttons_style_handler(callback: CallbackQuery):
        telegram_user_id = callback.from_user.id
        message_id = callback.message.message_id
        options = await get_profiles_options_api(telegram_user_id)
        buttons_style = callback.data.split(" ")[1]
        if buttons_style == options['telegram_buttons_style']:
            pass
        else:
            await SwitchOptions.options_switch_api(telegram_user_id=telegram_user_id, buttons_style=buttons_style)

            options = await get_profiles_options_api(telegram_user_id)
            message_text, keyboard = \
                await ShowOptionsMenu.buttons_style_switcher_menu(options['telegram_buttons_style'],
                                                                  options['telegram_language'])
            await MyBot.bot.edit_message_reply_markup(chat_id=telegram_user_id,
                                                      message_id=message_id,
                                                      reply_markup=keyboard)

    @staticmethod
    @options_router.callback_query(lambda c: c.data and c.data.startswith("switch_language "))
    async def switch_language_handler(callback: CallbackQuery):
        telegram_user_id = callback.from_user.id
        message_id = callback.message.message_id
        options = await get_profiles_options_api(telegram_user_id)
        language_code = callback.data.split(" ")[1]
        if language_code == options['telegram_language']:
            pass
        else:
            await SwitchOptions.options_switch_api(telegram_user_id=telegram_user_id, language_code=language_code)

            options = await get_profiles_options_api(telegram_user_id)
            message_text, keyboard = await ShowOptionsMenu.language_switch_menu(options['telegram_language'])
            await MyBot.bot.edit_message_text(chat_id=telegram_user_id, message_id=message_id,
                                              text=message_text, parse_mode='Markdown')
            await MyBot.bot.edit_message_reply_markup(chat_id=telegram_user_id,
                                                      message_id=message_id,
                                                      reply_markup=keyboard)
