import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

# Configuro el archivo de logs para guardar eventos y errores sin detener la ejecución
logging.basicConfig(
    filename="sistema_software_fj.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    encoding="utf-8",
)


def registrar_evento(nivel: str, mensaje: str) -> None:
    if nivel.upper() == "INFO":
        logging.info(mensaje)
    elif nivel.upper() == "WARNING":
        logging.warning(mensaje)
    elif nivel.upper() == "ERROR":
        logging.error(mensaje)


# Excepciones personalizadas para controlar errores propios del negocio
class ErrorSistemaFJ(Exception):
    pass


class DatoInvalidoError(ErrorSistemaFJ):
    pass


class ServicioNoDisponibleError(ErrorSistemaFJ):
    pass


class ReservaInvalidaError(ErrorSistemaFJ):
    pass


class CalculoInconsistenteError(ErrorSistemaFJ):
    pass


# Clase abstracta general para las entidades del sistema
class EntidadSistema(ABC):
    def __init__(self, id_entidad: str):
        if id_entidad is None or not isinstance(id_entidad, str) or not id_entidad.strip():
            raise DatoInvalidoError("El ID de la entidad es obligatorio.")
        self._id_entidad = id_entidad.strip()
        self._fecha_creacion = datetime.now()

    @property
    def id_entidad(self) -> str:
        return self._id_entidad

    @property
    def fecha_creacion(self) -> datetime:
        return self._fecha_creacion

    @abstractmethod
    def validar_integridad(self) -> bool:
        pass

    @abstractmethod
    def obtener_resumen(self) -> str:
        pass


# Clase Cliente con encapsulación y validaciones estrictas
class Cliente(EntidadSistema):
    def __init__(self, id_cliente: str, nombre: str, correo: str, telefono: str):
        super().__init__(id_cliente)
        self.nombre = nombre
        self.correo = correo
        self.telefono = telefono
        if not self.validar_integridad():
            raise DatoInvalidoError("Los datos del cliente no son íntegros.")

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        if valor is None or not isinstance(valor, str) or len(valor.strip()) < 3:
            raise DatoInvalidoError("El nombre del cliente debe tener al menos 3 caracteres.")
        self._nombre = valor.strip()

    @property
    def correo(self) -> str:
        return self._correo

    @correo.setter
    def correo(self, valor: str) -> None:
        if (
            valor is None
            or not isinstance(valor, str)
            or "@" not in valor
            or "." not in valor.split("@")[-1]
        ):
            raise DatoInvalidoError(f"Correo electrónico inválido: '{valor}'.")
        self._correo = valor.strip().lower()

    @property
    def telefono(self) -> str:
        return self._telefono

    @telefono.setter
    def telefono(self, valor: str) -> None:
        if valor is None or not isinstance(valor, str):
            raise DatoInvalidoError("El teléfono es obligatorio.")
        limpio = valor.strip()
        if not limpio.isdigit() or len(limpio) < 7:
            raise DatoInvalidoError("El teléfono debe tener al menos 7 dígitos numéricos.")
        self._telefono = limpio

    def validar_integridad(self) -> bool:
        return bool(self._id_entidad and self._nombre and self._correo and self._telefono)

    def obtener_resumen(self) -> str:
        return f"Cliente [{self.id_entidad}] {self.nombre} | Correo: {self.correo} | Tel: {self.telefono}"


