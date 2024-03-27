from typing import Any, Dict

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.api.django_auth import django_auth, update_last_request_time
from bot.business_processes.purchases.purchase_delete_and_list_menu import ListRead
from bot.constants import django_address
from bot.create_bot import MyBot

from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __

from bot.emoji import emoji

start_router = Router()

purchases_add_router = Router()


class StatesAddPurchases(StatesGroup):
    categorize = State()


class PurchasesGetAndCategorize:
    """
            Класс состоит из handler-функций и несколькими сопутствующими им функциями.
        Handler-функции обрабатывают сообщение с перечнем новых позиций для списка,
        выводят inline-клавиатуру для выбора категорий для всех полученных позиций,
        или для каждой в отдельности. По результату выбора категорий формируют data
        и отправляют для создания новых позиция в функции предыдущего класса PurchaseAdd.
    """

    @staticmethod
    async def parsing_purchases_details(message_text: str) -> list:
        list_of_purchases = []
        purchase_data_list = message_text.splitlines()
        for purchase_str in purchase_data_list:
            purchase_dict = {}
            purchase_data = purchase_str.split("." or ":" or ";")
            purchase_name = purchase_data[0].strip().lower().capitalize()
            purchase_dict["name"] = purchase_name
            if len(purchase_data) > 1:
                purchase_description = purchase_data[1].strip().lower()
                purchase_dict["description"] = purchase_description
            list_of_purchases.append(purchase_dict)
        return list_of_purchases

    @staticmethod
    @update_last_request_time(django_auth)
    async def gat_categories_api(telegram_user_id: int) -> list:
        print()
        url = f"{django_address}/categories/"
        data = {"telegram_user_id": telegram_user_id}
        response = django_auth.session.get(url=url, data=data)
        return response.json()

    @staticmethod
    async def categorize_keyboard_builder(status: str, categories: list) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        for category in categories:
            callback_data = f"categorize;{category['id']};{status}"
            builder.add(InlineKeyboardButton(text=category['name'], callback_data=callback_data))
        builder.add(InlineKeyboardButton(text=emoji['delete'] + _("Cancel"),
                                         callback_data=emoji['add'] + emoji['list'] + _("Cancel")))
        if status == 'same':
            builder.add(InlineKeyboardButton(text="Разные", callback_data="categorize;dif;dif"))
        else:
            builder.add(InlineKeyboardButton(text="Потом", callback_data="categorize;dif;later"))
            if status != "remaining":
                builder.add(InlineKeyboardButton(text="Остальные", callback_data="categorize;dif;remaining"))
        builder.adjust(3)
        return builder.as_markup(resize_keyboard=True)

    @staticmethod
    @purchases_add_router.message(F.text)
    async def purchases_add_handler(message: Message, state: FSMContext):
        telegram_user_id = message.from_user.id
        # Starting state, adding to state.data message text, parsed to positions data:
        non_categorized_purchases_list = await PurchasesGetAndCategorize.parsing_purchases_details(message.text)
        categories = await PurchasesGetAndCategorize.gat_categories_api(telegram_user_id)
        if len(categories) > 1:
            await state.set_state(StatesAddPurchases.categorize)

            await state.update_data(data={
                "non_categorized_purchases_list": non_categorized_purchases_list,
                "categorized_purchases_list": []
            })
            # Getting the keyboard to select category:
            categorize_keyboard = await PurchasesGetAndCategorize.categorize_keyboard_builder(
                status="same",
                categories=categories
            )
            # Sending message with category selecting keyboard:
            text = "Выберите категорию"
            await MyBot.bot.send_message(chat_id=telegram_user_id, text=text, reply_markup=ReplyKeyboardRemove())
            await MyBot.bot.send_message(chat_id=telegram_user_id, text="из списка:", reply_markup=categorize_keyboard)
        else:
            await Categorize.same_category_for_all(categories[0]['id'], non_categorized_purchases_list, telegram_user_id)

    @staticmethod
    @purchases_add_router.callback_query(
        lambda c: c.data and c.data.replace(f"{emoji['add']}{emoji['list']}", "") == __("Cancel"))
    async def cansel_categorize_handler(callback: CallbackQuery, state: FSMContext):
        telegram_user_id = callback.from_user.id
        await state.clear()
        await MyBot.bot.send_message(telegram_user_id, _("OK, inputted data is deleted"))
        await ListRead.get_current_lists_purchases_list(telegram_user_id)

    @staticmethod
    @purchases_add_router.callback_query(StatesAddPurchases.categorize)
    async def categorize_handler(callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        telegram_user_id = callback.from_user.id
        category_id, status = callback.data.split(";")[1:]
        non_categorized_purchases_list = data["non_categorized_purchases_list"]
        categorized_purchases_list = data["categorized_purchases_list"]

        # All in one category:
        if status == "same":
            await Categorize.same_category_for_all(
                category_id,
                non_categorized_purchases_list,
                telegram_user_id,
                state
            )

        # Different categories and NOT all purchases are selected category:
        # All remaining in blank_category to categorize later
        elif status == "later":
            await Categorize.later_all_in_blank(
                non_categorized_purchases_list,
                categorized_purchases_list,
                state,
                telegram_user_id
            )

        # Categorizing all remaining to one category
        elif status == "remaining":
            await Categorize.remaining_in_one(
                category_id,
                non_categorized_purchases_list,
                categorized_purchases_list,
                state,
                status,
                telegram_user_id
            )

        # Separate categorizing
        else:
            await Categorize.separate_categorizing(
                category_id,
                non_categorized_purchases_list,
                categorized_purchases_list,
                state,
                status,
                telegram_user_id
            )


class Categorize:
    """
            Класс содержит функционал, вынесенный из функции categorize_handler класса
        PurchasesGetAndCategorize. В каждой функции идет обработка кнопок
        inline-клавиатуры выбора категорий и метода категоризации позиций
        (все вместе, по отдельности, все оставшиеся).

            Финал работы этих функций -- формирование data с именами, описаниями и категориями
        и передача data функции add_purchases класса PurchaseAdd для создания позиций в
        базе данных.
    """

    @staticmethod
    async def separate_categorizing(
            category_id: str | int,
            non_categorized_purchases_list: list,
            categorized_purchases_list: list,
            state: FSMContext,
            status: str,
            telegram_user_id: int
    ):
        if len(non_categorized_purchases_list) > 1:
            # If NOT first step categorizing process
            if category_id != "dif":
                # Categorize one from end of the list
                non_categorized_purchases_list[-1]['category_id'] = category_id
                # Replace categorized purchase to spacial list
                categorized_purchases_list.append(non_categorized_purchases_list.pop())

            text = _("Choose category for new list position\n{purchase_name}:"
                     ).format(purchase_name=non_categorized_purchases_list[-1]['name'])
            categorize_keyboard = await PurchasesGetAndCategorize.categorize_keyboard_builder(telegram_user_id, status)
            # Next step of categorizing:
            await MyBot.bot.send_message(chat_id=telegram_user_id, text=text, reply_markup=categorize_keyboard)

        # Different categories and for all purchases are selected category:
        # Last step of separate categorizing
        elif len(non_categorized_purchases_list) == 1:
            non_categorized_purchases_list[0]['category_id'] = category_id  # Categorize one from end of the list
            categorized_purchases_list.append(non_categorized_purchases_list.pop())  # Replace categorized purchase
            await state.clear()
            await PurchaseAdd.add_purchases(categorized_purchases_list, telegram_user_id)

    @staticmethod
    async def remaining_in_one(
            category_id: str | int,
            non_categorized_purchases_list: list,
            categorized_purchases_list: list,
            state: FSMContext,
            status: str,
            telegram_user_id: int
    ):
        if category_id == "dif":
            text = _("Choose category for other new list positions ")
            for purchase in non_categorized_purchases_list:
                text += f"{purchase['name']}"
                purchase_description = purchase.get('description', "")
                if purchase_description != '':
                    text += f" ({purchase_description})\n"
                else:
                    text += '\n'
            categorize_keyboard = \
                await PurchasesGetAndCategorize.categorize_keyboard_builder(telegram_user_id, status)
            await MyBot.bot.send_message(chat_id=telegram_user_id, text=text, reply_markup=categorize_keyboard)
        else:
            for i in range(len(non_categorized_purchases_list)):
                non_categorized_purchases_list[i]['category_id'] = category_id
            await state.clear()
            await PurchaseAdd.add_purchases(
                purchases_list=(non_categorized_purchases_list + categorized_purchases_list),
                telegram_user_id=telegram_user_id
            )

    @staticmethod
    @update_last_request_time(django_auth)
    async def get_blank_category_api(telegram_user_id: int) -> Dict[str, Any]:
        url = f"{django_address}/categories/get_blank/"
        data = {"telegram_user_id": telegram_user_id}
        response = django_auth.session.get(url=url, data=data)
        return response.json()

    @staticmethod
    async def later_all_in_blank(
            non_categorized_purchases_list: list,
            categorized_purchases_list: list,
            state: FSMContext,
            telegram_user_id: int
    ):
        blank_category = await Categorize.get_blank_category_api(telegram_user_id)
        for i in range(len(non_categorized_purchases_list)):
            non_categorized_purchases_list[i]['category_id'] = blank_category['id']
        await state.clear()
        await PurchaseAdd.add_purchases(
            purchases_list=(non_categorized_purchases_list + categorized_purchases_list),
            telegram_user_id=telegram_user_id
        )

    @staticmethod
    async def same_category_for_all(
            category_id: int,
            non_categorized_purchases_list: list,
            telegram_user_id: int,
            state: FSMContext = None
    ):
        category_id = int(category_id)
        # Categorize all:
        for i in range(len(non_categorized_purchases_list)):
            non_categorized_purchases_list[i]['category_id'] = category_id
        # Add new purchases and read all list:
        if state:
            await state.clear()
        await PurchaseAdd.add_purchases(non_categorized_purchases_list, telegram_user_id)


class PurchaseAdd:
    """
            Класс содержит методы финальной стадии добавления новых позиций в список.
        На них отправка запроса на создание новых позиций в базе данных, формирование
        и отправка ответного сообщения, вызов функции, выводящей список, уже с новыми
        позициями.
    """

    @staticmethod
    async def purchases_data_processing(data: Dict[str, Any]) -> str:
        message_text = ""

        # Add to message_text added purchases, grouped by categories:
        number = 1
        if data['added'] == {}:
            message_text += _("All of this positions are already in the list\n")
        else:
            message_text += _("Positions which added to the list:\n")
            for category_name in data['added'].keys():
                message_text += f"____{category_name}\n"
                for purchase in data['added'][f"{category_name}"]:
                    message_text += f"{number}. {purchase['name']}"
                    if purchase['description']:
                        message_text += f" ({purchase['description']})\n"
                    else:
                        message_text += "\n"
                    number += 1

        # Add to message_text existed purchases, grouped by categories:
        number = 1
        if data['existed'] != {}:
            if data['added'] != {}:
                message_text += _("\nThe following positions are already in the list\n")
            for category_name in data['existed'].keys():
                message_text += f"____{category_name}\n"
                for purchase in data['existed'][f'{category_name}']:
                    message_text += f"{number}. {purchase['name']}"
                    number += 1
                    description = purchase.get('description', '')
                    if description != "":
                        message_text += f" ({description})\n"
                    else:
                        message_text += "\n"
        return message_text

    @staticmethod
    @update_last_request_time(django_auth)
    async def purchases_add_api(data: Dict[str, Any]) -> str:
        url = f"{django_address}/purchases/add/"
        response = await django_auth.session.post(url=url, data=data)
        message_text = await PurchaseAdd.purchases_data_processing(data=response.json())
        return message_text

    @staticmethod
    async def add_purchases(purchases_list: list, telegram_user_id):
        data = {
            "telegram_user_id": telegram_user_id,
            'purchases': str(purchases_list)
        }
        text = await PurchaseAdd.purchases_add_api(data)
        await MyBot.bot.send_message(chat_id=telegram_user_id, text=text)
        await ListRead.get_current_lists_purchases_list(telegram_user_id)