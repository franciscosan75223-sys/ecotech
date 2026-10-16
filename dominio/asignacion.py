from dominio.validaciones import (
    validar_fecha, validar_horas, validar_descripcion,
    validar_id, validar_horas_adicionales
)


class Asignacion:
    def __init__(self, id_asignacion, fecha, horas_trabajadas, tareas_realizadas,
                 id_empleado=None, id_proyecto=None):
        self._id_asignacion = id_asignacion
        self._fecha = validar_fecha(fecha)
        self.__horas_trabajadas = validar_horas(horas_trabajadas)
        self._tareas_realizadas = validar_descripcion(tareas_realizadas)
        self._id_empleado = validar_id(id_empleado) if id_empleado is not None else None
        self._id_proyecto = validar_id(id_proyecto) if id_proyecto is not None else None

    def get_id(self):
        return self._id_asignacion

    def get_fecha(self):
        return self._fecha

    def get_horas_trabajadas(self):
        return self.__horas_trabajadas

    def get_tareas_realizadas(self):
        return self._tareas_realizadas

    def get_id_empleado(self):
        return self._id_empleado

    def get_id_proyecto(self):
        return self._id_proyecto

    def sumar_horas(self, horas):
        horas = validar_horas_adicionales(horas)
        self.__horas_trabajadas = validar_horas(self.__horas_trabajadas + horas)

    def get_datos(self):
        return {
            "fecha": self._fecha,
            "horas_trabajadas": self.__horas_trabajadas,
            "tareas_realizadas": self._tareas_realizadas,
            "id_empleado": self._id_empleado,
            "id_proyecto": self._id_proyecto
        }

    def mostrar_datos(self):
        empleado = self._id_empleado if self._id_empleado is not None else "sin vincular"
        proyecto = self._id_proyecto if self._id_proyecto is not None else "sin vincular"
        return (
            f"Asignacion {self._id_asignacion} | Fecha: {self._fecha} | "
            f"Empleado: {empleado} | Proyecto: {proyecto} | "
            f"Horas: {self.__horas_trabajadas} | Tareas: {self._tareas_realizadas}"
        )

    def __str__(self):
        return self.mostrar_datos()