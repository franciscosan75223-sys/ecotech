from abc import ABC, abstractmethod
from dominio.validaciones import validar_nombre, validar_direccion, validar_telefono, validar_correo


class Persona(ABC):
    def __init__(self, nombre, direccion, telefono, correo):
        self.actualizar_datos(nombre, direccion, telefono, correo)

    def actualizar_datos(self, nombre, direccion, telefono, correo):
        nombre = validar_nombre(nombre)
        direccion = validar_direccion(direccion)
        telefono = validar_telefono(telefono)
        correo = validar_correo(correo)
        self._nombre = nombre
        self._direccion = direccion
        self._telefono = telefono
        self._correo = correo

    def get_nombre(self):
        return self._nombre

    def get_direccion(self):
        return self._direccion

    def get_telefono(self):
        return self._telefono

    def get_correo(self):
        return self._correo

    @abstractmethod
    def mostrar_datos(self):
        raise NotImplementedError("La clase hija debe implementar mostrar_datos.")

    def __str__(self):
        return self.mostrar_datos()