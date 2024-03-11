from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.business_processes.groups.utils.groups_menu_keyboard import groups_menu_keyboard_buttons
from bot.constants import buttons_styles
from bot.create_bot import MyBot
from bot.translate import transl

group_edit_router = Router()


class GroupUpdateLineUpStart:

    @staticmethod
    async def group_road_split_keyboard():
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="Состав", callback_data="group_line_up"))
        builder.add(InlineKeyboardButton(text="Переименовать", callback_data="group_update"))
        keyboard = builder.as_markup(resize_keyboard=True)
        return keyboard

    @staticmethod
    @group_edit_router.message(
        lambda message:
        any(message.text == groups_menu_keyboard_buttons(lang)[button_style]['edit']
            for lang in transl.keys() for button_style in buttons_styles)
        # F.text == "✏️🗃️"
    )
    async def group_update_road_split_handler(message: Message):
        telegram_user_id = message.from_user.id
        message_text = "Что Вы хотите сделать?"
        keyboard = await GroupUpdateLineUpStart.group_road_split_keyboard()
        await MyBot.bot.send_message(chat_id=telegram_user_id, text=message_text, reply_markup=keyboard)
