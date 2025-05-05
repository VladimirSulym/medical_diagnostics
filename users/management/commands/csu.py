import os
from django.core.management.base import BaseCommand
from dotenv import load_dotenv
from users.models import User

load_dotenv()

class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        user, created_user = User.objects.get_or_create(
            email=os.getenv("EMAIL_HOST_USER"),
            first_name="Владимир",
            last_name="Сулым",
            middle_name='Евгеньевич',
            phone="+7-985-123-45-67",
            is_superuser=True,
            is_active=True,
            is_staff=True,
        )
        user.set_password(os.getenv("CSU_PASS"))
        user.save()
        self.stdout.write(
            self.style.SUCCESS(f"Администратор успешно создан: {user.email}")
        )