# Clase abstracta Servicio y subclases con polimorfismo y cálculo sobrecargado
class Servicio(EntidadSistema, ABC):
    def __init__(self, id_servicio: str, nombre_servicio: str, tarifa_base: float):
        super().__init__(id_servicio)
        if nombre_servicio is None or not isinstance(nombre_servicio, str) or not nombre_servicio.strip():
            raise DatoInvalidoError("El nombre del servicio es obligatorio.")
        if tarifa_base is None or isinstance(tarifa_base, bool) or not isinstance(tarifa_base, (int, float)) or tarifa_base <= 0:
            raise DatoInvalidoError("La tarifa base debe ser un número mayor que cero.")
        self._nombre_servicio = nombre_servicio.strip()
        self._tarifa_base = float(tarifa_base)
        self._disponible = True

    @property
    def nombre_servicio(self) -> str:
        return self._nombre_servicio

    @property
    def tarifa_base(self) -> float:
        return self._tarifa_base

    @property
    def disponible(self) -> bool:
        return self._disponible

    @disponible.setter
    def disponible(self, estado: bool) -> None:
        if not isinstance(estado, bool):
            raise DatoInvalidoError("La disponibilidad debe ser un valor booleano.")
        self._disponible = estado

    @abstractmethod
    def calcular_costo_base(self, duracion_horas: int) -> float:
        pass

    @abstractmethod
    def describir_servicio(self) -> str:
        pass

    # Resuelvo la sobrecarga de cálculo de costos usando parámetros opcionales para impuestos, descuentos y recargos
    def calcular_costo_total(
        self,
        duracion_horas: int,
        impuesto_pct: float = 0.0,
        descuento_pct: float = 0.0,
        recargo_fijo: float = 0.0,
    ) -> float:
        try:
            if duracion_horas is None or isinstance(duracion_horas, bool) or not isinstance(duracion_horas, int) or duracion_horas <= 0:
                raise DatoInvalidoError("La duración en horas debe ser un entero mayor a cero.")
            if not (0 <= impuesto_pct <= 100) or not (0 <= descuento_pct <= 100):
                raise CalculoInconsistenteError("Los porcentajes deben estar entre 0 y 100.")
            if recargo_fijo < 0:
                raise CalculoInconsistenteError("El recargo fijo no puede ser negativo.")

            subtotal = self.calcular_costo_base(duracion_horas)
            descuento = subtotal * (descuento_pct / 100.0)
            base = subtotal - descuento + recargo_fijo
            total = base * (1.0 + (impuesto_pct / 100.0))

            if total <= 0:
                raise CalculoInconsistenteError("El costo total calculado es inconsistente.")
            return round(total, 2)
        except ErrorSistemaFJ:
            raise
        except Exception as e:
            raise CalculoInconsistenteError("Error al calcular el costo total del servicio.") from e

    def validar_integridad(self) -> bool:
        return self._tarifa_base > 0 and bool(self._nombre_servicio)

    def obtener_resumen(self) -> str:
        estado = "Disponible" if self._disponible else "Ocupado"
        return f"[{self.id_entidad}] {self.describir_servicio()} | Estado: {estado}"


class ReservaSala(Servicio):
    def __init__(self, id_servicio: str, nombre_servicio: str, tarifa_base: float, capacidad: int):
        super().__init__(id_servicio, nombre_servicio, tarifa_base)
        if capacidad is None or isinstance(capacidad, bool) or not isinstance(capacidad, int) or capacidad <= 0:
            raise DatoInvalidoError("La capacidad de la sala debe ser mayor que cero.")
        self._capacidad = capacidad

    def calcular_costo_base(self, duracion_horas: int) -> float:
        factor = 1.15 if self._capacidad > 20 else 1.0
        return self.tarifa_base * duracion_horas * factor

    def describir_servicio(self) -> str:
        return f"Sala '{self.nombre_servicio}' (Capacidad: {self._capacidad}) - Base: ${self.tarifa_base:,.2f}/h"


class AlquilerEquipo(Servicio):
    def __init__(
        self,
        id_servicio: str,
        nombre_servicio: str,
        tarifa_base: float,
        categoria_equipo: str,
        cantidad: int,
    ):
        super().__init__(id_servicio, nombre_servicio, tarifa_base)
        if not categoria_equipo or not isinstance(categoria_equipo, str) or not categoria_equipo.strip():
            raise DatoInvalidoError("La categoría del equipo es obligatoria.")
        if cantidad is None or isinstance(cantidad, bool) or not isinstance(cantidad, int) or cantidad <= 0:
            raise DatoInvalidoError("La cantidad de equipos debe ser al menos 1.")
        self._categoria_equipo = categoria_equipo.strip()
        self._cantidad = cantidad

    def calcular_costo_base(self, duracion_horas: int) -> float:
        return self.tarifa_base * duracion_horas * self._cantidad

    def describir_servicio(self) -> str:
        return (
            f"Equipo '{self.nombre_servicio}' [{self._categoria_equipo}] "
            f"(Cantidad: {self._cantidad}) - Base: ${self.tarifa_base:,.2f}/h"
        )


