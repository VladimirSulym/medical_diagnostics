from django import forms
from django.utils import timezone

from .models import Review, Appointment


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["doctor", "service", "doctor_rating", "service_rating", "text", "is_anonymous"]
        widgets = {
            "doctor_rating": forms.NumberInput(attrs={"min": "0", "max": "5", "class": "form-control"}),
            "service_rating": forms.NumberInput(attrs={"min": "0", "max": "5", "class": "form-control"}),
            "text": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "is_anonymous": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                    "type": "checkbox",
                    "id": "anonymous",
                    "onchange": "toggleAuthor()",
                }
            ),
            "doctor": forms.Select(attrs={"class": "form-control", "id": "doctor"}),
            "service": forms.Select(
                attrs={
                    "class": "form-control",
                    "id": "service",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Делаем поля необязательными, так как по логике модели
        # должно быть заполнено хотя бы одно из трёх: текст или рейтинги
        for field in self.fields:
            self.fields[field].required = False

    def clean(self):
        cleaned_data = super().clean()
        # text = cleaned_data.get('text')
        doctor_rating = cleaned_data.get("doctor_rating")
        service_rating = cleaned_data.get("service_rating")
        doctor = cleaned_data.get("doctor")
        service = cleaned_data.get("service")

        # if not (text or (doctor and doctor_rating > 0) or (service and service_rating > 0)):
        # self.add_error(None, "Необходимо заполнить хотя бы одно из: текст отзыва, оценку врача или оценку услуги")

        if doctor_rating and not doctor:
            self.add_error("doctor", "Нельзя указать оценку врача без выбора врача")

        if service_rating and not service:
            self.add_error("service", "Нельзя указать оценку услуги без выбора услуги")

        return cleaned_data


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["service", "doctor", "appointment_date", "appointment_time", "notes"]
        widgets = {
            "service": forms.Select(attrs={"class": "form-control"}),
            "doctor": forms.Select(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "appointment_date": forms.DateInput(attrs={"type": "date", "class": "form-control", "required": True}),
            "appointment_time": forms.TimeInput(attrs={"type": "time", "class": "form-control", "required": True}),
        }

    def clean(self):
        cleaned_data = super().clean()
        service = cleaned_data.get("service")
        doctor = cleaned_data.get("doctor")
        appointment_date = cleaned_data.get("appointment_date")
        appointment_time = cleaned_data.get("appointment_time")

        if not appointment_date:
            self.add_error("appointment_date", "Необходимо указать дату приема")

        if not appointment_time:
            self.add_error("appointment_time", "Необходимо указать время приема")

        if not service:
            self.add_error("service", "Необходимо выбрать услугу")

        if not doctor:
            self.add_error("doctor", "Необходимо выбрать врача")

        if appointment_date and appointment_date < timezone.now().date():
            self.add_error("appointment_date", "Дата приема не может быть в прошлом")

        # Проверка доступности врача
        if doctor and appointment_date and appointment_time:
            if Appointment.objects.filter(
                doctor=doctor, appointment_date=appointment_date, appointment_time=appointment_time, status="scheduled"
            ).exists():
                self.add_error("appointment_time", "Выбранное время уже занято")

        return cleaned_data
