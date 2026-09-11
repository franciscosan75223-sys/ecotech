class Empleado:
    def __init__(self, id_empleado, nombre, direccion, numero_telefonico, correo_electronico, fecha_inicio_contrato, salario):
        self.id_empleado = id_empleado # +publico
        self.nombre = nombre      # +publico
        self._direccion = direccion    # #protegido
        self._numero_telefonico = numero_telefonico  # #protegido
        self._correo_electronico = correo_electronico   # #protegido
        self._fecha_inicio_contrato = fecha_inicio_contrato   # #protegido
        self.__salario = salario   # -privado
        self._fecha_fin_contrato = None   # #protegido

    def registrar_empleado(self):
        print("Empleado registrado")
        print("ID:", self.id_empleado)
        print("Nombre:", self.nombre)
        print("Dirección:", self._direccion)
        print("Número de teléfono:", self._numero_telefonico)
        print("Correo electrónico:", self._correo_electronico)
        print("Fecha de inicio de contrato:", self._fecha_inicio_contrato)
        print("Salario:", self.__salario)