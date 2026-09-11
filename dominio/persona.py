class Persona:
    def __init__(self, nombre, direccion, telefono, correo):
        self.nombre = nombre  # +publico
        self._direccion = direccion  # #protegido
        self._telefono = telefono   # #protegido
        self._correo = correo  # #protegido
       
       
    def actualizar_datos(self, nuevo_nombre, nuevo_correo, nuevo_telefono, nueva_direccion):
        print("datos actualizados correctamente")
        self.nombre = nuevo_nombre
        self._correo = nuevo_correo
        self._telefono = nuevo_telefono
        self._direccion = nueva_direccion 
