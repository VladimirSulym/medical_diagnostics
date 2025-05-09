from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView

from services.models import Slot, Schedule
from users.forms import UserRegistrationForm
from users.models import Doctor, Department, User


class AboutView(ListView):
    model = Doctor
    template_name = "users/about.html"
    context_object_name = "doctors"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context["doctors"] = Doctor.objects.all()
        context["departments"] = Department.objects.all().order_by("name")
        return context


class ContactView(ListView):
    model = Doctor
    template_name = "contact.html"
    context_object_name = "doctors"


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

    # def get_queryset(self):
    #     return User.objects.filter(id=self.request.user.id)

    def get_context_data(self, **kwargs):
        user = self.request.user

        context = super().get_context_data(**kwargs)
        context['appointments'] = user.appointments.all()
        context['reviews'] = user.reviews.all()

        if hasattr(user, 'doctor') and user.doctor is not None:
            doctor = user.doctor
            context['slots'] = Slot.objects.filter(schedule__doctor=doctor).order_by('-date')
            context['schedules'] = Schedule.objects.filter(doctor=doctor)

        return context
