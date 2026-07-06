from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List, Optional, Dict

from domain.entities import CuentaEntity, TransaccionEntity, PrestamoEntity, CuotaEntity
from domain.ports import RepositorioCuenta, RepositorioTransaccion, RepositorioPrestamo, RepositorioCliente
from domain.rules import (
    validar_saldo_suficiente,
    validar_monto_positivo,
    simular_cuotas_frances,
    simular_cuotas_aleman,
    CuotaSimulada,
    calcular_score_crediticio,
)


@dataclass
class ResultadoTransferencia:
    exitoso: bool
    mensaje: str


class RealizarTransferencia:
    def __init__(
        self,
        repo_cuenta: RepositorioCuenta,
        repo_tx: RepositorioTransaccion,
    ):
        self._repo_cuenta = repo_cuenta
        self._repo_tx = repo_tx

    def ejecutar(
        self,
        cuenta_origen_id: int,
        destino_busqueda: str,
        monto: Decimal,
        descripcion: str = '',
    ) -> ResultadoTransferencia:
        if not validar_monto_positivo(monto):
            return ResultadoTransferencia(exitoso=False, mensaje='El monto debe ser un número positivo.')

        destino = self._repo_cuenta.buscar_por_alias_o_cvu(destino_busqueda)
        if destino is None:
            return ResultadoTransferencia(exitoso=False, mensaje='La cuenta destino no existe.')

        if cuenta_origen_id == destino.id:
            return ResultadoTransferencia(exitoso=False, mensaje='No podés transferir a la misma cuenta.')

        ids = sorted([cuenta_origen_id, destino.id])
        origen = self._repo_cuenta.buscar_por_id_con_bloqueo(ids[0])
        destino_locked = self._repo_cuenta.buscar_por_id_con_bloqueo(ids[1])

        id_a_entidad = {origen.id: origen, destino_locked.id: destino_locked}
        cuenta_origen = id_a_entidad[cuenta_origen_id]
        cuenta_destino = id_a_entidad[destino.id]

        if cuenta_origen.estado != 'activa':
            return ResultadoTransferencia(exitoso=False, mensaje='Cuenta origen inactiva.')
        if cuenta_destino.estado != 'activa':
            return ResultadoTransferencia(exitoso=False, mensaje='Cuenta destino inactiva.')
        if not validar_saldo_suficiente(cuenta_origen.saldo, monto):
            return ResultadoTransferencia(exitoso=False, mensaje='Saldo insuficiente.')

        self._repo_cuenta.incrementar_saldo(cuenta_origen.id, -monto)
        self._repo_cuenta.incrementar_saldo(cuenta_destino.id, monto)

        self._repo_tx.crear(TransaccionEntity(
            id=0,
            tipo='transferencia',
            monto=monto,
            cuenta_origen_id=cuenta_origen.id,
            cuenta_destino_id=cuenta_destino.id,
            descripcion=descripcion or 'Transferencia',
            estado='completada',
        ))

        return ResultadoTransferencia(exitoso=True, mensaje='Transferencia realizada con éxito.')


