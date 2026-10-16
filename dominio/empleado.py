from dominio.persona import Persona
from dominio.validaciones import validar_fecha, validar_salario, validar_rol


class Empleado(Persona):
    def __init__(self, id_empleado, nombre, direccion, telefono,
                 correo, fecha_inicio, salario, rol="Empleado"):
        super().__init__(nombre, direccion, telefono, correo)
        self._id_empleado = id_empleado
        self._fecha_inicio = validar_fecha(fecha_inicio)
        self.set_salario(salario)
        self._rol = validar_rol(rol)
        self.__cuenta_usuario = None

    def get_id(self):
        return self._id_empleado

    def get_fecha_inicio(self):
        return self._fecha_inicio

    def get_rol(self):
        return self._rol

    def get_salario(self):
        return self.__salario

    def set_salario(self, salario):
        self.__salario = validar_salario(salario)

    def asignar_cuenta(self, cuenta):
        if cuenta.get_correo() != self.get_correo():
            raise ValueError("La cuenta debe usar el correo del empleado.")
        self.__cuenta_usuario = cuenta

    def get_cuenta_usuario(self):
        return self.__cuenta_usuario

    def mostrar_datos(self):
        return (
            f"ID: {self._id_empleado} | Nombre: {self._nombre} | "
            f"Direccion: {self._direccion} | Telefono: {self._telefono} | "
            f"Correo: {self._correo} | Inicio: {self._fecha_inicio} | "
            f"Salario: {self.__salario:.2f} | Rol: {self._rol}"
        )