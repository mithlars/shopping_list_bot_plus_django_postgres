import ast
import datetime
import json
import os
import pprint
from time import time
from typing import Any, Dict
from urllib.parse import parse_qs

from django.contrib.auth.models import User
from django.core import serializers
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import generics, views

from core.settings import TELEGRAM_BOT_USER_ID
from .models import Categories, Lists, Purchases, UserProfile, Groups
from .serializers import (
    CategoriesPrefetchSerializer,
    CategoriesListSerializer,
    CategoryAddSerializer,
    PurchaseAddSerializer,
    CategoriesDitailSerializer, ListSerializer, UserProfileTelegramDitailSerializer, GroupsSerializer,
    GroupPrefetchSerializer
)
from django.db.models.query import QuerySet

from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Max

from list.permissions import IsTelegramUserOrIsUsersList

from django.views.generic import CreateView
from django.views import View
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login


# TODO: Добавить: Создание категории "Без категории" и добавление ее id в соответствующее поле.
class ListCreate(views.APIView):
    pass


class ListView(generics.ListAPIView):
    """
    View для вывода всех категорий списка со списком покупок.
    То есть весь список целиком
    """
    serializer_class = CategoriesPrefetchSerializer
    permission_classes = [IsTelegramUserOrIsUsersList]

    def get_queryset(self):
        """
            Берем List_id из ссылки.
            Фильтруем queryset по List_id и подтягиваем объекты 'purchases'
        """
        list_id = self.request.data.get('list_id')
        if list_id is not None:
            list_obj = Lists.objects.get(id=list_id)
        else:
            telegram_user_id = self.request.data["telegram_user_id"]
            profile = UserProfile.objects.get(telegram_user_id=telegram_user_id)
            list_obj = profile.telegram_current_list
        queryset = (Categories.objects.filter(list=list_obj).prefetch_related("purchases"))
        if isinstance(queryset, QuerySet):
            # Ensure queryset is re-evaluated on each request.
            queryset = queryset.all()
        return queryset


class ListOrGroupView(generics.ListAPIView):
    """
    View для вывода всех категорий списка со списком покупок.
    То есть весь список целиком
    """
    serializer_class = CategoriesPrefetchSerializer
    permission_classes = [IsTelegramUserOrIsUsersList]

    def get_queryset(self):
        """
            Фильтруем queryset категорий по current_group, а если его нет -- по current_list
            и подтягиваем объекты 'purchases' и 'list'
        """
        telegram_user_id = self.request.data["telegram_user_id"]
        profile = UserProfile.objects.get(telegram_user_id=telegram_user_id)
        list_obj = profile.telegram_current_list
        current_group = list_obj.telegram_current_group
        if current_group is None:
            queryset = (Categories.objects.filter(list=list_obj).
                        prefetch_related("purchases"))
        else:
            queryset = (Categories.objects.filter(groups=current_group).
                        prefetch_related("purchases"))
        if isinstance(queryset, QuerySet):
            # Ensure queryset is re-evaluated on each request.
            queryset = queryset.all()
        return queryset


