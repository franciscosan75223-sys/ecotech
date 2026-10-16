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
        self.__cifrador = Fernet(clave)

    def cifrar(self, texto):
        return self.__cifrador.encrypt(texto.encode())

    def descifrar(self, token):
        return self.__cifrador.decrypt(token).decode()

    def validacion_cifrado(self, ingresada, token):
        try:
            return ingresada == self.descifrar(token)
        except InvalidToken:
            return False

    def __str__(self):
        return "Servicio de cifrado Fernet"