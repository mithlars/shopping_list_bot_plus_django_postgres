from django.utils.datastructures import MultiValueDictKeyError
from rest_framework import permissions
from core.settings import TELEGRAM_BOT_USER_ID, TELEGRAM_BOT_IP
from .models import UserProfile


class IsTelegramUserOrIsUsersList(permissions.BasePermission):
    """
       Проверяет:
            Запрос от пользователя, который назначен для взаимодействия от имени телеграм-бота?
                Если да:
                    Проверяет ip, с которого отправлен запрос:
                        Если ip тот, на котором работает телеграм bot --
                            Проверяем авторизацию
                                Если да -- доступ предоставляется
                                Если нет -- доступ не предоставляется
                                    + сообщение в консоль.
                        Если ip не верный:
                            Отрабатывается тревога.
                            Доступ не предоставляется.
                Если другой пользователь:
                    Profile по user_id.
                    Проверяет есть ли в поле lists объекта Profile list, доступ к данным которого запрашивается.
                        Если есть -- доступ предоставляется.
                        Если нет -- доступ НЕ предоставляется.
    """
    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def has_permission(self, request, view):
        if request.user.id == TELEGRAM_BOT_USER_ID:
            client_ip = IsTelegramUserOrIsUsersList.get_client_ip(request)
            if client_ip == TELEGRAM_BOT_IP:
                # lists = []
                # try:
                #     profile = UserProfile.objects.get(telegram_user_id=request.data.get("telegram_user_id"))
                # except MultiValueDictKeyError:
                #     print("No telegram_id in request.data.")
                # lists = list(profile.lists.values_list('id', flat=True))

                # try:
                    # list_id = int(request.data.get('list_id'))

                    # if not (list_id in lists):
                    #     print(f"\nНе в свой список\n{lists = }\n{list_id = }")
                    #     return False
                # except Exception:  # TODO: Подобрать Exception class для request.data.get("list_id")
                #     print("No 'list_id' in request.query_params")
                #     return False
                if not request.user.is_authenticated:
                    print("\nНужна авторизация\n")
                    return False
                # print(f"{request.method} {request.get_full_path()} permissions is OK")
                return True
            else:
                # TODO: Тревога: Взломан TELEGRAM_BOT_USER!
                return False
        profile = UserProfile.objects.get(user=request.user.id)
        lists = list(profile.lists.values_list('id', flat=True))
        list_id = int(request.query_params.get("list_id"))
        return list_id in lists and request.user.is_authenticated


class TelegramIdProfileLists(permissions.BasePermission):
    """
        Проверяет:
            Запрос от пользователя, который назначен для взаимодействия от имени телеграм-бота?
                Если да:
                    Проверяет ip, с которого отправлен запрос:
                        Если ip тот, на котором работает телеграм bot:
                            Получаем Profile по telegram_id.
                            Проверяем, в поле lists объекта Profile есть list, доступ к данным которого запрашивается?
                                Если да -- доступ предоставляется.
                                Если нет -- отказ в доступе
                        Если ip не верный:
                            Отрабатывается тревога.
                            Доступ не предоставляется.
                Если другой пользователь -- доступ НЕ предоставляется.
    """
    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def has_permission(self, request, view):
        print(f"\nrequest.data:\n{request.data}\n")
        if request.user.id == TELEGRAM_BOT_USER_ID:
            client_ip = IsTelegramUserOrIsUsersList.get_client_ip(request)
            print(f"\nclient_ip: {client_ip}\n")
            if client_ip == TELEGRAM_BOT_IP:
                profile = UserProfile.objects.get(telegram_user_id=request.data["telegram_user_id"])
                lists = list(profile.lists.values_list('id', flat=True))
                print(f"\nTelegram profile:\n{profile}\n")
                return int(request.query_params.get("list_id")) in lists and request.user.is_authenticated
            else:
                # TODO: Тревога: Взломан TELEGRAM_BOT_USER!
                return False
        else:
            return False


class WebUserProfileLists(permissions.BasePermission):
    """
        Получает Profile по user_id.
        Проверяет есть ли в поле lists объекта Profile list, доступ к данным которого запрашивается.
            Если есть -- доступ предоставляется.
            Если нет -- доступ НЕ предоставляется.
    """
    def has_permission(self, request, view):
        profile = UserProfile.objects.get(user=request.user.id)
        lists = list(profile.lists.values_list('id', flat=True))
        return int(request.query_params.get("list_id")) in lists and request.user.is_authenticated
