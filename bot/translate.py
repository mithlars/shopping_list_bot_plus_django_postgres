

transl = {
            'ru': {
                'main_help': '*Этот бот создан для работы со списками.*\n'
                             '\n'
                             '*Основные возможности бота:*\n'
                             '1. Можно добавлять и удалять позиции списков;\n'
                             '2. Можно создать категории для списка и назначать категории дла позиций списков;\n'
                             '3. Создавать новые списки;\n'
                             '4. Давать доступ к спискам другим пользователям бота '
                             'для совместного использования списков;\n'
                             '5. Можно выводить весь список, а можно создать группы для нескольких категорий списка '
                             'и выводить эту группу категорий вместо всего списка;\n'
                             '\n'
                             '[*Ссылка на видео инструкцию по работе с позициями списка и категориями:*]'
                             '(https://youtu.be/kOfxkskDiLc?si=BQ9gg86jeI49F-4F)\n'
                             '\n'
                             '*Более подробно о функциях бота:*\n'
                             '1:\nДобавлять позиции списка можно просто отправив сообщение из любого раздела бота.\n'
                             'Чтобы удалить позицию нужно в основном разделе нажать на кнопку с номером позиции, '
                             'которую Вы хотите удалить.\n'
                             '\n'
                             '2:\nВ разделе \"Категории\" есть меню для управления категориями, там Вы сможете '
                             'создать, удалить, переименовать, очистить (удалить все позиции категории).'
                             'В основном разделе есть кнопки \"В категорию\" и \"Из категории\", с их помощью '
                             'Вы сможете перемещать позиции списка между категориями.\n'
                             '\n'
                             '3:\nАналогично категориям есть разделы для работы со списками.\n'
                             '\n'
                             '4:\nВ разделе для работы со списком есть подраздел для управления окружением '
                             '(список пользователей, с которыми Вы можете делиться своими списками) '
                             'и предоставления доступа к спискам.\n'
                             '\n'
                             '5:\nАналогично категориям и спискам есть разделы для работы с группами.'
                             'В этом разделе Вы сможете создать группу и изменить ее имя или состав ее категорий.'
                             '',
                'add': {
                    'input_description': 'Теперь введите описание'
                },
                'buttons': {
                    'cancel': 'Отмена',
                    'no_chngs': 'Без изменений',
                    'no_descr': 'Без описания'
                },
                'errors': {
                    'smt_rong': 'Что-то пошло не так'
                },
                'vocabulary': {
                    'category': 'Категория',
                    'ok': 'Хорошо'
                },
                'categories': {
                    'add': {
                        'input_name': 'Введите имя новой категории',
                        'new': 'Новая категория',
                        'created': 'создана',
                        'description': 'Описание'
                    },
                    'delete': {
                        'deleted': 'удалена',
                        'del_cat_from': 'Удаление категорий списка',
                        'empty_only': 'можно удалить только *пустые категории*',
                        'can_delete_only_empty': 'Можно удалить только пустую категорию.',
                        'is_base_cant_be_delete': 'является *базовой*, ее *нельзя* удалить.'
                    },
                    'sort': {
                        'choose_move': 'Выберите действия для изменения сортировки категорий:',
                        'not_enough': 'Категорий слишком мало для сортировки.'
                    },
                    'purify': {
                        'which_cat_purify_1': 'Какую категорию из списка',
                        'which_cat_purify_2': 'Вы хотите очистить?',
                        'sure_delete_all_q': 'Вы уверены, что хотите удалить позиции категории?',
                        'i_am_sure': 'Да, я хочу удалить позиции этой категории!',
                        'no_i_chged_mind': 'Нет, я передумал удалять позиции категории!'
                    },
                    'update': {
                        'choose_cat_for_update': 'Выберите категорию для редактирования:',
                        'input_new_cat_name': 'Введите новое имя для категории',
                        'input_new_cat_descr': 'Теперь введите новое описание',
                        'your_chs_no_chngs': 'Вы решили оставить данные категории без изменений.'
                    }
                },
                'options': {
                    'buttons_style': {
                        'message': "Стиль отображения кнопок \n(текст, картинки или картинки с сокращенным текстом):",
                    },
                    'tips': {
                        'message': "Опция отображения подсказок:",
                        'buttons': {'show': 'Показать'}
                    },
                    'language': {
                        'message': ""
                    }
                },
                'list_menu': {
                    'buttons': {
                        'groups': 'Группы',
                        'categories': 'Категории',
                        'lists': 'Списки',
                        'options': 'Опции',
                        'reload': 'Обновить',
                        'edit': 'Изменить',
                        'to_category': 'В категорию',
                        'from_category': 'Из категории'
                    },
                    'buttons_short': {
                        'groups': 'Гр.',
                        'categories': 'Кат.',
                        'lists': 'Сп.',
                        'options': 'Опц.',
                        'reload': 'Обн.',
                        'edit': 'Изм.',
                        'to_category': 'В кат.',
                        'from_category': 'Из кат.'
                    }
                },
                'lists_menu': {
                    'buttons': {
                        'switch': 'сменить',
                        'edit': 'изменить',
                        'add': 'создать',
                        'share': 'доступ',
                        'delete': 'удалить',
                        'clean': 'очистить',
                        'back': 'назад'
                    },
                    'buttons_short': {
                        'switch': 'смен.',
                        'edit': 'изм.',
                        'add': 'созд.',
                        'share': 'дост.',
                        'delete': 'удал.',
                        'clean': 'очист.',
                        'back': 'наз.'
                    }
                },
                'groups_menu': {
                    'buttons': {
                        'switch': 'сменить',
                        'edit': 'изменить',
                        'add': 'создать',
                        'sort': 'сортировать',
                        'delete': 'удалить',
                        'back': 'назад'
                    },
                    'buttons_short': {
                        'switch': 'смен.',
                        'edit': 'изм.',
                        'add': 'созд.',
                        'sort': 'сорт.',
                        'delete': 'удал.',
                        'back': 'наз.'
                    }
                },
                'categories_menu': {
                    'buttons': {
                        'edit': 'изменить',
                        'add': 'создать',
                        'sort': 'сортировать',
                        'delete': 'удалить',
                        'clean': 'очистить',
                        'back': 'назад'
                    },
                    'buttons_short': {
                        'edit': 'изм.',
                        'add': 'созд.',
                        'sort': 'сорт.',
                        'delete': 'удал.',
                        'clean': 'очист.',
                        'back': 'наз.'
                    }
                },
                'share_menu': {  # "Доступ к списку", "Окружение", "Добавь меня", "Назад к спискам", "назад"
                    'buttons': {
                        'access': 'Доступ к списку',
                        'surrounding': 'Окружение',
                        'add_me': 'Добавь меня',
                        'back_to_lists': 'Назад к спискам',
                        'back': 'назад'
                    },
                    'buttons_short': {  # "Доступ к списку", "Окружение", "Добавь меня", "↩️📦к спискам", "↩️📋назад"
                        'access': 'Доступ к списку',
                        'surrounding': 'Окружение',
                        'add_me': 'Добавь меня',
                        'back_to_lists': 'к спискам',
                        'back': 'назад'
                    }

                }
            },
            'en': {
                'main_help': '*This bot is created to work with lists.*\n'
                             '\n'
                             '*Basic bot capabilities:*\n'
                             '1. You can add and remove list positions;\n'
                             '2. You can create categories for a list and assign categories for list items;\n'
                             '3. Create new lists;\n'
                             '4. Give access to lists to other users of the bot for sharing lists;\n'
                             '5. You can display the whole list, or you can create groups '
                             'for several categories of the list and display this group of categories '
                             'instead of the whole list;\n'
                             '\n'
                             '[*Link to video instruction for working with list items and categories:*]'
                             '(https://youtu.be/kOfxkskDiLc?si=BQ9gg86jeI49F-4F)\n'
                             '\n'
                             '*In more detail about bot functions:*\n'
                             '1:\nYou can add list positions by simply sending a message from any bot section.\n'
                             'To remove this item you need to click on the button with the item number '
                             'you want to remove in the bot section.\n'
                             '\n'
                             '2:\nIn the section \"Categories\" there is a menu to manage categories, '
                             'there you will be able to create, delete, rename, clear (remove all category positions).'
                             'In the main section there are buttons \"To category\" and \"From category\" '
                             'with their help you will be able to move list positions between categories.\n'
                             '\n'
                             '3:\nSimilarly to categories there is section to work with lists.\n'
                             '\n'
                             '4:\nThere is a subsection to manage your environment in the list section '
                             '(list of users you can share your lists with) and providing access to your lists.\n'
                             '\n'
                             '5:\nSimilarly to categories and lists there is section for working with groups.'
                             'In this section you can create a group and change its name or its categories.'
                             '',
                'add': {
                    'input_description': 'Now input description'
                },
                'buttons': {
                    'cancel': 'Cancel',
                    'no_chngs': "Without changes",
                    'no_descr': 'Without description'
                },
                'errors': {
                    'smt_rong': "Something went wrong"
                },
                'vocabulary': {
                    'category': 'Category',
                    'ok': 'OK'
                },
                'categories': {
                    'add': {
                        'input_name': 'Add new category name',
                        'new': 'New category',
                        'created': 'created',
                        'description': 'Description'
                    },
                    'delete': {
                        'deleted': 'deleted',
                        'del_cat_from': 'Delete category from list',
                        'empty_only': 'you may delete only *empty categories*',
                        'can_delete_only_empty': 'You may delete only empty category.',
                        'is_base_cant_be_delete': "is *base*, *can't be* deleted."
                    },
                    'sort': {
                        'choose_move': 'Select actions to modify categorization:',
                        'not_enough': 'Too few categories to sort.'
                    },
                    'purify': {
                        'which_cat_purify_1': 'Which category from the',
                        'which_cat_purify_2': 'list you want to purify?',
                        'sure_delete_all_q': 'Are you sure you want to delete all the category positions?',
                        'i_am_sure': 'Yes I wont to delete all the category positions!',
                        'no_i_chged_mind': 'No I changed my mind!'
                    },
                    'update': {
                        'choose_cat_for_update': 'Выберите категорию для редактирования:',
                        'input_new_cat_name': 'Введите новое имя для категории',
                        'input_new_cat_descr': 'Теперь введите новое описание',
                        'your_chs_no_chngs': 'Вы решили оставить данные категории без изменений.'
                    }
                },
                'options': {
                    'buttons_style': {
                        'message': "Button display style \n(text, pictures or pictures with short text):",
                    },
                    'tips': {
                        'message': "Tooltip display option:",
                        'buttons': {'show': 'Show'}
                    },
                    'language': {
                        'message': ""
                    }
                },
                'list_menu': {
                    'buttons': {
                        'groups': 'Groups',
                        'categories': 'Categories',
                        'lists': 'Lists',
                        'options': 'Options',
                        'reload': 'Reload',
                        'edit': 'Change',
                        'to_category': 'To category',
                        'from_category': 'From category'
                    },
                    'buttons_short': {
                        'groups': 'Gr.',
                        'categories': 'Cat.',
                        'lists': 'Lst.',
                        'options': 'Opt.',
                        'reload': 'Rld.',
                        'edit': 'Chg.',
                        'to_category': 'To cat.',
                        'from_category': 'From cat.'
                    }
                },
                'lists_menu': {
                    'buttons': {
                        'switch': 'switch',
                        'edit': 'edit',
                        'add': 'add',
                        'share': 'share',
                        'delete': 'delete',
                        'clean': 'clean',
                        'back': 'back'
                    },
                    'buttons_short': {
                        'switch': 'swt.',
                        'edit': 'chg.',
                        'add': 'add',
                        'share': 'shr.',
                        'delete': 'del.',
                        'clean': 'cln.',
                        'back': 'bk.'
                    }
                },
                'groups_menu': {
                    'buttons': {
                        'switch': 'switch',
                        'edit': 'edit',
                        'add': 'add',
                        'sort': 'sort',
                        'delete': 'delete',
                        'back': 'back'
                    },
                    'buttons_short': {
                        'switch': 'swt.',
                        'edit': 'chg.',
                        'add': 'add',
                        'sort': 'sort',
                        'delete': 'del.',
                        'back': 'bk.'
                    }
                },
                'categories_menu': {
                    'buttons': {
                        'edit': 'edit',
                        'add': 'add',
                        'sort': 'sort',
                        'delete': 'delete',
                        'clean': 'clean',
                        'back': 'back'
                    },
                    'buttons_short': {
                        'edit': 'chg.',
                        'add': 'add',
                        'sort': 'sort',
                        'delete': 'del.',
                        'clean': 'cln.',
                        'back': 'bk.'
                    }
                },
                'share_menu': {  # "Доступ к списку", "Окружение", "Добавь меня", "↩️📦", "↩️📋"
                    'buttons': {
                        'access': 'Access to lists',
                        'surrounding': 'Surrounding',
                        'add_me': 'Facebook me',
                        'back_to_lists': 'Back to lists',
                        'back': 'back'
                    },
                    'buttons_short': {
                        'access': 'Access to lists',
                        'surrounding': 'Surrounding',
                        'add_me': 'Facebook me',
                        'back_to_lists': 'to lists',
                        'back': 'bk.'
                    }

                }
            }
        }
