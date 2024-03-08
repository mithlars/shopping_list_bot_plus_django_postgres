from aiogram.types import CallbackQuery
from aiogram import Router

from bot.api.django_auth import django_auth, update_last_request_time
from bot.business_processes.purchases.list_read_and_menu import ListRead
from bot.constants import django_address

purchases_delete_router = Router()


class PurchasesDeleteAPI:

    @staticmethod
    @update_last_request_time(django_auth)
    async def delete_purchase(telegram_user_id: int, purchase_id: int):
        url = f"{django_address}/purchases/detail/"
        data = {
            "telegram_user_id": telegram_user_id,
            "purchase_id": purchase_id
        }
        await django_auth.session.delete(url=url, data=data)


class PurchasesDelete:

    @staticmethod
    @purchases_delete_router.callback_query(lambda c: c.data and c.data.startswith('del_pur'))
    async def delete_purchase(callback: CallbackQuery):
        data = callback.data.split(" ")
        purchase_id = int(data[1])
        telegram_user_id = callback.from_user.id
        await PurchasesDeleteAPI.delete_purchase(telegram_user_id, purchase_id)
        await ListRead.get_current_lists_purchases_list(telegram_user_id)

