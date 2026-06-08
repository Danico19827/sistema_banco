# infrastructure/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from .models import Cliente

class RegistroClienteForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True, label='Nombre')
    last_name = forms.CharField(max_length=30, required=True, label='Apellido')

    telefono = forms.CharField(max_length=20, required=True, label='Teléfono')
    direccion = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=True, label='Dirección')

    dni = forms.CharField(max_length=8, required=True, label='DNI',
                           validators=[RegexValidator(r'^\d{7,8}$', 'El DNI debe tener 7 u 8 dígitos numéricos.')],
                           help_text='Documento Nacional de Identidad (7 u 8 dígitos)')
    fecha_nacimiento = forms.DateField(
        required=False, label='Fecha de nacimiento',
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text='Opcional'
    )
    genero = forms.ChoiceField(
        choices=Cliente.GENERO, required=False, label='Género',
        initial='N'
    )
    profesion = forms.CharField(
        max_length=100, required=False, label='Ocupación/Profesión',
        help_text='Opcional'
    )
    ingreso_mensual = forms.DecimalField(
        max_digits=12, decimal_places=2, required=False, label='Ingreso mensual',
        help_text='Opcional'
    )
    nivel_educativo = forms.ChoiceField(
        choices=Cliente.NIVEL_EDUCATIVO, required=False, label='Nivel educativo',
        initial='secundario'
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            cliente = user.cliente
            cliente.telefono = self.cleaned_data['telefono']
            cliente.direccion = self.cleaned_data['direccion']
            cliente.dni = self.cleaned_data['dni']
            if self.cleaned_data.get('fecha_nacimiento'):
                cliente.fecha_nacimiento = self.cleaned_data['fecha_nacimiento']
            if self.cleaned_data.get('genero'):
                cliente.genero = self.cleaned_data['genero']
            if self.cleaned_data.get('profesion'):
                cliente.profesion = self.cleaned_data['profesion']
            if self.cleaned_data.get('ingreso_mensual') is not None:
                cliente.ingreso_mensual = self.cleaned_data['ingreso_mensual']
            if self.cleaned_data.get('nivel_educativo'):
                cliente.nivel_educativo = self.cleaned_data['nivel_educativo']
            cliente.save()
        return user