class AsesoriaEspecializada(Servicio):
    def __init__(
        self,
        id_servicio: str,
        nombre_servicio: str,
        tarifa_base: float,
        especialidad: str,
        nivel_senior: bool = True,
    ):
        super().__init__(id_servicio, nombre_servicio, tarifa_base)
        if not especialidad or not isinstance(especialidad, str) or not especialidad.strip():
            raise DatoInvalidoError("La especialidad de la asesoría es obligatoria.")
        if not isinstance(nivel_senior, bool):
            raise DatoInvalidoError("El nivel senior debe ser booleano.")
        self._especialidad = especialidad.strip()
        self._nivel_senior = nivel_senior

    def calcular_costo_base(self, duracion_horas: int) -> float:
        factor_senior = 1.30 if self._nivel_senior else 1.0
        return self.tarifa_base * duracion_horas * factor_senior

    def describir_servicio(self) -> str:
        nivel = "Senior" if self._nivel_senior else "Semi-Senior"
        return f"Asesoría '{self.nombre_servicio}' ({self._especialidad}, {nivel}) - Base: ${self.tarifa_base:,.2f}/h"


# Clase Reserva para unir cliente, servicio, duración y estado
class Reserva(EntidadSistema):
    def __init__(
        self,
        id_reserva: str,
        cliente: Cliente,
        servicio: Servicio,
        duracion_horas: int,
        impuesto_pct: float = 19.0,
        descuento_pct: float = 0.0,
    ):
        super().__init__(id_reserva)
        if not isinstance(cliente, Cliente):
            raise ReservaInvalidaError("El cliente de la reserva no es válido.")
        if not isinstance(servicio, Servicio):
            raise ReservaInvalidaError("El servicio de la reserva no es válido.")
        if duracion_horas is None or isinstance(duracion_horas, bool) or not isinstance(duracion_horas, int) or duracion_horas <= 0:
            raise ReservaInvalidaError("La duración de la reserva debe ser mayor a 0 horas.")

        self._cliente = cliente
        self._servicio = servicio
        self._duracion_horas = duracion_horas
        self._impuesto_pct = impuesto_pct
        self._descuento_pct = descuento_pct
        self._estado = "PENDIENTE"
        self._costo_total = 0.0

    @property
    def estado(self) -> str:
        return self._estado

    @property
    def costo_total(self) -> float:
        return self._costo_total

    def procesar_y_confirmar(self) -> None:
        if self._estado == "CANCELADA":
            raise ReservaInvalidaError(f"No se puede confirmar {self.id_entidad} porque está cancelada.")
        if self._estado == "CONFIRMADA":
            raise ReservaInvalidaError(f"La reserva {self.id_entidad} ya está confirmada.")
        if not self._servicio.disponible:
            raise ServicioNoDisponibleError(
                f"El servicio '{self._servicio.nombre_servicio}' no está disponible."
            )

        self._costo_total = self._servicio.calcular_costo_total(
            duracion_horas=self._duracion_horas,
            impuesto_pct=self._impuesto_pct,
            descuento_pct=self._descuento_pct,
        )
        self._servicio.disponible = False
        self._estado = "CONFIRMADA"

    def cancelar_reserva(self) -> None:
        if self._estado == "CANCELADA":
            raise ReservaInvalidaError(f"La reserva {self.id_entidad} ya estaba cancelada.")
        if self._estado == "CONFIRMADA":
            self._servicio.disponible = True
        self._estado = "CANCELADA"

    def validar_integridad(self) -> bool:
        return (
            self._cliente.validar_integridad()
            and self._servicio.validar_integridad()
            and self._duracion_horas > 0
        )

    def obtener_resumen(self) -> str:
        return (
            f"Reserva [{self.id_entidad}] | Estado: {self._estado} | "
            f"Cliente: {self._cliente.nombre} | Servicio: {self._servicio.nombre_servicio} | "
            f"Duración: {self._duracion_horas}h | Total: ${self._costo_total:,.2f}"
        )


