from datetime import datetime, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView

from services.models import Slot, Schedule, Service, DiagnosticResult
from users.forms import UserRegistrationForm
from users.models import Doctor, Department, User

from django.contrib import messages


class AboutView(ListView):
    model = Doctor
    template_name = "users/about.html"
    context_object_name = "doctors"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context["doctors"] = Doctor.objects.all()
        context["departments"] = Department.objects.all().order_by("name")
        return context


class RegistrationView(CreateView):
    model = User
    form_class = UserRegistrationForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data["password1"])
        user.save()
        return super().form_valid(form)


class ProfileView(LoginRequiredMixin, ListView):
    model = User
    template_name = "users/profile.html"
    context_object_name = "users"

    def get_queryset(self):
        # Возвращаем только текущего пользователя
        return User.objects.filter(id=self.request.user.id)

    def get_context_data(self, **kwargs):
        user = self.request.user

        context = super().get_context_data(**kwargs)
        context["appointments"] = user.appointments.all()
        context["reviews"] = user.reviews.all()
        context["today"] = datetime.now().date()
        context["future_date"] = datetime.now().date() + timedelta(days=1)

        if hasattr(user, "doctor") and user.doctor is not None:
            doctor = user.doctor
            context["slots"] = Slot.objects.filter(schedule__doctor=doctor).order_by("-date")
            context["schedules"] = Schedule.objects.filter(doctor=doctor)

        return context

    def post(self, request, *args, **kwargs):
        user = self.request.user
        if not request.POST.get("appointment_id"):
            date = datetime.strptime(request.POST.get("date"), "%Y-%m-%d").date()
            working_shift = int(request.POST.get("working_shift"))

            if hasattr(user, "doctor") and user.doctor:
                try:
                    schedule = Schedule.objects.create(doctor=user.doctor, working_shift=working_shift, date=date)
                    messages.success(request, "Расписание успешно создано")
                except IntegrityError:
                    messages.error(request, f"Расписание на эту дату уже существует")
            else:
                messages.error(request, "Данную форму могут заполнять только доктора")
        else:

            try:
                appointment_id = request.POST.get("appointment_id")
                patient_id = request.POST.get('patient_id')
                diagnosis = request.POST.get('diagnosis')
                recommendations = request.POST.get('recommendations')
                medications = request.POST.get('medications')
                status = request.POST.get('status')

                # Проверяем, что пользователь является доктором
                if not hasattr(user, 'doctor') or not user.doctor:
                    messages.error(request, "Только доктор может создавать диагностические результаты")
                    return self.get(request, *args, **kwargs)

                # Получаем объекты из базы данных
                try:
                    from services.models import Appointment
                    appointment = Appointment.objects.get(id=appointment_id)
                    patient = User.objects.get(id=patient_id)
                except (Appointment.DoesNotExist, User.DoesNotExist):
                    messages.error(request, "Указанные запись на прием или пациент не найдены")
                    return self.get(request, *args, **kwargs)

                result, created = DiagnosticResult.objects.update_or_create(
                    doctor=user.doctor,
                    patient=patient,
                    appointment=appointment,
                    defaults={
                        'diagnosis': diagnosis,
                        'recommendations': recommendations,
                        'medications': medications,
                        'status': status
                    }
                )

                if 'attachment' in request.FILES:
                    result.attachments = request.FILES['attachment']
                    result.save()

                messages.success(request, "Диагностический результат успешно сохранен")

            except Exception as e:
                messages.error(request, f"Произошла ошибка при сохранении результата: {str(e)}")
                return self.get(request, *args, **kwargs)

            # appointment = request.POST.get("appointment")
            # patient = request.POST.get('patient')
            # diagnosis = request.POST.get('diagnosis')
            # recommendations = request.POST.get('recommendations')
            # medications = request.POST.get('medications')
            # status = request.POST.get('status')
            #
            # if 'attachment' in request.FILES:
            #     attachment = request.FILES['attachment']
            #
            # result, created = DiagnosticResult.objects.update_or_create(
            #     # Поиск по этим параметрам
            #     doctor=user.doctor,
            #     patient=patient,
            #     appointment=appointment,
            #     # Обновление или установка этих полей
            #     defaults={
            #         'diagnosis': diagnosis,
            #         'recommendations': recommendations,
            #         'medications': medications,
            #         'status': status
            #     })
            # result.save()

        # if 'attachment' in request.FILES and not attachment.content_type.startswith('image/'):
        #     messages.error(request, "Прикрепленный файл должен быть изображением")
        #     return HttpResponseBadRequest()

        self.object_list = self.get_queryset()
        context = self.get_context_data()
        return self.render_to_response(context)


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    fields = [
        "first_name",
        "last_name",
        "middle_name",
        "phone",
        "birth_date",
        "email",
        "gender",
        "insurance_policy",
        "document",
        "address",
        "telegram",
    ]
    template_name = "users/user_update.html"
    success_url = reverse_lazy("users:profile")

