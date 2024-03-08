from rest_framework import serializers
from .models import *
from rest_framework.fields import empty


class PurchasesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchases
        fields = ('id', 'name', 'description', 'published')


class ListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lists
        fields = ('id', 'name', 'description', 'owner', 'published', 'blank_category')


class CategoriesPrefetchSerializer(serializers.ModelSerializer):
    purchases = PurchasesSerializer(many=True)
    list = ListSerializer()

    class Meta:
        model = Categories
        fields = ('id', 'description', 'name', 'purchases', 'list', 'order_number')


class CategoriesDitailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categories
        fields = ('name', 'description')


class CategoriesListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categories
        fields = ('id', 'name', 'description', 'published')


class PurchaseAddSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchases
        fields = ('id', 'name', 'description', 'published', 'list')


class CategoryAddSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categories
        fields = ('order_number', 'id', 'name', 'description', 'published', 'list')


class GroupsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Groups
        fields = ('id', 'name', 'description', 'categories', 'list', 'order_number')


class GroupPrefetchSerializer(serializers.ModelSerializer):
    categories = CategoriesDitailSerializer(many=True)
    list = ListSerializer()

    class Meta:
        model = Groups
        fields = ('id', 'order_number', 'name', 'description', 'list', 'categories')


class UserProfileTelegramDitailSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            'id',
            'name',
            'published',
            'telegram_user_id',
            'telegram_username',
            'telegram_firstname',
            'telegram_lastname',
            'telegram_registering_date',
            'telegram_language',
            'stopped_in_telegram',
            'telegram_current_list',
            'lists',
            'last_active_date_time'
        )