class SolicitarPrestamo:
    TASA_ANUAL = 0.05  # 5% anual fija

    def __init__(self, repo_prestamo: RepositorioPrestamo, repo_cuenta: RepositorioCuenta):
        self._repo_prestamo = repo_prestamo
        self._repo_cuenta = repo_cuenta

    def simular(
        self,
        monto: Decimal,
        plazo_meses: int,
        sistema: str = 'frances',
        monto_minimo: Decimal = Decimal('1000.00'),
        monto_maximo: Decimal = Decimal('1000000.00'),
        plazo_minimo: int = 3,
        plazo_maximo: int = 60,
    ) -> Optional[List[CuotaSimulada]]:
        if monto < monto_minimo or monto > monto_maximo:
            return None
        if plazo_meses < plazo_minimo or plazo_meses > plazo_maximo:
            return None

        if sistema == 'frances':
            return simular_cuotas_frances(monto, self.TASA_ANUAL, plazo_meses)
        return simular_cuotas_aleman(monto, self.TASA_ANUAL, plazo_meses)

    def ejecutar(
        self,
        cliente_id: int,
        monto: Decimal,
        plazo_meses: int,
        sistema: str = 'frances',
    ) -> tuple[Optional[PrestamoEntity], str]:
        cartera = self._repo_prestamo.listar_por_cliente(cliente_id)
        prestamos_activos = [p for p in cartera if p.estado == 'activo']
        deuda_total = sum(p.saldo_pendiente for p in prestamos_activos)

        if deuda_total + monto > Decimal('500000.00'):
            return None, 'Excedés el límite máximo de endeudamiento.'

        cuotas_simuladas = self.simular(monto, plazo_meses, sistema)
        if cuotas_simuladas is None:
            return None, 'Monto o plazo fuera de los límites permitidos.'

        cuotas_entidades = []
        hoy = date.today()
        for i, c in enumerate(cuotas_simuladas):
            vencimiento = date(hoy.year + (hoy.month + i) // 12, ((hoy.month + i - 1) % 12) + 1, 1)
            cuotas_entidades.append(CuotaEntity(
                id=0,
                prestamo_id=0,
                numero_cuota=c.numero,
                monto_cuota=c.monto_cuota,
                fecha_vencimiento=vencimiento,
                estado='pendiente',
            ))

        prestamo = PrestamoEntity(
            id=0,
            cliente_id=cliente_id,
            monto_original=monto,
            saldo_pendiente=monto,
            tasa_interes_anual=self.TASA_ANUAL,
            plazo_meses=plazo_meses,
            sistema_amortizacion=sistema,
            estado='activo',
        )

        prestamo_creado = self._repo_prestamo.crear(prestamo, cuotas_entidades)
        return prestamo_creado, 'Préstamo aprobado. El monto fue acreditado en tu cuenta.'


class PagarCuota:
    def __init__(self, repo_prestamo: RepositorioPrestamo, repo_cuenta: RepositorioCuenta):
        self._repo_prestamo = repo_prestamo
        self._repo_cuenta = repo_cuenta

    def ejecutar(self, cuota_id: int, cuenta_id: int, cliente_id: int) -> tuple[bool, str]:
        cuentas = self._repo_cuenta.listar_por_cliente(cliente_id)
        if not any(c.id == cuenta_id for c in cuentas):
            return False, 'Cuenta no encontrada.'

        prestamos = self._repo_prestamo.listar_por_cliente(cliente_id)
        cuota = None
        for p in prestamos:
            for c in p.cuotas:
                if c.id == cuota_id:
                    cuota = c
                    break
            if cuota:
                break

        if cuota is None:
            return False, 'Cuota no encontrada.'
        if cuota.estado == 'pagada':
            return False, 'Esta cuota ya fue pagada.'

        cuenta = self._repo_cuenta.buscar_por_id_con_bloqueo(cuenta_id)
        if cuenta is None:
            return False, 'Cuenta no encontrada.'
        if cuenta.saldo < cuota.monto_cuota:
            return False, 'Saldo insuficiente para pagar esta cuota.'

        self._repo_cuenta.incrementar_saldo(cuenta_id, -cuota.monto_cuota)
        self._repo_prestamo.pagar_cuota(cuota_id, cuota.monto_cuota, date.today())

        return True, f'Cuota {cuota.numero_cuota} pagada con éxito.'

# metricas

class CalcularPromedioScoreClientesActivos:
    def __init__(self, repo_cliente: RepositorioCliente, repo_prestamo: RepositorioPrestamo):
        self._repo_cliente = repo_cliente
        self._repo_prestamo = repo_prestamo

    def ejecutar(self) -> Decimal:
        # 1. Obtenemos los IDs de los clientes cuyo estado es 'activo'
        clientes_ids = self._repo_cliente.listar_clientes_con_cuentas_activas()
        
        if not clientes_ids:
            return Decimal('0.00')
            
        suma_scores = Decimal('0.00')
        
        # 2. Recorremos los clientes activos y sumamos su score inicial real
        for cliente_id in clientes_ids:
            score_cliente = self._repo_cliente.obtener_score_por_cliente(cliente_id)
            suma_scores += Decimal(str(score_cliente))
            
        # 3. Calculamos el promedio
        total_clientes = Decimal(len(clientes_ids))
        promedio = suma_scores / total_clientes
        
        return promedio

class ObtenerTopIntentosFallidos:
    def __init__(self, repositorio_cliente: RepositorioCliente):
        self.repositorio_cliente = repositorio_cliente

    def ejecutar(self):
        return self.repositorio_cliente.obtener_monitoreo_seguridad()

class ObtenerDistribucionPagadoresPorGenero:
    def __init__(self, repositorio_cliente: RepositorioCliente):
        self._repositorio_cliente = repositorio_cliente

    def ejecutar(self) -> dict[str, int]:
        """
        Calcula la distribución por género de aquellos clientes 
        que están al día con sus cuotas (sin cuotas vencidas).
        """
        return self._repositorio_cliente.obtener_distribucion_pagadores_por_genero()
    
class ObtenerEvolucionCantidadPrestamosPorEducacion:
    def __init__(self, repo_cliente: RepositorioCliente):
        self._repo_cliente = repo_cliente

    def ejecutar(self):
        datos_crudos = self._repo_cliente.obtener_evolucion_cantidad_prestamos_por_educacion()
        return datos_crudos
    
class ObtenerDatosRiesgoEdadUseCase:
    def __init__(self, repo_cliente: RepositorioCliente):
        self._repo_cliente = repo_cliente

    def ejecutar(self) -> List[dict]:
        return self._repo_cliente.obtener_datos_riesgo_por_edad()