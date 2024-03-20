import asyncio
import logging

from aiogram.utils.i18n import I18n

from bot.business_processes.categories.categories_sort import categories_sort_router
from bot.business_processes.categories.category_add import category_add_router
from bot.business_processes.categories.category_delete import categories_delete_router
from bot.business_processes.categories.category_purify import category_purify_router
from bot.business_processes.categories.category_update import category_update_router
from bot.business_processes.groups.group_add import group_add_router
from bot.business_processes.groups.group_change_current import group_change_current_router
from bot.business_processes.groups.group_delete import group_delete_router
from bot.business_processes.groups.group_line_up import group_lineup_router
from bot.business_processes.groups.group_edit import group_edit_router
from bot.business_processes.groups.group_update import group_update_router
from bot.business_processes.lists.list_change_current import list_change_current_router
from bot.business_processes.lists.list_create import list_create_router
from bot.business_processes.lists.list_delete import list_delete_router
from bot.business_processes.lists.list_update import list_update_router
from bot.business_processes.lists.lists_share_and_menu import lists_share_router
from bot.archive.main_menu import main_menu_router
from bot.business_processes.options.options_read_and_menu import options_router
from bot.business_processes.purchases.purchase_add import purchases_add_router
from bot.business_processes.purchases.purchase_categorize_one import purchase_categorize_one_router
from bot.business_processes.purchases.purchase_uncategorize_one import purchase_uncategorize_one_router
from bot.business_processes.purchases.purchase_update import purchase_update_router
from bot.business_processes.user.manage_friends import manage_friends_router
from bot.middlewares import LanguageMiddleware
from constants import admin_telegram_id, startup_admin_message
from bot.api.django_auth import django_auth
from create_bot import MyBot
from aiogram import Bot
from bot.business_processes.purchases.purchases_delete_and_list_menu import purchases_delete_and_list_menu
from bot.business_processes.user.user_create_start import start_router


async def on_startup(bot: Bot):
    await bot.send_message(chat_id=admin_telegram_id, text=startup_admin_message)


async def main():

    # Авторизация бота в django:

    loop = asyncio.get_event_loop()
    try:
        await django_auth.login()
    except Exception as er:
        print(f"Авторизация провалилась\n {er}")
    # loop.run_until_complete(await django_auth.login())  # Авторизуемся при запуске бота
    loop.create_task(django_auth.refresh_session())

    # Register startup hook to initialize webhook
    MyBot.dp.startup.register(on_startup)

    i18n = I18n(path="locales", default_locale="en", domain="messages")
    my_i18n_middleware = LanguageMiddleware(i18n)
    MyBot.dp.update.middleware.register(my_i18n_middleware)

    # Register routers:
    MyBot.dp.include_routers(
        start_router,
        main_menu_router,
        manage_friends_router,
        options_router,

        list_change_current_router,
        purchases_delete_and_list_menu,
        list_create_router,
        list_update_router,
        list_delete_router,
        lists_share_router,

        group_change_current_router,
        group_add_router,
        group_delete_router,
        group_edit_router,
        group_lineup_router,
        group_update_router,

        category_add_router,
        category_update_router,
        categories_sort_router,
        categories_delete_router,
        category_purify_router,

        purchase_update_router,
        purchase_categorize_one_router,
        purchase_uncategorize_one_router,
        purchases_add_router,
    )

    # To skip pending updates:
    await MyBot.bot.delete_webhook(drop_pending_updates=True)

    # Start bot:
    await MyBot.dp.start_polling(MyBot.bot, loop=loop)


if __name__ == "__main__":
    # Включаем логирование, чтобы не пропустить важные сообщения
    logging.basicConfig(level=logging.INFO)

    # Start:
    asyncio.run(main())
