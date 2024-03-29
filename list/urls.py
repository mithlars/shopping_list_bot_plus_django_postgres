from django.urls import path
from .views import (
    ListOrGroupView,
    ListOfUsersListsView,
    CategoryDetailView,
    CategoriesListView,
    PurchasesCreateView,
    CategoryPurchasesUpdateView,
    PurchaseDetailView,
    WebRegisterView,
    RegisterNewTelegramBotUserView,
    ListsCreateUpdateNewView,
    ChangeCurrentListView, GetBlankCategoryView, CategoriesGetNextOrderNumberView, ListDitailView, CategorySortMoveView,
    CategoryPurifyView,
    PurchaseGetCategoriesView, GroupsView, GroupDitailView, GroupSortMoveView, GroupGetNextOrderNumberView, GroupPurifyView,
    GroupCategoriesUpdateView, GroupsPrefetchView, GroupCategoriesView, GroupGetCurrentView, GroupChangeCurrentView,
    ListView, ListsUpdateAccessView, ProfilesUpdateFriendsView, ProfilesGetFriendsView, ProfilesDeleteFriendView, ProfilesGetOneView,
    ProfilesOptionsView
)

app_name = "lists"
urlpatterns = [
    path('register/', WebRegisterView.as_view(), name='register'),
    path('telegram_register/', RegisterNewTelegramBotUserView.as_view(), name='telegram_register'),
    path('profiles/update_friends/', ProfilesUpdateFriendsView.as_view(), name="update_user's_friends"),
    path('profiles/get_friends/', ProfilesGetFriendsView.as_view(), name="get_user's_friends"),
    path('profiles/delete_friend/', ProfilesDeleteFriendView.as_view(), name="delete_user's_friend"),
    path('profiles/get_one/', ProfilesGetOneView.as_view(), name="get_one_profile's_details"),
    path('profiles/options/', ProfilesOptionsView.as_view(), name="get_profile's_options"),

    path('lists/', ListView.as_view(), name='list'),
    path('lists/list_or_group/', ListOrGroupView.as_view(), name='list'),
    path('lists/detail/', ListDitailView.as_view(), name='get_lists_ditail'),
    path('lists/users_lists/', ListOfUsersListsView.as_view(), name="list_of_user's_lists"),
    path('lists/change_current/', ChangeCurrentListView.as_view(), name='change_current_list'),
    path('lists/create_update_new_list/', ListsCreateUpdateNewView.as_view(), name='create_new_list'),
    path('lists/update_access/', ListsUpdateAccessView.as_view(), name="update_user_profile's_friends"),

    path('groups/', GroupsView.as_view(), name='list_of_groups'),
    path('groups/get_current/', GroupGetCurrentView.as_view(), name="get_current_group_for_user's_current_list"),
    path('groups/change_current/', GroupChangeCurrentView.as_view(),
         name="put_new_current_group_for_user's_current_list"),
    path('groups/prefetch/', GroupsPrefetchView.as_view(), name='list_of_groups_with_categories-and_list_details'),
    path('groups/add/', GroupDitailView.as_view(), name='create_new_group'),
    path('groups/update/', GroupDitailView.as_view(), name='update_group'),
    path('groups/delete/', GroupDitailView.as_view(), name='delete_group'),
    path('groups/sort/', GroupSortMoveView.as_view(), name='sort_list_of_groups'),
    path('groups/get_order_number/', GroupGetNextOrderNumberView.as_view(), name=''),
    path('groups/get_one/', GroupDitailView.as_view(), name=''),
    path('groups/purify/', GroupPurifyView.as_view(), name=''),
    path('groups/category_in_out/', GroupCategoriesUpdateView.as_view(),
         name='add_category_to_the_group_or_get_it_out'),
    path('groups/categories/', GroupCategoriesView.as_view(), name='get_categories_of_the_group'),

    path('categories/', CategoriesListView.as_view(), name='get_categories_list'),
    path('categories/get_order_number/', CategoriesGetNextOrderNumberView.as_view(),
         name="get_new_category_order_number"),
    path('categories/get_one/', CategoryDetailView.as_view(), name='get_category_with_purchases'),
    path('categories/sort/', CategorySortMoveView.as_view(), name='sort_categories'),
    path('categories/add/', CategoryDetailView.as_view(), name='category-create'),
    path('categories/update/', CategoryDetailView.as_view(), name='update_category'),
    path('categories/get_blank/', GetBlankCategoryView.as_view(), name='get_blank_category'),
    path('categories/purify/', CategoryPurifyView.as_view(), name='category_purify'),
    path('categories/purchases_update/', CategoryPurchasesUpdateView.as_view(), name='category-update-purchases'),
    path('categories/delete/', CategoryDetailView.as_view(), name='delete_category'),

    path('purchases/add/', PurchasesCreateView.as_view(), name='purchase-create'),
    path('purchases/detail/', PurchaseDetailView.as_view(), name='purchases-delete'),
    path('purchases/categories/', PurchaseGetCategoriesView.as_view(), name='get_categories_of_purchase')
]