class ListDitailView(views.APIView):
    """
        View-класс для получения имени списка.
    """

    permission_classes = [IsTelegramUserOrIsUsersList]

    @staticmethod
    def get(request):
        list_id = request.data.get('list_id', None)
        if list_id is not None:
            try:
                list_obj = Lists.objects.get(id=list_id)
            except Lists.DoesNotExist:
                return Response(data={"error": "List not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            try:
                profile = UserProfile.objects.get(telegram_user_id=request.data['telegram_user_id'])
            except UserProfile.DoesNotExist:
                return Response("UserProfile not found", status=status.HTTP_404_NOT_FOUND)
            list_obj = profile.telegram_current_list
        data = ListSerializer(list_obj).data
        return Response(data, status=status.HTTP_200_OK)

    @staticmethod
    def delete(request):
        telegram_user_id = request.data['telegram_user_id']
        list_id = int(request.data['list_id'])
        try:
            list_obj = Lists.objects.get(id=list_id)
        except Lists.DoesNotExist:
            return Response(data={"error": "List not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            profile = UserProfile.objects.get(telegram_user_id=telegram_user_id)
        except UserProfile.DoesNotExist:
            return Response(data={"error": "UserProfile not found."}, status=status.HTTP_404_NOT_FOUND)
        # Проверяем, является ли пользователь владельцем списка:
        if profile.id != list_obj.owner.id:
            # Если нет -- не удаляем список, а только удаляем его из списка доступов:
            profile.lists.remove(list_obj)
            return Response({"message": "OK"}, status=status.HTTP_200_OK)
        # Получаем список id списков, к которым у пользователя есть доступ:
        users_lists = profile.lists.all()
        users_lists_list = serializers.serialize('python', users_lists)
        # Проверяем, есть ли у пользователя доступ к спискам, кроме удаляемого:
        if len(users_lists_list) > 1:
            current_list_id = profile.telegram_current_list.id
            # Проверяем, совпадает ли удаляемый список с текущим:
            if current_list_id == list_id:
                lists_ids_list = [l_dict['pk'] for l_dict in users_lists_list]
                # Переключаем текущий на первый, не совпадающий с удаляемым:
                for i in range(len(lists_ids_list)):
                    if lists_ids_list[i] != list_id:
                        new_current_list = Lists.objects.get(id=lists_ids_list[i])
                        profile.telegram_current_list = new_current_list
                        profile.save()
                        break
            # Удаляем список:
            list_obj.delete()
            return Response({"message": "OK"}, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)


class GroupsView(generics.ListAPIView):
    """ View возвращает список групп без информации о связанных объектах. """
    permission_classes = {IsTelegramUserOrIsUsersList}
    serializer_class = GroupsSerializer

    def get_queryset(self):
        telegram_user_id = self.request.data.get('telegram_user_id')
        profile = UserProfile.objects.get(telegram_user_id=telegram_user_id)
        current_list = profile.telegram_current_list
        queryset = Groups.objects.filter(list=current_list)
        if isinstance(queryset, QuerySet):
            # Ensure queryset is re-evaluated on each request.
            queryset = queryset.all()
        return queryset


class GroupGetCurrentView(views.APIView):
    """ View for return current group for user's current list if it exists, or return None """
    permission_classes = [IsTelegramUserOrIsUsersList]

    @staticmethod
    def get(request):
        telegram_user_id = request.data["telegram_user_id"]
        try:
            profile = UserProfile.objects.get(telegram_user_id=telegram_user_id)
        except UserProfile.DoesNotExist:
            return Response(data={"error": "UserProfile not found."}, status=status.HTTP_404_NOT_FOUND)
        current_list = profile.telegram_current_list
        current_group = current_list.telegram_current_group
        if current_group is not None:
            current_group_id = current_group.id
        else:
            current_group_id = -1
        print(f"{current_group = }")
        return Response({"current_group": current_group_id}, status=status.HTTP_200_OK)


class GroupChangeCurrentView(views.APIView):
    permission_classes = [IsTelegramUserOrIsUsersList]

    @staticmethod
    def put(request):
        telegram_user_id = request.data['telegram_user_id']
        new_current_group_id = request.data['new_current_group_id']
        try:
            profile = UserProfile.objects.get(telegram_user_id=telegram_user_id)
        except UserProfile.DoesNotExist:
            return Response(data={"error": "UserProfile not found."}, status=status.HTTP_404_NOT_FOUND)
        current_list = profile.telegram_current_list
        current_list.telegram_current_group_id = new_current_group_id
        current_list.save()
        return Response(status=status.HTTP_200_OK)


class GroupsPrefetchView(generics.ListAPIView):
    """ View возвращает список групп с категориями и информацией о списке. """
    permission_classes = {IsTelegramUserOrIsUsersList}
    serializer_class = GroupPrefetchSerializer

    def get_queryset(self):
        telegram_user_id = self.request.data.get('telegram_user_id')
        profile = UserProfile.objects.get(telegram_user_id=telegram_user_id)
        current_list = profile.telegram_current_list
        queryset = Groups.objects.filter(list=current_list).prefetch_related("categories")
        if isinstance(queryset, QuerySet):
            # Ensure queryset is re-evaluated on each request.
            queryset = queryset.all()
        return queryset


class GroupDitailView(views.APIView):
    """

    """
    permission_classes = [IsTelegramUserOrIsUsersList]

    @staticmethod
    def post(request):
        try:
            profile = UserProfile.objects.get(telegram_user_id=request.data['telegram_user_id'])
        except UserProfile.DoesNotExist:
            return Response({"error": "UserProfile not found."}, status=status.HTTP_404_NOT_FOUND)
        list_id = profile.telegram_current_list.id
        data = {  # TODO: Переделать сериализатор так, чтобы list_id был получен на уровне сериализатора
            'name': request.data['name'],
            'description': request.data['description'],
            'list': list_id,
            'order_number': request.data['order_number']
        }
        serializer = GroupsSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def get(request):
        group_id = request.data.get('group_id')
        try:
            group = Groups.objects.get(id=group_id)
        except Groups.DoesNotExist:
            return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)
        group_serializer = GroupPrefetchSerializer(group)
        return Response(group_serializer.data, status=status.HTTP_200_OK)

    @staticmethod
    def put(request):
        try:
            group = Groups.objects.get(id=request.data['group_id'])
        except Groups.DoesNotExist:
            return Response({"error": "Group not found"}, status=status.HTTP_404_NOT_FOUND)
        group.name = request.data['name']
        group.description = request.data['description']
        group.save()
        group_serializer = GroupsSerializer(group)
        return Response(data=group_serializer.data, status=status.HTTP_200_OK)

    @staticmethod
    def delete(request):
        try:
            group = Groups.objects.get(id=request.data['group_id'])
        except Groups.DoesNotExist:
            return Response({"error": "Group not found"}, status=status.HTTP_404_NOT_FOUND)
        categories = group.categories.all()
        if len(categories) == 0:
            group.delete()
            group_serializer = GroupsSerializer(group)
            return Response(group_serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(data={"error": "group is not empty"},
                            status=status.HTTP_406_NOT_ACCEPTABLE)


class GroupGetNextOrderNumberView(views.APIView):
    """
        Get next empty order number for a new category.
    """
    permission_classes = [IsTelegramUserOrIsUsersList]

    @staticmethod
    def get(request):
        try:
            profile = UserProfile.objects.get(telegram_user_id=request.data['telegram_user_id'])
        except UserProfile.DoesNotExist:
            return Response({"error": "UserProfile not found."}, status=status.HTTP_404_NOT_FOUND)
        current_list = profile.telegram_current_list
        order_number = Groups.objects.filter(list=current_list).aggregate(Max('order_number'))['order_number__max']
        if order_number is None:
            order_number = 0
        return Response({"order_number": order_number + 1})


class GroupSortMoveView(views.APIView):
    """

    """
    permission_classes = [IsTelegramUserOrIsUsersList]

    @staticmethod
    def put(request):
        pass


class GroupPurifyView(views.APIView):
    """

    """
    permission_classes = [IsTelegramUserOrIsUsersList]

    @staticmethod
    def put(request):
        pass


class GroupCategoriesUpdateView(views.APIView):
    """

    """
    permission_classes = [IsTelegramUserOrIsUsersList]

    @staticmethod
    def put(request):
        category_id = request.data['category_id']
        group_id = request.data['group_id']
        move = request.data['move']
        try:
            group = Groups.objects.get(id=group_id)
        except Groups.DoesNotExist:
            return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            if move == "include":
                group.categories.add(category_id)
            else:
                group.categories.remove(category_id)
        except Categories.DoesNotExist:
            return Response({"error": "Category mot found."}, status=status.HTTP_404_NOT_FOUND)

        group.save()
        return Response({"message": "OK"}, status=status.HTTP_200_OK)


class GroupCategoriesView(views.APIView):
    """
        Returns list of group's categories.
    """
    permission_classes = [IsTelegramUserOrIsUsersList]

    @staticmethod
    def get(request):
        group_id = request.data['group_id']
        try:
            group = Groups.objects.get(id=group_id)
        except Groups.DoesNotExist:
            return Response("Group not found", status=status.HTTP_404_NOT_FOUND)
        categories_ids = group.categories.all().values_list('id', flat=True)
        return Response({"list": categories_ids}, status=status.HTTP_200_OK)


class GetBlankCategoryView(views.APIView):
    permission_classes = [IsTelegramUserOrIsUsersList]

    @staticmethod
    def get(request):
        try:
            profile = UserProfile.objects.get(telegram_user_id=request.data['telegram_user_id'])
        except UserProfile.DoesNotExist:
            return Response("UserProfile not found", status=status.HTTP_404_NOT_FOUND)
        blank_category = profile.telegram_current_list.blank_category
        serializer = CategoriesListSerializer(blank_category)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CategoriesGetNextOrderNumberView(views.APIView):
    """
        Get next empty order number for a new category.
    """
    permission_classes = [IsTelegramUserOrIsUsersList]

    @staticmethod
    def get(request):
        try:
            profile = UserProfile.objects.get(telegram_user_id=request.data['telegram_user_id'])
        except UserProfile.DoesNotExist:
            return Response({"error": "UserProfile not found."}, status=status.HTTP_404_NOT_FOUND)
        list_id = profile.telegram_current_list.id
        order_number = Categories.objects.filter(list_id=list_id).aggregate(Max('order_number'))['order_number__max']
        return Response({"order_number": order_number + 1})


class CategoryPurifyView(views.APIView):
    """
            View class goal is to clean category of purchases. If it's the only link for the purchase --
        so it will be deleted, if not -- so link to the category will be deleted and purchase will be kept.
    """
    @staticmethod
    def put(request):
        try:
            category = Categories.objects.get(id=request.data['category_id'])
        except Categories.DoesNotExist:
            return Response({"error": "Category not found."}, status=status.HTTP_404_NOT_FOUND)

        purchases = category.purchases.all()
        for purchase in purchases:
            if len(purchase.categories_set.all()) > 1:
                category.purchases.remove(purchase)
            else:
                purchase.delete()
        return Response({"message": "OK"}, status=status.HTTP_200_OK)


class CategoryDetailView(views.APIView):
    """
        View для:
         1. создания новой категории.
         2. изменения одной категории
         3. редактирования одной категории
         4. чтения одной категории со связанными покупками
    """

    permission_classes = [IsTelegramUserOrIsUsersList]

    @staticmethod
    def get(request):
        try:
            category = Categories.objects.get(id=request.data['category_id'])
        except Categories.DoesNotExist:
            return Response({"error": "Category not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = CategoriesPrefetchSerializer(category)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @staticmethod
    def post(request):
        try:
            profile = UserProfile.objects.get(telegram_user_id=request.data['telegram_user_id'])
        except UserProfile.DoesNotExist:
            return Response({"error": "UserProfile not found."}, status=status.HTTP_404_NOT_FOUND)
        list_id = profile.telegram_current_list.id
        data = {
            'name': request.data['name'],
            'description': request.data['description'],
            'list': list_id,
            'order_number': request.data['order_number']
        }
        serializer = CategoryAddSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def delete(request):
        category_id = request.data['category_id']
        try:
            category = Categories.objects.get(id=category_id)
        except Categories.DoesNotExist:
            return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
        purchases = category.purchases.all()
        if len(purchases) == 0:
            if category.id != category.list.blank_category.id:
                category.delete()
                category_serializer = CategoryAddSerializer(category)
                return Response(category_serializer.data, status=status.HTTP_200_OK)
            else:
                data = {'error': 'base_category', 'name': f"{category.list.blank_category.name}"}
                return Response(data=data, status=status.HTTP_406_NOT_ACCEPTABLE)
        else:
            data = {'error': 'not_empty'}
            return Response(data=data, status=status.HTTP_406_NOT_ACCEPTABLE)

    @staticmethod
    def put(request):
        try:
            category = Categories.objects.get(id=request.data['category_id'])
        except Categories.DoesNotExist:
            return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
        category.name = request.data['name']
        category.description = request.data['description']
        category.save()
        serializer = CategoriesDitailSerializer(category)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class CategoriesListView(generics.ListAPIView):
    """ Список категорий без связанных объектов. """
    serializer_class = CategoriesListSerializer
    permission_classes = [IsTelegramUserOrIsUsersList]

    def get_queryset(self):
        profile = UserProfile.objects.get(telegram_user_id=self.request.data.get('telegram_user_id'))
        current_list_id = profile.telegram_current_list.id
        queryset = Categories.objects.filter(list__id=current_list_id)
        if isinstance(queryset, QuerySet):
            # Ensure queryset is re-evaluated on each request.
            queryset = queryset.all()
        return queryset


class PurchasesCreateView(views.APIView):
    """
    View для создания новой записи в списке

    При создании записи в списке создается связь с категорией по переданному id.

    Пример тела запроса:
        {
        "name": "Кофе",
        "description": "Молотый",
        "list": 1,
        "category": 15
        }
    """

    permission_classes = [IsTelegramUserOrIsUsersList]

    @staticmethod
    def get_list_details(telegram_user_id):
        response = Response(status=status.HTTP_200_OK)
        profile = {}
        try:
            profile = UserProfile.objects.get(telegram_user_id=telegram_user_id)
        except UserProfile.DoesNotExist:
            response = Response({"error": "UserProfile not found."}, status=status.HTTP_404_NOT_FOUND)
        current_list = profile.telegram_current_list
        list_id = current_list.id
        blank_category = current_list.blank_category
        return list_id, blank_category, response

    @staticmethod
    def get_existed_purchases(purchases_names, list_id):
        existed_purchases_names = []
        existed_purchases = []
        try:
            existed_purchases_queryset = Purchases.objects.filter(name__in=purchases_names, list_id=list_id)
            existed_purchases = serializers.serialize('python', existed_purchases_queryset)
            existed_purchases_names = [purchase['fields']['name'] for purchase in existed_purchases]
        except Purchases.DoesNotExist:
            print("Все позиции новые.")
        return existed_purchases, existed_purchases_names

    @staticmethod
    def is_the_purchase_new(purchase, existed_purchases_names, existed_purchases):
        do = True
        if purchase['name'] in existed_purchases_names:
            purchase_description = purchase.get('description', '')
            for ex_purchase in existed_purchases:
                if (ex_purchase['fields']['name'] == purchase['name'] and
                        ex_purchase['fields']['description'] == purchase_description):
                    do = False
                    break
        return do

    @staticmethod
    def create_new_purchase(purchase, blank_category, list_id):
        purchases_serializer = PurchaseAddSerializer(data=purchase)
        response = Response(status=status.HTTP_200_OK)
        category = blank_category
        if 'category_id' in purchase.keys():
            try:
                category = Categories.objects.get(id=purchase['category_id'])
            except Categories.DoesNotExist:
                response = Response({"error": "Category not found."}, status=status.HTTP_404_NOT_FOUND)
        purchase['list'] = list_id
        if not purchases_serializer.is_valid():
            return purchases_serializer, Response(purchases_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        purchase = purchases_serializer.save()
        category.purchases.add(purchase)
        category.save()
        return purchases_serializer, category, response

    @staticmethod
    def categorize_existed(existed_list: list, list_id: int) -> Dict[str, Any]:
        categorized_existed_dict = {}
        for purchase in existed_list:
            purchase_obj = Purchases.objects.get(name=purchase["name"],
                                                 description=purchase.get("description", ''),
                                                 list=list_id)
            categories = purchase_obj.categories_set.all()
            for category in categories:
                if not categorized_existed_dict.get(f'{category.name}', None):
                    categorized_existed_dict[f'{category.name}'] = []
                categorized_existed_dict[f'{category.name}'].append(purchase)
        return categorized_existed_dict

    @staticmethod
    def post(request):
        response = {"added": {}, "existed": []}

        list_id, blank_category, resp = PurchasesCreateView.get_list_details(request.data['telegram_user_id'])
        if resp.status_code != 200:
            return resp

        purchases_json_str = request.data['purchases'].replace("'", '"')
        purchases = json.loads(purchases_json_str)
        purchases_names = [pur['name'] for pur in purchases]

        existed_purchases, existed_purchases_names = PurchasesCreateView.get_existed_purchases(purchases_names, list_id)

        for purchase in purchases:
            if PurchasesCreateView.is_the_purchase_new(purchase, existed_purchases_names, existed_purchases):
                purchases_serializer, category, resp = (
                    PurchasesCreateView.create_new_purchase(purchase, blank_category, list_id))
                if resp.status_code != 200:
                    return resp
                if not response["added"].get(f"{category.name}", None):
                    response["added"][f"{category.name}"] = []
                response["added"][f"{category.name}"].append(purchases_serializer.data)
            else:
                purchases_serializer = PurchaseAddSerializer(data=purchase)
                purchases_serializer.is_valid()
                response["existed"].append(purchases_serializer.data)
        response["existed"] = PurchasesCreateView.categorize_existed(response['existed'], list_id)
        return Response(response, status=status.HTTP_200_OK)


class CategoryPurchasesUpdateView(views.APIView):
    permission_classes = [IsTelegramUserOrIsUsersList]

    @staticmethod
    def put(request):
        purchase_id = request.data["purchase_id"]
        category_id = request.data.get('category_to_id', None)

        if category_id is not None:
            try:
                category = Categories.objects.get(id=category_id)
            except Categories.DoesNotExist:
                return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)

            category.purchases.add(purchase_id)

        category_from_id = request.data.get('category_from_id')
        if category_from_id is not None:
            try:
                category_from = Categories.objects.get(id=category_from_id)
            except Categories.DoesNotExist:
                return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
            category_from.purchases.remove(purchase_id)
        return Response({"Message": "OK"}, status=status.HTTP_200_OK)


class CategorySortMoveView(views.APIView):

    permission_classes = [IsTelegramUserOrIsUsersList]

    @staticmethod
    def put(request):
        main_category_id, move, telegram_user_id = request.data['category_id'], request.data['move'], request.data['telegram_user_id']
        try:
            main_category = Categories.objects.get(id=main_category_id)
        except Categories.DoesNotExist:
            return Response({"error": "Main category not found"}, status=status.HTTP_404_NOT_FOUND)
        main_order_number = main_category.order_number

        try:
            profile = UserProfile.objects.get(telegram_user_id=telegram_user_id)
        except UserProfile.DoesNotExist:
            return Response({"error": "UserProfile not found"}, status=status.HTTP_404_NOT_FOUND)
        current_list = profile.telegram_current_list

        try:
            if move == 'up':
                next_category = Categories.objects.filter(
                    order_number__lt=main_category.order_number, list_id=current_list).order_by('-order_number').first()
            else:
                next_category = Categories.objects.filter(
                    order_number__gt=main_category.order_number, list_id=current_list).order_by('order_number').first()
        except Categories.DoesNotExist:
            return Response({"error": "Next category not found"}, status=status.HTTP_404_NOT_FOUND)

        main_category.order_number, next_category.order_number = next_category.order_number, main_category.order_number
        main_category.save()
        next_category.save()
        return Response({"message": "OK"}, status=status.HTTP_200_OK)


class PurchaseDetailView(views.APIView):
    permission_classes = [IsTelegramUserOrIsUsersList]

    @staticmethod
    def get(request):
        purchase_id = request.data['purchase_id']
        try:
            purchase = Purchases.objects.get(id=purchase_id)
        except Purchases.DoesNotExist:
            return Response({"error": "Purchase not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(PurchaseAddSerializer(purchase).data, status=status.HTTP_200_OK)

    @staticmethod
    def delete(request):
        purchase_id = request.data['purchase_id']
        try:
            purchase = Purchases.objects.get(id=purchase_id)
        except Purchases.DoesNotExist:
            return Response({"error": "Purchase not found."}, status=status.HTTP_404_NOT_FOUND)

        purchase.categories_set.clear()
        serializer = PurchaseAddSerializer(purchase)
        purchase.delete()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @staticmethod
    def put(request):
        purchase_id = request.data['purchase_id']
        try:
            purchase = Purchases.objects.get(id=purchase_id)
        except Purchases.DoesNotExist:
            return Response({"error": "Purchase not found."}, status=status.HTTP_404_NOT_FOUND)
        purchase.name = request.data["name"]
        purchase.description = request.data.get("description", "")
        purchase.save()
        return Response(PurchaseAddSerializer(purchase).data, status=status.HTTP_200_OK)


class PurchaseGetCategoriesView(views.APIView):
    permission_classes = [IsTelegramUserOrIsUsersList]

    @staticmethod
    def get(request):
        purchase_id = request.data.get('purchase_id')
        try:
            purchase = Purchases.objects.get(id=purchase_id)
        except Purchases.DoesNotExist:
            return Response({"error": "Purchase not found"}, status=status.HTTP_404_NOT_FOUND)
        categories_queryset = purchase.categories_set.all()
        categories_dict = serializers.serialize('python', categories_queryset)
        categories_ids = []
        for category in categories_dict:
            categories_ids.append(category['pk'])
        return Response({"categories_ids": categories_ids}, status=status.HTTP_200_OK)


class ListsCreateUpdateNewView(View):
    """ View для создания нового списка с категорией "Без категории". """
    permission_classes = [IsAuthenticated]

    @staticmethod
    def post(request):
        data = request.POST
        full_data = {'name': data.get('name'), 'description': data.get('description')}
        try:
            profile = UserProfile.objects.get(telegram_user_id=data.get("telegram_user_id"))
        except UserProfile.DoesNotExist:
            return JsonResponse({"error": "UserProfile not found."}, status=status.HTTP_404_NOT_FOUND)
        full_data["owner"] = profile.id
        serializer = ListSerializer(data=full_data)
        if not serializer.is_valid():
            return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        new_list = serializer.save()
        new_blank_category = Categories.objects.create(name="Без категории", list=new_list, order_number=0)
        new_list.blank_category = new_blank_category
        new_list.save()

        # TODO: Исправить на декоратор и добавить ко всем методам всех классов:
        try:
            profile = UserProfile.objects.get(telegram_user_id=data.get('telegram_user_id'))
        except UserProfile.DoesNotExist:
            return JsonResponse({"error": "UserProfile not found."}, status=status.HTTP_404_NOT_FOUND)
        profile.last_active_date_time = timezone.now()
        profile.lists.add(new_list)
        profile.telegram_current_list = new_list
        profile.save()
        return JsonResponse({'message': 'OK'}, status=status.HTTP_200_OK)

    @staticmethod
    def put(request):
        my_dict = parse_qs(request.body.decode())
        data = {k: my_dict[k][0] for k in my_dict}
        try:
            list_for_update = Lists.objects.get(id=data['list_id'])
            list_for_update.name = data['name']
            list_for_update.description = data['description']
            list_for_update.save()
            return JsonResponse({'message': 'OK'}, status=status.HTTP_200_OK)
        except Lists.DoesNotExist:
            return JsonResponse({"error": "List not found."}, status=status.HTTP_404_NOT_FOUND)


class ListOfUsersListsView(views.APIView):
    """ View для отправки всех списков пользователя. """
    permission_classes = [IsTelegramUserOrIsUsersList]

    def get(self, second_parameter):
        if self.request.user.id == TELEGRAM_BOT_USER_ID:
            telegram_user_id = self.request.data.get("telegram_user_id")
            try:
                profile = UserProfile.objects.get(telegram_user_id=telegram_user_id)
            except UserProfile.DoesNotExist:
                return Response({"error": "UserProfile not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            try:
                profile = UserProfile.objects.get(user_id=self.request.user.id)
            except UserProfile.DoesNotExist:
                return Response({"error": "UserProfile not found."}, status=status.HTTP_404_NOT_FOUND)
        lists = list(profile.lists.values_list('id', flat=True))
        queryset = Lists.objects.filter(id__in=lists)
        lists_data = serializers.serialize('python', queryset)
        current_list = profile.telegram_current_list
        current_list_data = ListSerializer(current_list).data
        lists_data.append(current_list_data)
        return Response(lists_data, status=status.HTTP_200_OK)


class ListOfUsersListsForDeleteView(views.APIView):
    """
            View-класс для получения списков пользователя
    """


class ListOfUsersListsView1(generics.ListAPIView):
    """ View для отправки всех списков пользователя. """
    permission_classes = [IsTelegramUserOrIsUsersList]
    serializer_class = ListSerializer

    # TODO: Переделать в подкласс View. Переопределить метод get() так,
    #  чтобы он возвращал уже словарь с выделенным жирным текущим списком.
    def get_queryset(self):
        if self.request.user.id == TELEGRAM_BOT_USER_ID:
            try:
                profile = UserProfile.objects.get(telegram_user_id=self.request.data.get("telegram_user_id"))
            except UserProfile.DoesNotExist:
                return Response({"error": "UserProfile not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            try:
                profile = UserProfile.objects.get(user_id=self.request.user.id)
            except UserProfile.DoesNotExist:
                return Response({"error": "UserProfile not found."}, status=status.HTTP_404_NOT_FOUND)
        lists = list(profile.lists.values_list('id', flat=True))
        queryset = Lists.objects.filter(id__in=lists)
        if isinstance(queryset, QuerySet):
            # Ensure queryset is re-evaluated on each request.
            queryset = queryset.all()
        return queryset


class ChangeCurrentListView(View):
    """ View для изменения текущего списка для пользователя """
    permission_classes = [IsTelegramUserOrIsUsersList]

    @staticmethod
    def put(request):
        """ Метод устанавливает новое значения для поля telegram_current_list для текущего пользователя. """
        data = ast.literal_eval(request.body.decode())
        try:
            user_profile = UserProfile.objects.get(telegram_user_id=data["telegram_user_id"])
        except UserProfile.DoesNotExist:
            return Response({"error": "UserProfile not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            new_current_list = Lists.objects.get(id=data["new_current_list_id"])
        except Lists.DoesNotExist:
            return Response({"error": "List not found."}, status=status.HTTP_404_NOT_FOUND)
        user_profile.telegram_current_list = new_current_list
        user_profile.save()
        return JsonResponse(ListSerializer(new_current_list).data)


class RegisterNewTelegramBotUserView(View):
    """ View для регистрации нового (реактивации остановленного) пользователя телеграм-бота. """
    permission_classes = [IsAuthenticated]

    @staticmethod
    def post(request):

        try:
            profile = UserProfile.objects.get(telegram_user_id=request.POST.get("telegram_user_id"))
            profile.stopped_in_telegram = False
            profile.last_active_date_time = timezone.now()
            profile.save()
            return JsonResponse({'message': 'User profile already exists'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except UserProfile.DoesNotExist:
            data = request.POST
            # TODO: Исправить на сохранение через сериализатор:
            print(f"{data.get('telegram_user_name') = }")
            UserProfile.objects.create(
                name=data.get("telegram_user_name", data.get('telegram_user_id')),
                telegram_user_id=int(data.get('telegram_user_id')),
                telegram_username=data.get('telegram_user_name'),
                telegram_firstname=data.get('first_name'),
                telegram_lastname=data.get('last_name'),
                telegram_registering_date=timezone.now(),
                telegram_language=data.get('language_code'),
                stopped_in_telegram=False,
                last_active_date_time=timezone.now()
            )
            return JsonResponse({'message': 'User profile created successfully'}, status=status.HTTP_201_CREATED)


class ListsUpdateAccessView(views.APIView):
    permission_classes = [IsTelegramUserOrIsUsersList]

    @staticmethod
    def put(request):
        friend_id = request.data['friend_id']
        move = request.data['move']
        list_id = request.data['list_id']
        try:
            friend = UserProfile.objects.get(id=friend_id)
        except UserProfile.DoesNotExist:
            return Response({"error": "UserProfile Not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            if move == "share":
                friend.lists.add(list_id)
            else:
                friend.lists.remove(list_id)
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status.HTTP_409_CONFLICT)


class ProfilesUpdateFriendsView(views.APIView):
    permission_classes = [IsTelegramUserOrIsUsersList]

    @staticmethod
    def put(request):
        telegram_user_id = request.data['telegram_user_id']
        friend_id = request.data.get('friend_id', None)
        friend_username = request.data.get('friend_username', None)
        move = request.data['move']
        if friend_id == telegram_user_id:
            return Response({"error": "Вы прислали свой id. Нужен id другого пользователя."},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            profile = UserProfile.objects.get(telegram_user_id=telegram_user_id)
            if friend_id is not None:
                friend = UserProfile.objects.get(telegram_user_id=friend_id)
            else:
                friend = UserProfile.objects.get(telegram_username=friend_username)
        except UserProfile.DoesNotExist:
            return Response({"error": "UserProfile Not found."}, status=status.HTTP_404_NOT_FOUND)
        if friend.id == profile.id:
            return Response({"error": "Вы прислали свой username. Нужен username другого пользователя."},
                            status=status.HTTP_400_BAD_REQUEST)
        if move == "add":
            profile.friends.add(friend)
        else:
            profile.friends.remove(friend)
        return Response(status=status.HTTP_200_OK)


class ProfilesGetFriendsView(views.APIView):
    permission_classes = [IsTelegramUserOrIsUsersList]

    @staticmethod
    def get(request):
        telegram_user_id = request.data['telegram_user_id']
        try:
            profile = UserProfile.objects.get(telegram_user_id=telegram_user_id)
        except UserProfile.DoesNotExist:
            return Response({"error": "UserProfile Not found."}, status=status.HTTP_404_NOT_FOUND)
        friends_queryset = profile.friends.all()
        friends = serializers.serialize('python', friends_queryset)
        return Response(friends, status=status.HTTP_200_OK)


class ProfilesDeleteFriendView(views.APIView):
    permission_classes = [IsTelegramUserOrIsUsersList]

    @staticmethod
    def delete(request):
        telegram_user_id = request.data.get("telegram_user_id", None)
        friend_id = request.data.get("friend_id", None)
        try:
            profile = UserProfile.objects.get(telegram_user_id=telegram_user_id)
            friend = UserProfile.objects.get(id=friend_id)
        except UserProfile.DoesNotExist:
            return Response({"error": "UserProfile Not found."}, status=status.HTTP_404_NOT_FOUND)
        lists_ids = profile.lists.all().values_list('id', flat=True)
        friend.lists.remove(*lists_ids)
        profile.friends.remove(friend_id)
        return Response(status=status.HTTP_200_OK)


class ProfilesGetOneView(views.APIView):
    permission_classes = [IsTelegramUserOrIsUsersList]

    @staticmethod
    def get(request):
        telegram_user_id = request.data.get('telegram_user_id')
        try:
            profile = UserProfile.objects.get(telegram_user_id=telegram_user_id)
        except UserProfile.DoesNotExist:
            return Response({"error": "UserProfile Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserProfileTelegramDitailSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProfilesOptionsView(views.APIView):
    permission_classes = [IsTelegramUserOrIsUsersList]

    @staticmethod
    def get(request):
        telegram_user_id = request.data.get('telegram_user_id')
        try:
            profile = UserProfile.objects.get(telegram_user_id=telegram_user_id)
        except UserProfile.DoesNotExist:
            return Response({"error": "UserProfile Not found."}, status=status.HTTP_404_NOT_FOUND)
        data = {
                'telegram_tips': profile.telegram_tips,
                'telegram_buttons_style': profile.telegram_buttons_style,
                'telegram_language': profile.telegram_language
            }
        return Response(data, status=status.HTTP_200_OK)

    @staticmethod
    def put(request):
        telegram_user_id = request.data.get('telegram_user_id')
        telegram_tips = request.data.get('telegram_tips')
        telegram_buttons_style = request.data.get('telegram_buttons_style')
        telegram_language = request.data.get('telegram_language')
        try:
            profile = UserProfile.objects.get(telegram_user_id=telegram_user_id)
        except UserProfile.DoesNotExist:
            return Response({"error": "UserProfile Not found."}, status=status.HTTP_404_NOT_FOUND)

        if telegram_tips:
            profile.telegram_tips = bool(int(telegram_tips))
        if telegram_buttons_style:
            profile.telegram_buttons_style = telegram_buttons_style
        if telegram_language:
            profile.telegram_language = telegram_language
        profile.save()
        return Response(status=status.HTTP_200_OK)


class WebRegisterView(CreateView):
    form_class = UserCreationForm
    template_name = "myauth/register.html"
    success_url = "http://127.0.0.1:8000/lists/0/"

    def form_valid(self, form):
        response = super().form_valid(form)
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password1")
        user = authenticate(
            self.request,
            username=username,
            password=password,
        )
        login(request=self.request, user=user)
        return response
