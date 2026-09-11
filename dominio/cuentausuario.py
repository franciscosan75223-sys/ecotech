class Cuentausuario:
    def __init__(self, nombre, correo, contrasena):
        self.nombre = nombre   #  +publico
        self._correo = correo   #  # #protegido
        self._contrasena = contrasena   # #protegido
       
       
    def acceso_cuenta(self, intentos):
        print("acceso consedido ")