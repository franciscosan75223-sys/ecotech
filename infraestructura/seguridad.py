from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken


class ServicioCifrado:
    def __init__(self, archivo_clave):
        archivo = Path(archivo_clave)
        if archivo.exists():
            clave = archivo.read_bytes()
        else:
            clave = Fernet.generate_key()
            with archivo.open("xb") as salida:
                salida.write(clave)
        try:
            self.__cifrador = Fernet(clave)
        except ValueError as error:
            raise ValueError("El archivo de clave Fernet no contiene una clave valida.") from error

    def cifrar(self, texto):
        if not isinstance(texto, str):
            raise TypeError("El texto que se cifra debe ser una cadena.")
        return self.__cifrador.encrypt(texto.encode("utf-8"))

    def descifrar(self, token):
        if not isinstance(token, (bytes, bytearray, memoryview)):
            raise TypeError("El token cifrado debe recibirse como bytes.")
        try:
            texto = self.__cifrador.decrypt(bytes(token))
        except InvalidToken as error:
            raise ValueError(
                "No se pudo descifrar la contrasena guardada. Revise que este usando la clave Fernet original."
            ) from error
        return texto.decode("utf-8")

    def validacion_cifrado(self, ingresada, token):
        return ingresada == self.descifrar(token)

    def __str__(self):
        return "Servicio de cifrado Fernet"