# Gestor central que mantiene las listas en memoria sin base de datos
class GestorSoftwareFJ:
    def __init__(self):
        self._clientes: List[Cliente] = []
        self._servicios: List[Servicio] = []
        self._reservas: List[Reserva] = []
        registrar_evento("INFO", "Gestor de Software FJ iniciado en memoria.")

    def buscar_cliente(self, id_cliente: str) -> Optional[Cliente]:
        return next((c for c in self._clientes if c.id_entidad == id_cliente), None)

    def buscar_servicio(self, id_servicio: str) -> Optional[Servicio]:
        return next((s for s in self._servicios if s.id_entidad == id_servicio), None)

    def registrar_cliente(
        self, id_cliente: str, nombre: str, correo: str, telefono: str
    ) -> Optional[Cliente]:
        cliente = None
        try:
            if self.buscar_cliente(id_cliente) is not None:
                raise DatoInvalidoError(f"Ya existe un cliente con ID '{id_cliente}'.")
            cliente = Cliente(id_cliente, nombre, correo, telefono)
        except ErrorSistemaFJ as e:
            mensaje = f"[ERROR CLIENTE] {e}"
            print(mensaje)
            registrar_evento("ERROR", mensaje)
            return None
        else:
            self._clientes.append(cliente)
            mensaje = f"[OK] {cliente.obtener_resumen()}"
            print(mensaje)
            registrar_evento("INFO", mensaje)
            return cliente
        finally:
            registrar_evento("INFO", f"Intento de registro de cliente '{id_cliente}' procesado.")

    def registrar_servicio(self, servicio: Servicio) -> bool:
        try:
            if not isinstance(servicio, Servicio):
                raise DatoInvalidoError("Servicio inválido.")
            if self.buscar_servicio(servicio.id_entidad) is not None:
                raise DatoInvalidoError(f"Ya existe un servicio con ID '{servicio.id_entidad}'.")
            self._servicios.append(servicio)
            mensaje = f"[OK] {servicio.obtener_resumen()}"
            print(mensaje)
            registrar_evento("INFO", mensaje)
            return True
        except ErrorSistemaFJ as e:
            mensaje = f"[ERROR SERVICIO] {e}"
            print(mensaje)
            registrar_evento("ERROR", mensaje)
            return False

    def crear_y_confirmar_reserva(
        self,
        id_reserva: str,
        id_cliente: str,
        id_servicio: str,
        duracion_horas: int,
        impuesto_pct: float = 19.0,
        descuento_pct: float = 0.0,
    ) -> Optional[Reserva]:
        try:
            cliente = self.buscar_cliente(id_cliente)
            if cliente is None:
                raise ReservaInvalidaError(f"No existe el cliente '{id_cliente}'.")

            servicio = self.buscar_servicio(id_servicio)
            if servicio is None:
                raise ReservaInvalidaError(f"No existe el servicio '{id_servicio}'.")

            reserva = Reserva(
                id_reserva, cliente, servicio, duracion_horas, impuesto_pct, descuento_pct
            )
            reserva.procesar_y_confirmar()
            self._reservas.append(reserva)

            mensaje = f"[OK] {reserva.obtener_resumen()}"
            print(mensaje)
            registrar_evento("INFO", mensaje)
            return reserva
        except ErrorSistemaFJ as e:
            mensaje = f"[ERROR RESERVA '{id_reserva}'] {e}"
            print(mensaje)
            registrar_evento("ERROR", mensaje)
            return None
        except Exception as e:
            try:
                raise ErrorSistemaFJ(f"Error inesperado en reserva '{id_reserva}'.") from e
            except ErrorSistemaFJ as encadenada:
                mensaje = f"[ERROR ENCADENADO] {encadenada} (Causa: {encadenada.__cause__})"
                print(mensaje)
                registrar_evento("ERROR", mensaje)
                return None

    def cancelar_reserva_por_id(self, id_reserva: str) -> None:
        try:
            reserva = next((r for r in self._reservas if r.id_entidad == id_reserva), None)
            if reserva is None:
                raise ReservaInvalidaError(f"No se encontró la reserva '{id_reserva}'.")
            reserva.cancelar_reserva()
            mensaje = f"[OK] Cancelada -> {reserva.obtener_resumen()}"
            print(mensaje)
            registrar_evento("INFO", mensaje)
        except ErrorSistemaFJ as e:
            mensaje = f"[ERROR CANCELACIÓN] {e}"
            print(mensaje)
            registrar_evento("ERROR", mensaje)

    def mostrar_reporte_general(self) -> None:
        print("\n--- REPORTE GENERAL SOFTWARE FJ ---")
        print(f"Clientes ({len(self._clientes)}):")
        for c in self._clientes:
            print(" ", c.obtener_resumen())

        print(f"Servicios ({len(self._servicios)}):")
        for s in self._servicios:
            print(" ", s.obtener_resumen())

        print(f"Reservas ({len(self._reservas)}):")
        for r in self._reservas:
            print(" ", r.obtener_resumen())
        print("----------------------------------\n")


