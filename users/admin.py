from django.contrib import admin
from users.models import User, Doctor, Department, Specialization


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'middle_name', 'phone', 'is_active')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('last_name', 'first_name', 'middle_name')


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'department', 'experience')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    list_filter = ('specialization', 'department')
    ordering = ('user__last_name', 'user__first_name', 'user__middle_name')


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description',)
    ordering = ('name',)


@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    ordering = ('name',)
