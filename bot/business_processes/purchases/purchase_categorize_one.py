from typing import Tuple, Dict, Any

from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from requests import Response

from bot.api.django_auth import django_auth, update_last_request_time
from bot.business_processes.purchases.list_read_and_menu import ListRead
from bot.constants import django_address
from bot.create_bot import MyBot

purchase_categorize_one_router = Router()


class PurchaseCategorizeOneStart:

    @staticmethod
    async def data_processing(list_data: list) -> Tuple[str, InlineKeyboardMarkup]:
        message_text = ""
        number_count = 1
        builder = InlineKeyboardBuilder()
        for category_dict in list_data:
            category_name = category_dict["name"]
            purchases_list = category_dict["purchases"]
            if purchases_list:
                message_text += f"____{category_name}\n"
                for purchase_dict in purchases_list:
                    message_text += f"{number_count}. {purchase_dict['name']}"
                    purchase_description = purchase_dict.get('description', '')
                    if purchase_description != '' and purchase_description is not None:
                        message_text += f" ({purchase_description})\n"
                    else:
                        message_text += "\n"
                    callback_data = f"categorize_purchase {purchase_dict['id']} {category_dict['id']}"
                    builder.add(InlineKeyboardButton(text=f"{number_count}", callback_data=callback_data))
                    number_count += 1
        if message_text == "":
            message_text = "Список (категории группы) пока пуст(ы)."
        builder.add(InlineKeyboardButton(text="Отмена",
                                         callback_data=f"categorize_purchase stop stop"))
        keyboard = builder.as_markup(resize_keyboard=True)
        return message_text, keyboard

    @staticmethod
    @update_last_request_time(django_auth)
    async def get_purchase_choice_text_and_keyboard_api(telegram_user_id: int) -> Tuple[str, InlineKeyboardMarkup]:
        url = f"{django_address}/lists/list_or_group/"  # TODO: Что делать, если в группе нет blank-категории?
        data = {"telegram_user_id": telegram_user_id}
        response = django_auth.session.get(url=url, data=data)
        message_text, keyboard = await PurchaseCategorizeOneStart.data_processing(response.json())
        return message_text, keyboard

    @staticmethod
    async def categorize_choice(telegram_user_id: int):
        """
                Method is getting text with purchases and inline-keyboard to choose purchase for changing category for.
            and sending message to user with this text and keyboard
        """
        message_text, keyboard = await (PurchaseCategorizeOneStart.
                                        get_purchase_choice_text_and_keyboard_api(telegram_user_id))
        await MyBot.bot.send_message(chat_id=telegram_user_id, text=message_text, reply_markup=keyboard)

    @staticmethod
    @purchase_categorize_one_router.message(F.text == "➡️🗂️")
    async def categorize_one_start_handler(message: Message):
        telegram_user_id = message.from_user.id
        await PurchaseCategorizeOneStart.categorize_choice(telegram_user_id)


class PurchaseCategorizeChooseCategory:

    @staticmethod
    @update_last_request_time(django_auth)
    async def get_purchases_categories_api(telegram_user_id: int, purchase_id: str) -> list:
        url = f"{django_address}/purchases/categories/"  # TODO: url
        data = {
            "telegram_user_id": telegram_user_id,
            "purchase_id": purchase_id
        }
        response = django_auth.session.get(url=url, data=data)
        return response.json()['categories_ids']

    @staticmethod
    async def processing_categories_data(categories_list_data: list, purchase_id: str, category_from_id: str,
                                         telegram_user_id: int) -> Tuple[str, InlineKeyboardMarkup]:
        """
                Функция-parser, принимает ответ от Django, парсит его в текст сообщения
            со списком категорий и клавиатуру для выбора новой категории для выбранной позиции списка.
        """
        # Get list of categories for the purchase:
        purchases_categories_list = \
            await PurchaseCategorizeChooseCategory.get_purchases_categories_api(telegram_user_id, purchase_id)
        # Build message text and keyboard to choose list position to change category for:
        message_text = ""
        number_count = 1
        builder = InlineKeyboardBuilder()
        for category_dict in categories_list_data:
            # Excluding categories, where the purchase is in
            # from the list of categories message text and keyboard buttons:
            if category_dict['id'] not in purchases_categories_list:
                # Building next row of text:
                category_name = category_dict["name"]
                category_description = category_dict.get('description', '')
                message_text += f"{number_count}. {category_name}"
                if category_description != '' and category_description is not None:
                    message_text += f" ({category_description})\n"
                else:
                    message_text += "\n"
                # Adding next button to keyboard
                callback_data = f"categorize_with_1 start {category_dict['id']} {purchase_id} {category_from_id}"
                builder.add(InlineKeyboardButton(text=f"{number_count}", callback_data=callback_data))
                number_count += 1
        # Adding cancel button to keyboard:
        builder.add(InlineKeyboardButton(text="Отмена", callback_data=f"categorize_with_1 stop s s s"))
        keyboard = builder.as_markup(resize_keyboard=True)
        return message_text, keyboard

    @staticmethod
    @update_last_request_time(django_auth)
    async def categories_list_api(telegram_user_id: int, purchase_id: str, category_from_id: str
                                  ) -> Tuple[str, InlineKeyboardMarkup]:
        url = f"{django_address}/categories/"
        data = {"telegram_user_id": telegram_user_id}
        response = django_auth.session.get(url=url, data=data)
        message_text, keyboard = await PurchaseCategorizeChooseCategory.processing_categories_data(
            response.json(), purchase_id, category_from_id, telegram_user_id)
        return message_text, keyboard

    @staticmethod
    @purchase_categorize_one_router.callback_query(lambda c: c.data and c.data.startswith("categorize_purchase"))
    async def choose_category_handler(callback: CallbackQuery):
        telegram_user_id = callback.from_user.id
        purchase_id, category_from_id = callback.data.split(" ")[1:]
        if purchase_id == "stop":
            await MyBot.bot.send_message(chat_id=telegram_user_id, text="OK")
            await ListRead.get_current_lists_purchases_list(telegram_user_id)
        else:
            message_text, keyboard = await PurchaseCategorizeChooseCategory.categories_list_api(
                telegram_user_id, purchase_id, category_from_id)
            await MyBot.bot.send_message(chat_id=telegram_user_id, text=message_text, reply_markup=keyboard)


