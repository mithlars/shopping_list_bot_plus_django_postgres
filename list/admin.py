from django.contrib import admin
from .models import *


class CategoriesAdmin(admin.ModelAdmin):
    list_display = ('list', 'id', 'name', 'description', 'order_number', 'published')
    list_display_links = ('list', 'id', 'name', 'description', 'order_number', 'published')
    search_fields = ('list', 'id', 'name', 'description')


admin.site.register(Categories, CategoriesAdmin)


class PurchasesAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'published')
    list_display_links = ('id', 'name', 'description', 'published')
    search_fields = ('id', 'name', 'description')


admin.site.register(Purchases, PurchasesAdmin)


class GroupsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'published')
    list_display_links = ('id', 'name', 'description', 'published')
    search_fields = ('id', 'name', 'description')


admin.site.register(Groups, GroupsAdmin)


class ListsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'published', 'blank_category')
    list_display_links = ('id', 'name', 'description', 'published')
    search_fields = ('id', 'name', 'description')


admin.site.register(Lists, ListsAdmin)


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'telegram_user_id', 'gender', 'published')
    list_display_links = ('id', 'name', 'telegram_user_id')
    search_fields = ('id', 'name')


admin.site.register(UserProfile, UserProfileAdmin)