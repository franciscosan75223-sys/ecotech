from validaciones import (
    validar_nombre_entidad, validar_id, validar_id_opcional, validar_departamento
)


class Departamento:
    def __init__(self, id_departamento, nombre, gerente_id, departamento):
        self._id_departamento = validar_id_opcional(id_departamento)
        self._nombre = validar_nombre_entidad(nombre)
        self._gerente_id = validar_id(gerente_id)
        self._departamento = validar_departamento(departamento)

    def get_id(self):
        return self._id_departamento

    def get_nombre(self):
        return self._nombre

    def get_gerente_id(self):
        return self._gerente_id

    def get_departamento(self):
        return self._departamento

    def get_datos(self):
        return {
            "nombre": self._nombre,
            "departamento": self._departamento,
            "gerente_id": self._gerente_id
        }

    def mostrar_datos(self):
        return (
            "Departamento {} | {} | Descripcion: {} | ID del gerente: {}"
        ).format(
            self._id_departamento, self._nombre,
            self._departamento, self._gerente_id
        )

    def __str__(self):
        return self.mostrar_datos()
