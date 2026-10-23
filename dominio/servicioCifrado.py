import os
from hmac import compare_digest
from pathlib import Path

from cryptography.exceptions import InvalidKey
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id


class ServicioCifrado:
    MARCADOR_HASH = "{ARGON2ID}"

    def __init__(self, archivo_clave):
        archivo = Path(archivo_clave)
        if archivo.exists():
            clave = archivo.read_bytes()
        else:
            clave = Fernet.generate_key()
            descriptor = os.open(archivo, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "wb") as salida:
                salida.write(clave)
        try:
            self.__cifrador = Fernet(clave)
        except ValueError as error:
            raise ValueError("El archivo de clave Fernet no contiene una clave valida.") from error

    def cifrar(self, texto):
        if not isinstance(texto, str):
            raise TypeError("El texto que se cifra debe ser una cadena.")
        return self.__cifrador.encrypt(texto.encode("utf-8"))

    def cifrar_contrasena(self, contrasena):
        if not isinstance(contrasena, str):
            raise TypeError("La contrasena debe ser una cadena.")
        derivador = Argon2id(
            salt=os.urandom(16),
            length=32,
            iterations=3,
            lanes=4,
            memory_cost=64 * 1024
        )
        resumen = derivador.derive_phc_encoded(contrasena.encode("utf-8"))
        return self.cifrar(self.MARCADOR_HASH + resumen)

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
        if not isinstance(ingresada, str):
            raise TypeError("La contrasena debe ser una cadena.")
        contenido = self.descifrar(token)
        if contenido.startswith(self.MARCADOR_HASH):
            resumen = contenido[len(self.MARCADOR_HASH):]
            try:
                Argon2id.verify_phc_encoded(ingresada.encode("utf-8"), resumen)
            except InvalidKey:
                return False
            return True
        return compare_digest(ingresada.encode("utf-8"), contenido.encode("utf-8"))

    def __str__(self):
        return "Servicio de cifrado Fernet"
