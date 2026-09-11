class Informes:
    def __init__(self, empleados, proyecto, departamento, registro_de_tiempo):
        self.empleados = empleados  # +publico
        self.proyecto = proyecto  # +publico
        self.departamento = departamento  # +publico
        self.registro_de_tiempo = registro_de_tiempo  # +publico    

    def generar_informes(self):
        print("informe generado correctamente")
