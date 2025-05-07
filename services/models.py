from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from users.models import Department, Doctor, User, CATEGORY_CHOICES


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
    doctors = models.ManyToManyField(Doctor, verbose_name="Врачи", blank=True, related_name='services')
    name = models.CharField(max_length=200, verbose_name="Название услуги")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name="Отделение", related_name='services')
    duration = models.DurationField(verbose_name="Длительность")
    number_of_slots = models.IntegerField(verbose_name="Количество слотов", editable=False)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Стоимость")
    description = models.TextField(verbose_name="Описание", blank=True)
    is_active = models.BooleanField(verbose_name="Активность", default=True)

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"
        ordering = [
            "department",
            "-duration",
            "name",
        ]
        unique_together = ['name', 'department']

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

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, verbose_name="Врач", related_name='schedules')
    date = models.DateField(verbose_name="Дата")
    working_shift = models.IntegerField(choices=SHIFT_CHOICES, verbose_name="Рабочая смена")

    class Meta:
        verbose_name = "Расписание"
        verbose_name_plural = "Расписание"
        unique_together = ['doctor', 'date']
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
                Slot.objects.create(
                    schedule=self,
                    date=self.date,
                    number=number,
                    status="free"
                )
    
    def get_available_slots(self):
        return self.slots.filter(status="free")


class Slot(models.Model):
    STATUS_SLOT = (
        ("start", "start"),
        ("busy", "busy"),
        ("free", "free"),
    )

    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, verbose_name="Расписание", related_name='slots')
    date = models.DateField(verbose_name="Дата")
    number = models.IntegerField(choices=NUMBER_SLOT, verbose_name="Слот")
    status = models.CharField(choices=STATUS_SLOT, verbose_name="Статус слота")
    previous_slot = models.OneToOneField('self', on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='next_slot', default=None, editable=False)

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
                    schedule=self.schedule,
                    date=self.date,
                    number=self.number - 1
                ).first()
        super().save(*args, **kwargs)


class CategoryCoefficient(models.Model):
    """
    Модель коэффициентов стоимости услуг в зависимости от категории врача
    """

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, unique=True, verbose_name="Категория", default='none')
    coefficient = models.DecimalField(max_digits=3, decimal_places=2, verbose_name="Коэффициент")

    class Meta:
        verbose_name = "Коэффициент категории"
        verbose_name_plural = "Коэффициенты категорий"

    def __str__(self):
        return f"{self.get_category_display()} - {self.coefficient}"


class Appointment(models.Model):
    """
    Модель записи пациента на прием к врачу
    """
    STATUS_CHOICES = (
        ('scheduled', 'Запланирован'),
        ('completed', 'Завершен'),
        ('cancelled', 'Отменен'),
    )

    patient = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пациент", related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, verbose_name="Врач", related_name='appointments')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name="Услуга", related_name='appointments')
    slot = models.OneToOneField(Slot, on_delete=models.PROTECT, verbose_name="Слот", related_name='appointment',
                                null=True, editable=False)
    appointment_date = models.DateField(verbose_name="Дата приема")
    appointment_time = models.TimeField(verbose_name="Время приема")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', verbose_name="Статус")
    notes = models.TextField(verbose_name="Примечания", blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Стоимость", editable=False, default=0)

    class Meta:
        verbose_name = "Запись на прием"
        verbose_name_plural = "Записи на прием"
        ordering = ['-date', 'appointment_date', 'appointment_time']

    def __str__(self):
        return f"{self.patient} к {self.doctor} на {self.appointment_date} {self.appointment_time}"

    def get_slot_number(self):
        """Определяет номер слота по времени приема"""
        time_str = self.appointment_time.strftime('%H:%M')
        for number, slot_time in NUMBER_SLOT:
            if slot_time == time_str:
                return number
        return None

    def clean(self):
        if self.appointment_date < timezone.now().date():
            raise ValidationError("Нельзя создать запись на прошедшую дату")

        if self.doctor.department != self.service.department:
            raise ValidationError("Врач и услуга должны относиться к одному отделению")

        if not self.appointment_date or not self.appointment_time:
            raise ValidationError("Необходимо указать дату и время приема")

        schedule = Schedule.objects.filter(
            doctor=self.doctor,
            date=self.appointment_date
        ).first()

        if not schedule:
            raise ValidationError("Врач не работает в этот день")

        slot_number = self.get_slot_number()
        if not slot_number:
            raise ValidationError("Некорректное время приема")

        initial_slot = Slot.objects.filter(
            schedule=schedule,
            number=slot_number,
            status='free'
        ).first()

        if not initial_slot:
            raise ValidationError("Выбранное время недоступно для записи")

        required_slots = self.service.number_of_slots
        consecutive_slots = []
        current_slot = initial_slot

        while (current_slot and current_slot.status == 'free' and
               len(consecutive_slots) < required_slots):
            consecutive_slots.append(current_slot)
            current_slot = current_slot.next_slot if hasattr(current_slot, 'next_slot') else None

        if len(consecutive_slots) < required_slots:
            alternative_schedules = Schedule.objects.filter(
                doctor=self.doctor,
                date__gt=self.appointment_date
            ).order_by('date')[:5]

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
                if new_status == 'busy' and i == 0:
                    current_slot.status = 'start'
                else:
                    current_slot.status = new_status
                current_slot.save()
                current_slot = current_slot.next_slot if hasattr(current_slot, 'next_slot') else None

    def save(self, *args, **kwargs):
        if not self.pk:
            self.full_clean()

            # Расчет стоимости на основе категории врача
            category = self.doctor.category if hasattr(self.doctor, 'category') else 'none'
            try:
                coefficient = CategoryCoefficient.objects.get(category=category).coefficient
            except CategoryCoefficient.DoesNotExist:
                coefficient = 1
                print(
                    f"WARNING: Коэффициент для категории '{category}' не найден, используется коэффициент по умолчанию 1.0")
            self.cost = self.service.price * coefficient

            super().save(*args, **kwargs)
            
            self.update_slots_status('busy')

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
                if old_instance.status == 'completed' or old_instance.status == 'cancelled':
                    raise ValidationError("Нельзя изменить статус завершенного или отмененного приема")
                if self.status == 'cancelled':
                    self.update_slots_status('free')
                    self.slot = None
            super().save(*args, **kwargs)
