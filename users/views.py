from django.views.generic import ListView

from users.models import Doctor



class AboutView(ListView):
    model = Doctor
    template_name = "develop.html"
    context_object_name = "doctors"