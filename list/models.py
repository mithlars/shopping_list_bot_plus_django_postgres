from django.db import models
from django.contrib.auth.models import User
from .constants import GENDER_CHOICES


class Purchases(models.Model):
    name = models.CharField(max_length=250, verbose_name='Purchase')
    description = models.TextField(null=True, blank=True, verbose_name='Description')
    published = models.DateTimeField(auto_now_add=True)
    list = models.ForeignKey('Lists', on_delete=models.CASCADE, verbose_name='List')

    class Meta:
        verbose_name_plural = 'Purchases'
        verbose_name = 'Purchase'
        ordering = ['name']

    def __str__(self):
        return f"{self.id} {self.name}"


class Categories(models.Model):
    name = models.CharField(max_length=150, verbose_name='Name')
    description = models.TextField(null=True, blank=True, verbose_name='Description')
    order_number = models.SmallIntegerField(null=True, blank=True)
    published = models.DateTimeField(auto_now_add=True)
    purchases = models.ManyToManyField('Purchases', blank=True)
    list = models.ForeignKey('Lists', on_delete=models.CASCADE, verbose_name='List')

    # groups = models.ManyToManyField('Groups', blank=True, verbose_name='Groups')

    class Meta:
        verbose_name_plural = 'Categories'
        verbose_name = 'Category'
        ordering = ['order_number']

    def __str__(self):
        return f"{self.id} {self.name}"


class Groups(models.Model):
    name = models.CharField(max_length=150, verbose_name='Group')
    description = models.TextField(null=True, blank=True, verbose_name='Description')
    order_number = models.SmallIntegerField(null=True, blank=True)
    published = models.DateTimeField(auto_now_add=True)
    list = models.ForeignKey('Lists', on_delete=models.CASCADE, verbose_name='List')
    categories = models.ManyToManyField('Categories', blank=True, verbose_name='Categories', related_name='groups')

    class Meta:
        verbose_name_plural = 'Groups'
        verbose_name = 'Group'
        ordering = ['published']

    def __str__(self):
        return f"{self.id} {self.name}"


class Lists(models.Model):
    name = models.CharField(max_length=150, verbose_name='Shopping list')
    description = models.TextField(null=True, blank=True, verbose_name='Description')
    published = models.DateTimeField(auto_now_add=True)
    blank_category = models.ForeignKey('Categories', null=True, blank=True, on_delete=models.SET_NULL,
                                       verbose_name='Blank_category')
    telegram_current_group = models.ForeignKey('Groups', null=True, blank=True, on_delete=models.SET_NULL,
                                               verbose_name='Telegram_current_group')
    owner = models.ForeignKey('UserProfile', on_delete=models.CASCADE, verbose_name='Owner', related_name='My_lists')

    class Meta:
        verbose_name_plural = 'Lists'
        verbose_name = 'List'
        ordering = ['published']

    def __str__(self):
        return f"{self.id} {self.name}"


class UserProfile(models.Model):
    name = models.CharField(max_length=150, blank=True)
    published = models.DateTimeField(auto_now_add=True)

    telegram_user_id = models.IntegerField(null=True, blank=True)
    telegram_username = models.CharField(max_length=270, null=True, blank=True)
    telegram_firstname = models.CharField(max_length=270, null=True, blank=True)
    telegram_lastname = models.CharField(max_length=270, null=True, blank=True)
    telegram_registering_date = models.DateTimeField(null=True, blank=True)
    stopped_in_telegram = models.BooleanField(null=True, blank=True)
    telegram_current_list = models.ForeignKey('Lists', null=True, blank=True, on_delete=models.SET_NULL,
                                              verbose_name='current_ist', related_name="user_profile_for_current")
    telegram_tips = models.BooleanField(default=True, verbose_name='telegram_tips')

    BUTTONS_TEXT_CHOICE = [
        ('text', 'Text'),
        ('pics', 'Pictures'),
        ('both', 'Pictures with short text')
    ]
    telegram_buttons_style = models.CharField(max_length=4, choices=BUTTONS_TEXT_CHOICE,
                                              default='text', verbose_name='text_on_buttons')

    LANGUAGES = [
        ('bel', 'Беларуская'),
        ('en', 'English'),
        ('hy', 'Հայերեն'),
        ('ru', 'Русски'),
        ('uk', 'Українська'),
    ]
    telegram_language = models.CharField(max_length=4, choices=LANGUAGES,
                                         default='ru', verbose_name='text_on_buttons')

    friends = models.ManyToManyField('UserProfile', null=True, blank=True,
                                     verbose_name='friends', related_name="user_profile_friends")

    lists = models.ManyToManyField(to='Lists', blank=True, verbose_name='Lists')

    last_active_date_time = models.DateTimeField(null=True, blank=True)

    web_registering_date = models.DateTimeField(null=True, blank=True)
    web_language_code = models.CharField(max_length=10, null=True, blank=True)
    web_firstname = models.CharField(max_length=270, null=True, blank=True)
    web_lastname = models.CharField(max_length=270, null=True, blank=True)

    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, verbose_name='user',
                             related_name='profile')

    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)

    class Meta:
        verbose_name_plural = 'UserProfile'
        verbose_name = 'UserProfile'
        ordering = ['published']

    def __str__(self):
        return f"{self.id} {self.name} {self.lists}"
