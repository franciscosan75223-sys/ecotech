from dominio.validaciones import validar_nombre_usuario, validar_correo, validar_contrasena


class CuentaUsuario:
    def __init__(self, nombre, correo, servicio, contrasena=None):
        self._nombre = validar_nombre_usuario(nombre)
        self._correo = validar_correo(correo)
        self.__servicio = servicio
        self.__contrasena_cifrada = None
        if contrasena is not None:
            self.set_contrasena(contrasena)

    def get_nombre(self):
        return self._nombre

    def get_correo(self):
        return self._correo

    def set_contrasena(self, contrasena):
        contrasena = validar_contrasena(contrasena)
        self.__contrasena_cifrada = self.__servicio.cifrar(contrasena)

    def get_contrasena_cifrada(self):
        if self.__contrasena_cifrada is None:
            raise ValueError("La cuenta todavia no tiene contrasena.")
        return self.__contrasena_cifrada

    def cargar_contrasena_cifrada(self, token):
        self.__contrasena_cifrada = bytes(token)

    def acceso_cuenta(self, nombre, contrasena):
        if nombre != self._nombre:
            return False
        return self.__servicio.validacion_cifrado(
            contrasena, self.get_contrasena_cifrada()
        )

    def __str__(self):
        return f"Usuario: {self._nombre} | Correo: {self._correo}"