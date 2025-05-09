import locale
from datetime import timedelta, datetime
from django.db.models import Avg

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator

from users.models import Department, Doctor, User, CATEGORY_CHOICES

locale.setlocale(locale.LC_ALL, "ru_RU.UTF-8")

NUMBER_SLOT = (
    (1, "07:00"),
    (2, "07:30"),
    (3, "08:00"),
    (4, "08:30"),
    (5, "09:00"),
    (6, "09:30"),
    (7, "10:00"),
    (8, "10:30"),
    (9, "11:00"),
    (10, "11:30"),
    (11, "12:00"),
    (12, "12:30"),
    (13, "13:00"),
    (14, "13:30"),
    (15, "14:00"),
    (16, "14:30"),
    (17, "15:00"),
    (18, "15:30"),
    (19, "16:00"),
    (20, "16:30"),
    (21, "17:00"),
    (22, "17:30"),
    (23, "18:00"),
    (24, "18:30"),
)


class Service(models.Model):
    """
    Модель медицинской услуги, оказываемой в клинике
    """

    doctors = models.ManyToManyField(
        Doctor, verbose_name="Врачи", help_text="Врачи, оказывающие данную услугу", blank=True, related_name="services"
    )
    name = models.CharField(
        max_length=200, verbose_name="Название услуги", help_text="Наименование медицинской услуги"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        verbose_name="Отделение",
        help_text="Отделение, к которому относится услуга",
        related_name="services",
    )
    duration = models.DurationField(
        verbose_name="Длительность",
        help_text="Продолжительность оказания услуги (должна быть кратна 30 минутам), заносится в секундах",
    )
    number_of_slots = models.IntegerField(
        verbose_name="Количество слотов",
        help_text="Количество временных слотов, необходимых для услуги",
        editable=False,
    )
    price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Стоимость", help_text="Базовая стоимость услуги"
    )
    description = models.TextField(verbose_name="Описание", help_text="Подробное описание услуги", blank=True)
    is_active = models.BooleanField(verbose_name="Активность", help_text="Доступность услуги для записи", default=True)
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        verbose_name="Рейтинг",
        default=0,
        help_text="Рейтинг услуги по отзывам пациентов (от 0 до 5)",
    )

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"
        ordering = [
            "department",
            "-duration",
            "name",
        ]
        unique_together = ["name", "department"]

    def __str__(self):
        return f"{self.name} ({self.duration})"

    def clean(self):
        duration_minutes = self.duration.total_seconds() / 60
        if duration_minutes % 30 != 0:
            raise ValidationError("Длительность услуги должна быть кратна 30 минутам")
        if self.duration > timedelta(hours=6):
            raise ValidationError("Длительность услуги не может превышать 6 часов")
        self.number_of_slots = int(duration_minutes / 30)

    def save(self, *args, **kwargs):
        self.clean()
        duration_minutes = self.duration.total_seconds() / 60
        self.number_of_slots = int(duration_minutes / 30)  # Обновление slots перед сохранением
        super().save(*args, **kwargs)


class Schedule(models.Model):
    """
    Модель расписания работы врача по дням недели
    """

    SHIFT_CHOICES = (
        (1, "1 Смена"),
        (2, "2 Смена"),
    )

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        verbose_name="Врач",
        help_text="Врач, для которого составляется расписание",
        related_name="schedules",
    )
    date = models.DateField(verbose_name="Дата", help_text="Дата рабочего дня")
    working_shift = models.IntegerField(
        choices=SHIFT_CHOICES, verbose_name="Рабочая смена", help_text="Номер рабочей смены (1 или 2)"
    )

    class Meta:
        verbose_name = "Расписание"
        verbose_name_plural = "Расписание"
        unique_together = ["doctor", "date"]
        ordering = [
            "date",
        ]

    def __str__(self):
        return f"{self.doctor} - {self.date}: {self.get_working_shift_display()}"

    def clean(self):
        from django.utils import timezone

        if self.date < timezone.now().date():
            raise ValidationError("Нельзя создать расписание на прошедшую дату")

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            slot_range = range(1, 13) if self.working_shift == 1 else range(13, 25)
            for number in slot_range:
                Slot.objects.create(schedule=self, date=self.date, number=number, status="free")

    def get_available_slots(self):
        return self.slots.filter(status="free")


