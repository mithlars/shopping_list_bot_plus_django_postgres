from aiogram import F, Router
from aiogram.types import Message, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from bot.create_bot import MyBot


class MainMenuKeyboard:

    @staticmethod
    async def main_menu_keyboard_builder():
        builder = ReplyKeyboardBuilder()
        builder.add(
            KeyboardButton(text="📦Lis"),  # Списки
            KeyboardButton(text="🗃️Gr"),  # ️Группы
            KeyboardButton(text="🗂️Cat"),  # ️Категории
            KeyboardButton(text="🛠️Conf"),  # Настройки
            KeyboardButton(text="↩️📋")  # Назад

        )
        builder.adjust(6)
        return builder.as_markup(resize_keyboard=True)


main_menu_router = Router()


class MainMenu:

    @staticmethod
    @main_menu_router.message(
        (F.text.startswith("☰")) |
        (F.text.startswith("↩️☰back")) |
        (F.text.startswith("↩️☰"))
    )
    async def main_menu_header(message: Message):
        user_id = message.from_user.id
        text = ("------\"Основное меню!------\n"
                "  Вы можете перейти в настройки списков, нажав \"📦Списки\", где можно создать "
                "новые списки, изменить имена и описания ранее созданных списков, сделать другой "
                "список активным, чтобы поработать в нем.\n"
                "  Или перейти в меню работы с группами (\"🗃️Группы\") или категориями \"🗂️Категории\""
                "и настроить иерархию позиций текущего списка\n"
                "  Для возврата в к работе с позициями текущего списка нажмите \"↩️Назад📋\", или "
                "отправьте текст новой позиции списка.\n")
        # " Так же Вы можете перейти в настройки параметров взаимодействия с ботом, нажав \"🛠️Настройки\".")
        keyboard = await MainMenuKeyboard.main_menu_keyboard_builder()
        await MyBot.bot.send_message(user_id, text, reply_markup=keyboard)