# Pruebo más de 10 operaciones válidas e inválidas para verificar el comportamiento del sistema
def ejecutar_simulacion() -> None:
    sistema = GestorSoftwareFJ()

    sistema.registrar_cliente("CLI-01", "Laura Martínez", "laura.m@empresa.com", "3104567890")
    sistema.registrar_cliente("CLI-02", "Carlos Gómez", "cgomez@techcol.co", "3209876543")
    sistema.registrar_cliente("CLI-03", "Ana", "correo_invalido", "123")
    sistema.registrar_cliente("CLI-01", "Laura Duplicada", "otra@correo.com", "3112223344")

    sala_juntas = ReservaSala("SRV-01", "Sala Ejecutiva Norte", 80000, capacidad=25)
    sistema.registrar_servicio(sala_juntas)

    kit_laptops = AlquilerEquipo("SRV-02", "Workstations Dell", 35000, "Cómputo", cantidad=4)
    sistema.registrar_servicio(kit_laptops)

    asesoria_arq = AsesoriaEspecializada(
        "SRV-03", "Arquitectura Cloud", 150000, "DevSecOps", nivel_senior=True
    )
    sistema.registrar_servicio(asesoria_arq)

    try:
        servicio_invalido = ReservaSala("SRV-04", "Sala Inválida", -50000, capacidad=10)
        sistema.registrar_servicio(servicio_invalido)
    except ErrorSistemaFJ as e:
        mensaje = f"[ERROR CREACIÓN SERVICIO] {e}"
        print(mensaje)
        registrar_evento("ERROR", mensaje)

    sistema.crear_y_confirmar_reserva("RES-101", "CLI-01", "SRV-01", 4, 19.0, 10.0)
    sistema.crear_y_confirmar_reserva("RES-102", "CLI-02", "SRV-01", 2)
    sistema.crear_y_confirmar_reserva("RES-103", "CLI-02", "SRV-03", 3, 19.0, 0.0)
    sistema.crear_y_confirmar_reserva("RES-104", "CLI-99", "SRV-02", -2)

    sistema.cancelar_reserva_por_id("RES-101")
    sistema.crear_y_confirmar_reserva("RES-105", "CLI-02", "SRV-01", 2)
    sistema.cancelar_reserva_por_id("RES-101")

    sistema.mostrar_reporte_general()
    print("Simulación terminada. Revisa 'sistema_software_fj.log'.")


if __name__ == "__main__":
    ejecutar_simulacion()
    #se usaron --------- en print para separar y ordenar el reporte 
    