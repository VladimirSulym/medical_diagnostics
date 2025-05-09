from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView

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
