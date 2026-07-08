from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from typing import Any, Dict, Optional, List
from .entities import CuentaEntity, TransaccionEntity, PrestamoEntity, CuotaEntity, PlazoFijoEntity


class RepositorioCuenta(ABC):
    @abstractmethod
    def buscar_por_id_con_bloqueo(self, cuenta_id: int):
        ...

    @abstractmethod
    def buscar_por_alias_o_cvu(self, valor: str):
        ...

    @abstractmethod
    def listar_por_cliente(self, cliente_id: int):
        ...

    @abstractmethod
    def listar_por_cliente_activas(self, cliente_id: int):
        ...

    @abstractmethod
    def incrementar_saldo(self, cuenta_id: int, delta: Decimal) -> None:
        ...


class RepositorioTransaccion(ABC):
    @abstractmethod
    def crear(self, transaccion: TransaccionEntity) -> TransaccionEntity:
        ...

    @abstractmethod
    def listar_por_cuenta(self, cuenta_id: int, limite: int = 10) -> List[TransaccionEntity]:
        ...

    @abstractmethod
    def listar_por_cliente(self, cliente_id: int, limite: int = 10) -> List[TransaccionEntity]:
        ...


class RepositorioPrestamo(ABC):
    @abstractmethod
    def crear(self, prestamo: PrestamoEntity, cuotas: List[CuotaEntity]) -> PrestamoEntity:
        ...

    @abstractmethod
    def listar_por_cliente(self, cliente_id: int) -> List[PrestamoEntity]:
        ...

    @abstractmethod
    def buscar_por_id(self, prestamo_id: int) -> Optional[PrestamoEntity]:
        ...

    @abstractmethod
    def pagar_cuota(self, cuota_id: int, monto: Decimal, fecha_pago) -> None:
        ...

## Métodos abstractos para la realización de las métricas

class RepositorioCliente(ABC):
    @abstractmethod
    def listar_clientes_con_cuentas_activas(self) -> List[int]:
        """Retorna una lista de IDs de clientes que tienen al menos una cuenta activa."""
        ...
    
    @abstractmethod
    def obtener_score_por_cliente(self, cliente_id: int) -> int:
        """Obtiene el score crediticio inicial de un cliente."""
        ...
        
    @abstractmethod
    def obtener_monitoreo_seguridad(self) -> List[Dict[str, Any]]:
        """Retorna la lista de usuarios con sus intentos fallidos y estados de bloqueo."""
        ...

    @abstractmethod
    def obtener_distribucion_pagadores_por_genero(self) -> Dict[str, int]:
        """Retorna la cantidad de clientes sin deudas agrupados por género."""
        ...

    #usar para demostrar clientes morosos
    @abstractmethod
    def obtener_distribucion_morosos_por_genero(self) -> Dict[str, int]:
        """Retorna la cantidad de clientes sin deudas agrupados por género."""
        ...

    @abstractmethod
    def obtener_evolucion_cantidad_prestamos_por_educacion(self) -> List[Dict[str, Any]]:
        """
        Retorna una lista de diccionarios con el conteo de préstamos 
        agrupados por mes y por el nivel educativo del cliente.
        """
        ...

    @abstractmethod
    def obtener_datos_riesgo_por_edad(self) -> List[dict]:
        """Declaración del nuevo puerto."""
        ...


class MotorFraud(ABC):
    @abstractmethod
    def evaluar(self, monto: float, hora: int, dia_semana: int,
                 cantidad_ultimas_24h: int, saldo_origen: float) -> float:
        """Retorna score de riesgo de fraude: 0.0 (normal) a 1.0 (fraude)"""
        ...


class MotorScoring(ABC):
    @abstractmethod
    def evaluar(self, cliente_id: int) -> float:
        """Retorna score de riesgo crediticio: 0.0 (bajo riesgo) a 1.0 (alto riesgo)"""
        ...


class RepositorioPlazoFijo(ABC):

    @abstractmethod
    def crear(self, plazo: PlazoFijoEntity) -> PlazoFijoEntity:
        ...

    @abstractmethod
    def listar_por_cliente(self, cliente_id: int) -> List[PlazoFijoEntity]:
        ...

    @abstractmethod
    def buscar_por_id(self, plazo_id: int) -> Optional[PlazoFijoEntity]:
        ...

    @abstractmethod
    def cancelar(self, plazo_id: int) -> None:
        ...