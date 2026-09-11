class Departamento:
    def __init__(self, nombre, gerente, departamento):
        self.nombre = nombre   # +publico
        self._gerente = gerente # #protegido
        self._departamento = departamento # #protegido

    def creacion_departamento(self):
        print("departamento creado")
        print("nombre:", self.nombre)
        print("gerente:", self._gerente)

    def edicion_departamento(self, nuevo_nombre, nuevo_gerente):
        self.nombre = nuevo_nombre
        self._gerente = nuevo_gerente
        print("edicion del departamento hecha")

    def busqueda_departamento(self):
        print("departamento encontrado")

    def eliminacion_departamento(self):
        print("departamento eliminado")