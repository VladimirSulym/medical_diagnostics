import phonenumbers
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

GENDER_CHOICES = (
    ("M", "Мужской"),
    ("F", "Женский"),
)

CATEGORY_CHOICES = (
    ("none", "Нет категории"),
    ("second", "Вторая категория"),
    ("first", "Первая категория"),
    ("highest", "Высшая категория"),
)


def validate_phone_number(value):
    try:
        phone_number = phonenumbers.parse(value)
        if not phonenumbers.is_valid_number(phone_number):
            raise ValidationError("Неверный формат номера телефона")
    except phonenumbers.phonenumberutil.NumberParseException:
        raise ValidationError("Неверный формат номера телефона")


class User(AbstractUser):
    """
    Расширенная модель пользователя, включающая дополнительные поля для
    хранения персональной информации пациентов и сотрудников клиники
    """

    username = None
    email = models.EmailField(
        unique=True, verbose_name="Электронная почта", help_text="Адрес электронной почты пользователя"
    )
    phone = models.CharField(
        max_length=20,
        validators=[validate_phone_number],
        verbose_name="Телефон",
        help_text="Номер телефона пользователя в международном формате (например, +79991234567)",
        null=True,
        blank=True,
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
            "last_name",
            "first_name",
            "middle_name",
            "email",
        ]
        indexes = [
            models.Index(fields=["email"]),
        ]

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.last_name} {self.first_name}"


class Department(models.Model):
    """
    Модель отделения медицинской клиники
    """

    name = models.CharField(max_length=100, verbose_name="Название отделения", help_text="Название отделения клиники")
    description = models.TextField(verbose_name="Описание", blank=True, help_text="Подробное описание отделения")

    class Meta:
        verbose_name = "Отделение"
        verbose_name_plural = "Отделения"
        ordering = [
            "name",
        ]

    def __str__(self):
        return self.name


class Specialization(models.Model):
    """
    Модель специализации врача
    """

    name = models.CharField(
        max_length=100, verbose_name="Название специализации", help_text="Наименование врачебной специализации"
    )
    description = models.TextField(verbose_name="Описание", blank=True, help_text="Подробное описание специализации")

    class Meta:
        verbose_name = "Специализация"
        verbose_name_plural = "Специализации"
        ordering = ["name"]

    def __str__(self):
        return self.name


class PatientQuestionnaire(models.Model):
    """
    Модель анкеты пациента, содержащая медицинскую информацию
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    chronic_diseases = models.TextField(
        verbose_name="Хронические заболевания",
        help_text="Описание имеющихся хронических заболеваний",
        blank=True,
    )
    allergies = models.TextField(
        verbose_name="Аллергии и реакции",
        help_text="Информация об аллергиях и возможных реакциях на препараты",
        blank=True,
    )
    hereditary_diseases = models.TextField(
        verbose_name="Наследственные заболевания",
        help_text="Информация о предрасположенности к наследственным заболеваниям",
        blank=True,
    )
    treatment_preferences = models.TextField(
        verbose_name="Предпочтения в лечении",
        help_text="Предпочитаемые методы лечения",
        blank=True,
    )
    bad_habits = models.TextField(
        verbose_name="Вредные привычки",
        help_text="Описание имеющихся вредных привычек",
        blank=True,
    )
    lifestyle = models.TextField(
        verbose_name="Образ жизни",
        help_text="Описание образа жизни (питание, физическая активность и т.д.)",
        blank=True,
    )
    medications = models.TextField(
        verbose_name="Принимаемые препараты",
        help_text="Информация о принимаемых лекарственных препаратах",
        blank=True,
    )

    class Meta:
        verbose_name = "Анкета пациента"
        verbose_name_plural = "Анкеты пациентов"
        ordering = ["user__last_name", "user__first_name"]

    def __str__(self):
        return f"Анкета пациента: {self.user.last_name} {self.user.first_name}"


class Doctor(models.Model):
    """
    Модель врача, связанная с пользователем и отделением клиники
    """

    ACADEMIC_DEGREE_CHOICES = (
        ("none", "Нет"),
        ("candidate", "Кандидат медицинских наук"),
        ("doctor", "Доктор медицинских наук"),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        help_text="Связанный пользователь системы",
        unique=True,
        related_name="doctor",
    )
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, verbose_name="Отделение", help_text="Отделение, в котором работает врач"
    )
    specialization = models.ForeignKey(
        Specialization, on_delete=models.PROTECT, verbose_name="Специализация", help_text="Специализация врача"
    )
    experience = models.PositiveIntegerField(
        validators=[MinValueValidator(0)], verbose_name="Стаж работы (лет)", help_text="Опыт работы врача в годах"
    )
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        verbose_name="Рейтинг",
        default=0,
        help_text="Рейтинг врача по отзывам пациентов (от 0 до 5)",
    )
    academic_degree = models.CharField(
        max_length=20,
        choices=ACADEMIC_DEGREE_CHOICES,
        default="none",
        verbose_name="Ученая степень",
        help_text="Ученая степень врача",
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name="Категория",
        default="none",
        help_text="Квалификационная категория врача",
    )

    class Meta:
        verbose_name = "Врач"
        verbose_name_plural = "Врачи"
        ordering = [
            "user__last_name",
            "user__first_name",
        ]
        unique_together = ["user", "department"]

    def clean(self):
        super().clean()
        if self.experience > 60:
            raise ValidationError("Невероятно большой стаж работы")

    def __str__(self):
        return f"{self.user.last_name} {self.user.first_name} - {self.specialization}"
