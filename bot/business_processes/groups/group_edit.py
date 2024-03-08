from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.create_bot import MyBot

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
    @group_edit_router.message(F.text == "✏️🗃️")
    async def group_update_road_split_handler(message: Message):
        telegram_user_id = message.from_user.id
        message_text = "Что Вы хотите сделать?"
        keyboard = await GroupUpdateLineUpStart.group_road_split_keyboard()
        await MyBot.bot.send_message(chat_id=telegram_user_id, text=message_text, reply_markup=keyboard)
