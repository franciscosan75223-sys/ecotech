class Tiempo:
    def __init__(self, fecha, horas_trabajadas, descripcion_de_tareas, empleado, proyecto):
        self.fecha = fecha  # +publico
        self._horas_trabajadas = horas_trabajadas  # #protegido
        self._descripcion_de_tareas = descripcion_de_tareas  # #protegido
        self.empleado = empleado
        self.proyecto = proyecto

    def registro_horas(self):
        print("las horas trabajadas son:", self._horas_trabajadas)