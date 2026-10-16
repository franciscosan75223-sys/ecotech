from dominio.validaciones import (
    validar_nombre_entidad, validar_descripcion,
    validar_fecha, validar_miembro, validar_presupuesto
)


class Proyecto:
    def __init__(self, id_proyecto, nombre, descripcion_proyecto,
                 fecha_de_inicio, miembro, presupuesto):
        self._id_proyecto = id_proyecto
        self._nombre = validar_nombre_entidad(nombre)
        self._descripcion_proyecto = validar_descripcion(descripcion_proyecto)
        self._fecha_de_inicio = validar_fecha(fecha_de_inicio)
        self._miembro = validar_miembro(miembro)
        self.__presupuesto = validar_presupuesto(presupuesto)

    def get_id(self):
        return self._id_proyecto

    def get_nombre(self):
        return self._nombre

    def get_descripcion_proyecto(self):
        return self._descripcion_proyecto

    def get_fecha_de_inicio(self):
        return self._fecha_de_inicio

    def get_miembro(self):
        return self._miembro

    def get_presupuesto(self):
        return self.__presupuesto

    def get_datos(self):
        return {    
            "nombre": self._nombre,
            "descripcion_proyecto": self._descripcion_proyecto,
            "fecha_de_inicio": self._fecha_de_inicio,
            "miembro": self._miembro,
            "presupuesto": self.__presupuesto
        }

    def mostrar_datos(self):
        return (
            f"Proyecto {self._id_proyecto} | {self._nombre} | "
            f"Descripcion: {self._descripcion_proyecto} | Inicio: {self._fecha_de_inicio} | "
            f"Miembro: {self._miembro} | Presupuesto: {self.__presupuesto:.2f}"
        )

    def __str__(self):
        return self.mostrar_datos()