class Proyecto:
    def __init__(self, nombre, descripcion_proyecto, fecha_de_inicio):
        self.nombre = nombre  # +publico
        self._descripcion_proyecto = descripcion_proyecto  # #protregido
        self._fecha_de_inicio = fecha_de_inicio  # #protegido

    def creacion_proyecto(self):
        print("proyecto creado")
        print("nombre del proyecto:", self.nombre)
        print("descripcion del proyecto:", self._descripcion_proyecto)
        print("fecha de inicio del proyecto:", self._fecha_de_inicio)

    def edicion_proyecto(self, nuevo_nombre, nueva_descripcion, nueva_fecha):
        self.nombre = nuevo_nombre
        self._descripcion_proyecto = nueva_descripcion
        self._fecha_de_inicio = nueva_fecha
    print("el proyecto a sido editado correctamente")

    def eliminacion_proyecto(self):
        print("proyecto eliminado") 
        
