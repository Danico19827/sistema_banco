from django.shortcuts import redirect, render
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib import messages
from django.db import transaction
from django.urls import reverse_lazy
from django.views.generic import TemplateView, CreateView
from .forms import RegistroClienteForm


class InicioView(TemplateView):
    template_name = 'inicio.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)


class RegistroView(CreateView):
    form_class = RegistroClienteForm
    template_name = 'registro.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()
        login(self.request, self.object)
        messages.success(self.request, f'¡Bienvenido {self.object.first_name}! Tu cuenta fue creada con éxito.')
        return redirect(self.get_success_url())


class LoginView(BaseLoginView):
    template_name = 'login.html'

    def form_valid(self, form):
        messages.success(self.request, f'¡Bienvenido de nuevo, {form.get_user().first_name}!')
        return super().form_valid(form)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        mock_cliente = {
            'nombre': self.request.user.first_name or self.request.user.username,
            'apellido': self.request.user.last_name,
            'email': self.request.user.email,
        }

        mock_cuentas = [
            {'tipo': 'Caja de Ahorro', 'numero': '**** 4521', 'saldo': 125430.50, 'moneda': 'ARS', 'estado': 'activa'},
            {'tipo': 'Cuenta Corriente', 'numero': '**** 7890', 'saldo': 8750.00, 'moneda': 'USD', 'estado': 'activa'},
        ]

        mock_transacciones = [
            {'fecha': '05/06/2026', 'tipo': 'Transferencia', 'descripcion': 'Transferencia a Juan Pérez', 'monto': -15000.00},
            {'fecha': '04/06/2026', 'tipo': 'Depósito', 'descripcion': 'Depósito en efectivo', 'monto': 50000.00},
            {'fecha': '03/06/2026', 'tipo': 'Pago', 'descripcion': 'Pago de servicios', 'monto': -8230.00},
            {'fecha': '01/06/2026', 'tipo': 'Transferencia', 'descripcion': 'Recibido de María López', 'monto': 25000.00},
            {'fecha': '28/05/2026', 'tipo': 'Compra', 'descripcion': 'Compra en comercio', 'monto': -12450.00},
            {'fecha': '25/05/2026', 'tipo': 'Depósito', 'descripcion': 'Depósito de sueldo', 'monto': 180000.00},
        ]

        context['cliente'] = mock_cliente
        context['cuentas'] = mock_cuentas
        context['transacciones'] = mock_transacciones
        return context


class TransferenciaView(LoginRequiredMixin, TemplateView):
    template_name = 'transferencia.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cuentas'] = [
            {'id': 1, 'tipo': 'Caja de Ahorro', 'numero': '**** 4521', 'saldo': 125430.50, 'moneda': 'ARS'},
            {'id': 2, 'tipo': 'Cuenta Corriente', 'numero': '**** 7890', 'saldo': 8750.00, 'moneda': 'USD'},
        ]
        return context

    def post(self, request, *args, **kwargs):
        mock_cuentas = [
            {'id': 1, 'tipo': 'Caja de Ahorro', 'numero': '**** 4521', 'saldo': 125430.50, 'moneda': 'ARS'},
            {'id': 2, 'tipo': 'Cuenta Corriente', 'numero': '**** 7890', 'saldo': 8750.00, 'moneda': 'USD'},
        ]
        datos = {
            'origen': next(
                (c['tipo'] + ' ' + c['numero'] for c in mock_cuentas if c['id'] == int(request.POST.get('cuenta_origen', 0))),
                'Cuenta seleccionada'
            ),
            'destino': request.POST.get('cuenta_destino', ''),
            'monto': request.POST.get('monto', '0.00'),
            'concepto': request.POST.get('concepto', ''),
        }
        return render(request, 'transferencia_exito.html', {'datos': datos})
