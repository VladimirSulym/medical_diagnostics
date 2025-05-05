from django.contrib.auth.models import AbstractUser
from django.db import models

GENDER_CHOICES = (
    ("M", "Мужской"),
    ("F", "Женский"),
)


class User(AbstractUser):
    username = None
    email = models.EmailField(
        unique=True, verbose_name="Электронная почта", help_text="Адрес электронной почты пользователя"
    )
    phone = models.CharField(
        max_length=20, verbose_name="Телефон", help_text="Номер телефона пользователя", null=True, blank=True
    )
    middle_name = models.CharField(
        max_length=150, verbose_name="Отчество", help_text="Отчество пользователя", null=True, blank=True
    )
    gender = models.CharField(
        max_length=1, choices=GENDER_CHOICES, verbose_name="Пол", help_text="Пол пользователя", null=True, blank=True
    )
    birth_date = models.DateField(
        verbose_name="Дата рождения", help_text="Дата рождения пользователя", null=True, blank=True
    )
    insurance_policy = models.CharField(
        max_length=16, verbose_name="Страховой полис", help_text="Номер страхового полиса", null=True, blank=True
    )
    document = models.CharField(
        max_length=20, verbose_name="Документ", help_text="Паспорт или свидетельство о рождении", null=True, blank=True
    )
    address = models.TextField(verbose_name="Адрес", help_text="Полный адрес пользователя", null=True, blank=True)
    telegram = models.CharField(
        max_length=150, verbose_name="Telegram", help_text="Username в Telegram", null=True, blank=True
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = [
            "email",
        ]

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.last_name} {self.first_name}"
