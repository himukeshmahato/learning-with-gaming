from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import PDFDocument

class PDFDocumentForm(forms.ModelForm):
    class Meta:
        model = PDFDocument
        fields = ['title', 'file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter PDF Title'}),
            'file': forms.FileInput(attrs={'class': 'form-input'}),
        }

class UserRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-input'})