class Slot(models.Model):
    STATUS_SLOT = (
        ("start", "start"),
        ("busy", "busy"),
        ("free", "free"),
    )

    schedule = models.ForeignKey(
        Schedule,
        on_delete=models.CASCADE,
        verbose_name="Расписание",
        help_text="Расписание, к которому относится слот",
        related_name="slots",
    )
    date = models.DateField(verbose_name="Дата", help_text="Дата слота")
    number = models.IntegerField(
        choices=NUMBER_SLOT, verbose_name="Слот", help_text="Порядковый номер временного слота"
    )
    status = models.CharField(
        choices=STATUS_SLOT,
        verbose_name="Статус слота",
        help_text="Текущий статус слота (свободен/занят/начало приема)",
    )
    previous_slot = models.OneToOneField(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="next_slot",
        default=None,
        editable=False,
        help_text="Предыдущий временной слот",
    )

    class Meta:
        verbose_name = "Слот"
        verbose_name_plural = "Слоты"
        ordering = ["date", "number"]
        unique_together = ["schedule", "number"]

    def __str__(self):
        return f"{self.schedule} - {self.date} {self.get_number_display()}"

    def save(self, *args, **kwargs):
        if not self.pk:
            if self.number not in [1, 13]:
                self.previous_slot = Slot.objects.filter(
                    schedule=self.schedule, date=self.date, number=self.number - 1
                ).first()
        super().save(*args, **kwargs)


class CategoryCoefficient(models.Model):
    """
    Модель коэффициентов стоимости услуг в зависимости от категории врача
    """

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        unique=True,
        verbose_name="Категория",
        help_text="Категория врача",
        default="none",
    )
    coefficient = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        verbose_name="Коэффициент",
        help_text="Коэффициент стоимости услуг для данной категории",
    )

    class Meta:
        verbose_name = "Коэффициент категории"
        verbose_name_plural = "Коэффициенты категорий"

    def __str__(self):
        return f"{self.get_category_display()} - {self.coefficient}"


def get_upload_path(instance, filename):
    """
    Генерирует путь загрузки для файлов на основе данных экземпляра и текущей даты.

    Эта функция создает путь для загрузки результатов диагностики.
    Файл помещается в определенную папку на основе атрибута patient
    переданного экземпляра. Если атрибут patient не указан, файл
    будет сохранен в папке "temp". Путь также включает текущую дату
    в формате "день месяц год".

    Параметры:
        instance: Объект, содержащий атрибут patient для определения
            папки хранения файла.
        filename: str
            Имя загружаемого файла.

    Возвращает:
        str: Сформированный путь для загружаемого файла.
    """
    today = datetime.now()
    folder = instance.patient if instance.patient else "temp"
    return f"diagnostic_results/{folder}/{today.strftime('%d %B %Y')}/{filename}"


class Review(models.Model):
    """
    Модель отзывов пациентов о врачах и услугах
    """

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        verbose_name="Пациент",
        help_text="Пациент, который оставил отзыв",
        related_name="reviews",
        null=True,
        blank=True,
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        verbose_name="Врач",
        help_text="Врач, о котором оставлен отзыв",
        related_name="reviews",
        null=True,
        blank=True,
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        verbose_name="Услуга",
        help_text="Услуга, о которой оставлен отзыв",
        related_name="reviews",
        null=True,
        blank=True,
    )
    text = models.TextField(verbose_name="Текст отзыва", help_text="Содержание отзыва", null=True, blank=True)
    doctor_rating = models.IntegerField(
        verbose_name="Оценка врача",
        help_text="Оценка работы врача от 0 до 5",
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        default=0,
    )
    service_rating = models.IntegerField(
        verbose_name="Оценка услуги",
        help_text="Оценка качества услуги от 0 до 5",
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        default=0,
    )
    is_anonymous = models.BooleanField(
        verbose_name="Анонимный отзыв", help_text="Отметка об анонимности отзыва", default=False
    )
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания", help_text="Дата создания отзыва")

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ["-date"]

    def __str__(self):
        author = f" ({self.user.get_full_name()})" if not self.is_anonymous and self.user else ""
        return f"Отзыв{author} от {self.date.strftime('%d.%m.%Y')}"

    def clean(self):
        if not any([self.text, self.doctor and self.doctor_rating > 0, self.service and self.service_rating > 0]):
            raise ValidationError("Необходимо заполнить хотя бы одно из: текст отзыва, оценку врача или оценку услуги")

    def save(self, *args, **kwargs):
        """
        Обновляет рейтинги связанных врача и услуги при сохранении отзыва. Этот метод переопределяет
        метод save родительского класса для добавления дополнительных операций - обновления среднего
        рейтинга связанного врача или услуги. Если с отзывом связан врач и указана валидная оценка
        врача, метод пересчитывает и обновляет общий рейтинг врача. Аналогично, если с отзывом связана
        услуга и указана валидная оценка услуги, пересчитывается и обновляется общий рейтинг услуги.
        """
        self.full_clean()
        super().save(*args, **kwargs)

        if self.doctor and self.doctor_rating > 0:
            avg_rating = Review.objects.filter(doctor=self.doctor, doctor_rating__gt=0).aggregate(
                Avg("doctor_rating")
            )["doctor_rating__avg"]
            if avg_rating:
                self.doctor.rating = round(avg_rating, 2)
                self.doctor.save()

        if self.service and self.service_rating > 0:
            avg_rating = Review.objects.filter(service=self.service, service_rating__gt=0).aggregate(
                Avg("service_rating")
            )["service_rating__avg"]
            if avg_rating:
                self.service.rating = round(avg_rating, 2)
                self.service.save()


