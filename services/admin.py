from django.contrib import admin

from services.models import Service, Appointment, Schedule, Slot, CategoryCoefficient, DiagnosticResult, Review


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "department", "duration", "price", "is_active", "rating")
    list_filter = ("department", "is_active")
    ordering = ("department", "-duration", "name")
    search_fields = ("name", "description")
    readonly_fields = ("number_of_slots",)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "doctor",
        "service",
        "appointment_date",
        "appointment_time",
        "status",
        "cost",
        "payment_status",
    )
    list_filter = ("status", "appointment_date", "doctor")
    search_fields = ("patient__email", "doctor__last_name", "service__name")
    ordering = ("-date", "appointment_date", "appointment_time")
    readonly_fields = ("date", "slot")


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ("doctor", "date", "working_shift")
    list_filter = ("working_shift", "date")
    search_fields = ("doctor__last_name",)
    ordering = ("date",)


@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display = ("schedule", "appointment__service", "date", "number", "status")
    list_filter = ("status", "date")
    search_fields = (
        "schedule__doctor__user__last_name__icontains",
        "schedule__doctor__user__first_name__icontains",
        "date",
    )
    ordering = ("date", "number")
    readonly_fields = ("previous_slot",)


@admin.register(CategoryCoefficient)
class CategoryCoefficientAdmin(admin.ModelAdmin):
    list_display = ("category", "coefficient")
    list_filter = ("category",)
    ordering = ("category",)


@admin.register(DiagnosticResult)
class DiagnosticResultAdmin(admin.ModelAdmin):
    list_display = (
        "appointment",
        "doctor",
        "patient",
        "status",
        "created_at",
        "updated_at",
    )
    list_filter = ("created_at",)
    search_fields = (
        "appointment__patient__user__last_name__icontains",
        "appointment__doctor__user__last_name__icontains",
        "diagnosis",
    )
    ordering = ("-created_at",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "doctor",
        "service",
        "date",
        "doctor_rating",
        "service_rating",
        "is_anonymous",
    )
    list_filter = ("doctor", "service", "date")
    search_fields = (
        "user__user__last_name__icontains",
        "user__user__first_name__icontains",
    )
    ordering = ("-date",)
