from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional, List
from .entities import CuentaEntity, TransaccionEntity, PrestamoEntity, CuotaEntity


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
