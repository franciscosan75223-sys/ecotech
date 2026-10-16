class Tiempo:
    def __init__(self, fecha, horas_trabajadas, descripcion_de_tareas, empleado, proyecto,
                 mostrar_mensaje=True):
        self.fecha = fecha
        self._horas_trabajadas = 0
        self._descripcion_de_tareas = descripcion_de_tareas
        self.empleado = empleado
        self.proyecto = proyecto
        self.registro_horas(horas_trabajadas, mostrar_mensaje)

    def registro_horas(self, horas, mostrar_mensaje=True):
        if horas > 0:
            self._horas_trabajadas = horas
            if mostrar_mensaje:
                print("horas registradas correctamente")
        elif mostrar_mensaje:
            print("las horas deben ser mayores que cero")

    def mostrar_registro(self):
        print("registro de fecha", self.fecha)
        print("horas trabajadas", self._horas_trabajadas)
        print("descripcion de la tarea", self._descripcion_de_tareas)
        print("empleado", self.empleado)
        print("proyecto", self.proyecto)

    def get_horas_trabajadas(self):
        return self._horas_trabajadas

    def get_descripcion_de_tareas(self):
        return self._descripcion_de_tareas