from django.views.generic import ListView

from services.models import Service, Review
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

        return context

    def post(self, request, *args, **kwargs):
        print(request.POST)
        Review.objects.create(
            user=request.user if not request.POST.get("is_anonymous") else None,
            doctor=Doctor.objects.get(pk=request.POST.get("doctor_id")),
            service=Service.objects.get(pk=request.POST.get("service_id")),
            doctor_rating=request.POST.get("doctor_rating"),
            service_rating=request.POST.get("service_rating"),
            text=request.POST.get("text"),
            is_anonymous=True if request.POST.get("is_anonymous") else False,
        )
        return self.get(request, *args, **kwargs)