class PurchaseCategorize:

    @staticmethod
    async def del_or_keep_keyboard(category_id: str, purchase_id: str, category_from_id: str) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        data = f"{category_id} {purchase_id} {category_from_id}"
        builder.add(InlineKeyboardButton(text="Удалить", callback_data=f"categorize_with_2 del {data}"))
        builder.add(InlineKeyboardButton(text="Оставить", callback_data=f"categorize_with_2 keep {data}"))
        builder.add(InlineKeyboardButton(text="Отмена", callback_data=f"categorize_with_1 stop 0 0 0"))
        keyboard = builder.as_markup(resize_keyboard=True)
        return keyboard

    @staticmethod
    async def categorizing_api(telegram_user_id: int, category_id: str, purchase_id: str, category_from_id: str = None
                               ) -> Response:
        url = f"{django_address}/categories/purchases_update/"
        data = {
            "telegram_user_id": telegram_user_id,
            "category_to_id": category_id,
            "purchase_id": purchase_id,
            "category_from_id": category_from_id
        }
        response = await django_auth.session.put(url=url, data=data)
        return response

    @staticmethod
    @update_last_request_time(django_auth)
    async def get_blank_category_api(telegram_user_id: int) -> int:
        url = f"{django_address}/categories/get_blank/"
        data = {"telegram_user_id": telegram_user_id}
        response = django_auth.session.get(url=url, data=data)
        blank_category_id = response.json()["id"]
        return blank_category_id

    @staticmethod
    @purchase_categorize_one_router.callback_query(lambda c: c.data and c.data.startswith("categorize_with_1"))
    async def categorize_handler(callback: CallbackQuery):
        """
                Function handle inline-button choice in which category to put chosen position from the list.
                Check if previous category is blank one -- so call function to change category from blank to chosen,
            if previous is not blank so send message with question if user wants to keep for the list position link
            with previous category or delete it.
        """
        telegram_user_id = callback.from_user.id
        command, category_id, purchase_id, category_from_id = callback.data.split(" ")[1:]

        if command == "stop":
            await MyBot.bot.send_message(chat_id=telegram_user_id, text="OK")
            await ListRead.get_current_lists_purchases_list(telegram_user_id)

        elif command == 'start':
            # category_id, purchase_id, category_from_id = int(category_id), int(purchase_id), int(category_from_id)
            blank_category_id = await PurchaseCategorize.get_blank_category_api(telegram_user_id)
            if int(category_from_id) == blank_category_id:
                response = await PurchaseCategorize.categorizing_api(telegram_user_id, category_id,
                                                                     purchase_id, category_from_id)
                if response.status_code != 200:
                    await MyBot.bot.send_message(chat_id=telegram_user_id, text="Что-то пошло не так...")
                await ListRead.get_current_lists_purchases_list(telegram_user_id)
            else:
                keyboard = await PurchaseCategorize.del_or_keep_keyboard(category_id, purchase_id, category_from_id)
                message_text = f"Удалить позицию из предыдущей категории?"
                await MyBot.bot.send_message(chat_id=telegram_user_id, text=message_text, reply_markup=keyboard)

    @staticmethod
    @purchase_categorize_one_router.callback_query(lambda c: c.data and c.data.startswith("categorize_with_2"))
    async def categorize_del_or_keep__handler(callback: CallbackQuery):
        """
                Function handle inline-button choice about delete or keep link for list position with previous category
            and call change category function without or with previous category id.
            After changing category for the list position function calls whole list with delete inline-keyboard.
        """
        telegram_user_id = callback.from_user.id
        command, category_id, purchase_id, category_from_id = callback.data.split(" ")[1:]

        if command == 'del':
            response = await PurchaseCategorize.categorizing_api(telegram_user_id, category_id,
                                                                 purchase_id, category_from_id)
            if response.status_code != 200:
                await MyBot.bot.send_message(chat_id=telegram_user_id, text="Что-то пошло не так...")
            await ListRead.get_current_lists_purchases_list(telegram_user_id)

        else:
            response = await PurchaseCategorize.categorizing_api(telegram_user_id, category_id, purchase_id)
            if response.status_code != 200:
                await MyBot.bot.send_message(chat_id=telegram_user_id, text="Что-то пошло не так...")
            await ListRead.get_current_lists_purchases_list(telegram_user_id)
