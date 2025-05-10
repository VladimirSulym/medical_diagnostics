from datetime import timedelta, datetime

from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

from services.forms import ReviewForm, AppointmentForm
from services.models import Service, Appointment, Slot
from users.models import Doctor, Department


class HomeView(ListView):
    model = Service  # Модель, из которой будут браться данные
    template_name = "services/home.html"  # Имя шаблона в папке templates/
    context_object_name = "services"  # Имя переменной в контексте, в которой будут доступны данные

    def get_queryset(self):
        return Service.objects.filter(is_active=True).order_by("-duration")

    def get_context_data(self, **kwargs):
        # user = self.request.user
        context = super().get_context_data(**kwargs)

        context["doctors"] = Doctor.objects.all()
        context["departments"] = Department.objects.all()
        context["form"] = ReviewForm()
        return context

    def post(self, request, *args, **kwargs):
        post_data = request.POST.copy()
        if not post_data.get("doctor_rating"):
            post_data["doctor_rating"] = 0
        if not post_data.get("service_rating"):
            post_data["service_rating"] = 0

        form = ReviewForm(post_data)

        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user if not form.cleaned_data["is_anonymous"] else None
            try:
                review.save()
                messages.success(request, "Спасибо! Ваш отзыв успешно добавлен.")
                return redirect("services:home")
            except Exception as e:
                messages.error(request, f"Произошла ошибка при сохранении отзыва: {str(e)}")
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме.")

        # В случае ошибки возвращаем страницу с формой и ошибками
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        context["form"] = form
        return self.render_to_response(context)


class ServiceView(ListView):
    model = Service
    template_name = "services/services.html"
    context_object_name = "services"
    # paginate_by = 10
    # paginate_orphans = 5
    ordering = ["name"]

    def get_queryset(self):
        return Service.objects.filter(is_active=True).order_by("-duration")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context["doctors"] = Doctor.objects.all()
        context["departments"] = Department.objects.all().order_by("name")
        return context


class ServiceDetailView(DetailView):
    model = Service
    template_name = "services/service_detail.html"
    context_object_name = "service"


class AppointmentCreateView(LoginRequiredMixin, CreateView):
    model = Appointment
    template_name = "services/appointment_create.html"
    form_class = AppointmentForm
    success_url = reverse_lazy("services:services")

    def form_valid(self, form):
        form.instance.patient = self.request.user
        try:
            return super().form_valid(form)
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["doctors"] = Doctor.objects.all()
        context["services"] = Service.objects.filter(is_active=True)
        context["slots"] = Slot.objects.all()
        context["today"] = datetime.now().date()
        context["future_date"] = datetime.now().date() + timedelta(days=1)
        return context

    def get_success_url(self):
        messages.success(self.request, "Запись на прием успешно создана")
        return super().get_success_url()


class ContactsView(ListView):
    model = Service
    template_name = "services/contacts.html"
    context_object_name = "services"

    def get_queryset(self):
        return Service.objects.filter(is_active=True).order_by("-duration")

    def get_context_data(self, **kwargs):
        # user = self.request.user
        context = super().get_context_data(**kwargs)

        context["doctors"] = Doctor.objects.all()
        context["departments"] = Department.objects.all()
        context["form"] = ReviewForm()
        return context

    def post(self, request, *args, **kwargs):
        post_data = request.POST.copy()
        if not post_data.get("doctor_rating"):
            post_data["doctor_rating"] = 0
        if not post_data.get("service_rating"):
            post_data["service_rating"] = 0

        form = ReviewForm(post_data)

        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user if not form.cleaned_data["is_anonymous"] else None
            try:
                review.save()
                messages.success(request, "Спасибо! Ваш отзыв успешно добавлен.")
                return redirect("services:home")
            except Exception as e:
                messages.error(request, f"Произошла ошибка при сохранении отзыва: {str(e)}")
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме.")

        # В случае ошибки возвращаем страницу с формой и ошибками
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        context["form"] = form
        return self.render_to_response(context)