class DiagnosticResult(models.Model):
    """
    Модель результатов диагностики
    """

    DIAGNOSTIC_STATUS = (
        ("pending", "Ожидает заполнения"),
        ("completed", "Заполнено"),
    )

    appointment = models.OneToOneField(
        "Appointment",
        on_delete=models.CASCADE,
        verbose_name="Запись на прием",
        help_text="Связанная запись на прием",
        related_name="diagnostic_result",
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.PROTECT,
        verbose_name="Врач",
        help_text="Врач, проводивший диагностику",
        related_name="diagnostic_results",
    )
    patient = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name="Пациент",
        help_text="Пациент, прошедший диагностику",
        related_name="diagnostic_results",
    )
    diagnosis = models.TextField(verbose_name="Диагноз", help_text="Поставленный диагноз", null=True, blank=True)
    recommendations = models.TextField(
        verbose_name="Рекомендации", help_text="Рекомендации по лечению", null=True, blank=True
    )
    medications = models.TextField(
        verbose_name="Назначенные лекарства", help_text="Список назначенных лекарств", null=True, blank=True
    )
    attachments = models.FileField(
        upload_to=get_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=["pdf", "jpg", "jpeg", "png"])],
        verbose_name="Прикрепленные файлы",
        help_text="Результаты анализов, снимки и другие файлы (PDF, JPG, PNG)",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=DIAGNOSTIC_STATUS,
        default="pending",
        verbose_name="Статус",
        help_text="Текущий статус диагностического результата",
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата создания", help_text="Дата создания записи"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Дата обновления", help_text="Дата последнего обновления"
    )

    class Meta:
        verbose_name = "Результат диагностики"
        verbose_name_plural = "Результаты диагностики"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Диагностика {self.patient} от {self.created_at.strftime('%d.%m.%Y')}"

    def clean(self):
        if self.status == "completed":
            if not self.diagnosis:
                raise ValidationError({"diagnosis": "Необходимо указать диагноз для завершенного результата"})
            if not self.recommendations:
                raise ValidationError(
                    {"recommendations": "Необходимо указать рекомендации для завершенного результата"}
                )
            if not self.medications:
                raise ValidationError(
                    {"medications": "Необходимо указать назначенные лекарства для завершенного результата"}
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Appointment(models.Model):
    """
    Модель записи пациента на прием к врачу
    """

    STATUS_CHOICES = (
        ("scheduled", "Запланирован"),
        ("completed", "Завершен"),
        ("cancelled", "Отменен"),
    )

    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пациент",
        help_text="Пациент, записанный на прием",
        related_name="appointments",
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        verbose_name="Врач",
        help_text="Врач, к которому осуществляется запись",
        related_name="appointments",
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        verbose_name="Услуга",
        help_text="Выбранная медицинская услуга",
        related_name="appointments",
    )
    slot = models.OneToOneField(
        Slot,
        on_delete=models.PROTECT,
        verbose_name="Слот",
        help_text="Временной слот записи",
        related_name="appointment",
        null=True,
        editable=False,
    )
    appointment_date = models.DateField(verbose_name="Дата приема", help_text="Дата планируемого приема")
    appointment_time = models.TimeField(verbose_name="Время приема", help_text="Время начала приема")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания", help_text="Дата создания записи")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="scheduled",
        verbose_name="Статус",
        help_text="Текущий статус записи",
    )
    notes = models.TextField(verbose_name="Примечания", help_text="Дополнительные заметки к записи", blank=True)
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Стоимость",
        help_text="Итоговая стоимость услуги с учетом категории врача",
        editable=False,
        default=0,
    )
    payment_status = models.BooleanField(default=False, verbose_name="Оплата", help_text="Статус оплаты приема")

    class Meta:
        verbose_name = "Запись на прием"
        verbose_name_plural = "Записи на прием"
        ordering = ["-date", "appointment_date", "appointment_time", "payment_status"]

    def __str__(self):
        return f"{self.patient} к {self.doctor} на {self.appointment_date} {self.appointment_time}"

    def get_slot_number(self):
        """Определяет номер слота по времени приема"""
        time_str = self.appointment_time.strftime("%H:%M")
        for number, slot_time in NUMBER_SLOT:
            if slot_time == time_str:
                return number
        return None

    def clean(self):

        if not self.doctor:
            raise ValidationError("Необходимо выбрать врача")

        if not self.service:
            raise ValidationError("Необходимо выбрать услугу")

        if not self.appointment_date:
            raise ValidationError("Необходимо указать дату приема")

        if not self.appointment_time:
            raise ValidationError("Необходимо указать время приема")

        if self.appointment_date < timezone.now().date():
            raise ValidationError("Нельзя создать запись на прошедшую дату")

        if self.doctor.department != self.service.department:
            raise ValidationError("Врач и услуга должны относиться к одному отделению")

        # if not self.appointment_date or not self.appointment_time:
        #     raise ValidationError("Необходимо указать дату и время приема")

        schedule = Schedule.objects.filter(doctor=self.doctor, date=self.appointment_date).first()

        if not schedule:
            raise ValidationError("Врач не работает в этот день")

        slot_number = self.get_slot_number()
        if not slot_number:
            raise ValidationError("Некорректное время приема")

        initial_slot = Slot.objects.filter(schedule=schedule, number=slot_number, status="free").first()

        if not initial_slot:
            raise ValidationError("Выбранное время недоступно для записи")

        required_slots = self.service.number_of_slots
        consecutive_slots = []
        current_slot = initial_slot

        while current_slot and current_slot.status == "free" and len(consecutive_slots) < required_slots:
            consecutive_slots.append(current_slot)
            current_slot = current_slot.next_slot if hasattr(current_slot, "next_slot") else None

        if len(consecutive_slots) < required_slots:
            alternative_schedules = Schedule.objects.filter(
                doctor=self.doctor, date__gt=self.appointment_date
            ).order_by("date")[:5]

            alternative_dates = [schedule.date for schedule in alternative_schedules]
            raise ValidationError(
                f"Недостаточно свободного времени для услуги '{self.service.name}' "
                f"({self.service.duration}). "
                f"Попробуйте следующие даты: {', '.join(map(str, alternative_dates))}"
            )

        self.slot = initial_slot

    def update_slots_status(self, new_status):
        """Обновляет статус для всех слотов, связанных с этой записью"""
        required_slots = self.service.number_of_slots
        current_slot = self.slot

        for i in range(required_slots):
            if current_slot:
                if new_status == "busy" and i == 0:
                    current_slot.status = "start"
                else:
                    current_slot.status = new_status
                current_slot.save()
                current_slot = current_slot.next_slot if hasattr(current_slot, "next_slot") else None

    def save(self, *args, **kwargs):
        if not self.pk:
            self.full_clean()

            # Расчет стоимости на основе категории врача
            category = self.doctor.category if hasattr(self.doctor, "category") else "none"
            try:
                coefficient = CategoryCoefficient.objects.get(category=category).coefficient
            except CategoryCoefficient.DoesNotExist:
                coefficient = 1
                print(
                    f"WARNING: Коэффициент для категории '{category}' не найден, используется коэффициент по умолчанию 1.0"
                )
            self.cost = self.service.price * coefficient

            super().save(*args, **kwargs)

            self.update_slots_status("busy")

            # required_slots = self.service.number_of_slots
            # current_slot = self.slot
            #
            # for i in range(required_slots):
            #     if current_slot:
            #         if i == 0:
            #             current_slot.status = 'start'
            #         else:
            #             current_slot.status = 'busy'
            #         current_slot.save()
            #         current_slot = current_slot.next_slot if hasattr(current_slot, 'next_slot') else None
        else:
            old_instance = Appointment.objects.get(pk=self.pk)
            if old_instance.status != self.status:
                if old_instance.status == "completed" or old_instance.status == "cancelled":
                    raise ValidationError("Нельзя изменить статус завершенного или отмененного приема")
                if self.status == "cancelled":
                    self.update_slots_status("free")
                    self.slot = None
            super().save(*args, **kwargs)
