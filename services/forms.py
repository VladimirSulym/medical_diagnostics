from django import forms

from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['doctor', 'service', 'doctor_rating', 'service_rating', 'text', 'is_anonymous']
        widgets = {
            'doctor_rating': forms.NumberInput(attrs={
                'min': '0',
                'max': '5',
                'class': 'form-control'
            }),
            'service_rating': forms.NumberInput(attrs={
                'min': '0',
                'max': '5',
                'class': 'form-control'
            }),
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'is_anonymous': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'type': "checkbox",
                'id': "anonymous",
                'onchange': "toggleAuthor()"
            }),
            'doctor': forms.Select(attrs={
                'class': 'form-control',
                'id': "doctor"
            }),
            'service': forms.Select(attrs={
                'class': 'form-control',
                'id': "service",

            })       
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
        doctor_rating = cleaned_data.get('doctor_rating')
        service_rating = cleaned_data.get('service_rating')
        doctor = cleaned_data.get('doctor')
        service = cleaned_data.get('service')

        # if not (text or (doctor and doctor_rating > 0) or (service and service_rating > 0)):
        #     self.add_error(None, "Необходимо заполнить хотя бы одно из: текст отзыва, оценку врача или оценку услуги")

        if doctor_rating and not doctor:
            self.add_error('doctor', "Нельзя указать оценку врача без выбора врача")

        if service_rating and not service:
            self.add_error('service', "Нельзя указать оценку услуги без выбора услуги")

        return cleaned_data
