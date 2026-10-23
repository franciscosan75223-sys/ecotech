import os
from dominio import (
    Empleado,
    CuentaUsuario,
    Proyecto,
    Departamento,
    Asignacion
)
from validaciones import (
    validar_nombre,
    validar_direccion,
    validar_telefono,
    validar_correo,
    validar_fecha,
    validar_salario,
    validar_presupuesto,
    validar_rol,
    validar_nombre_entidad,
    validar_descripcion,
    validar_miembro,
    validar_departamento,
    validar_id,
    validar_horas,
    validar_nombre_usuario,
    validar_contrasena
)
from infraestructura.repositorio import (
    consultar_empleados,
    buscar_empleado,
    consultar_proyectos,
    buscar_proyecto,
    empleado_dirige_departamento
)
from infraestructura.conexion import (
    SUPABASE_PUERTO,
    SUPABASE_BASE
)

def pedir_contrasena(mensaje):
    if os.name != "nt":
        from getpass import getpass
        return getpass(mensaje)

    import msvcrt

    print(mensaje, end="", flush=True)
    caracteres = []

    while True:
        tecla = msvcrt.getwch()

        if tecla in ("\r", "\n"):
            print()
            return "".join(caracteres)

        if tecla == "\b":
            if caracteres:
                caracteres.pop()
                print("\b \b", end="", flush=True)

        elif tecla == "\x03":
            print()
            raise KeyboardInterrupt

        elif tecla == "\x1a":
            print()
            raise EOFError

        elif tecla in ("\x00", "\xe0"):
            # Descarta el segundo código de las teclas especiales.
            msvcrt.getwch()

        elif tecla.isprintable():
            caracteres.append(tecla)
            print("*", end="", flush=True)


def pedir_id(mensaje):
    return pedir_dato(mensaje, validar_id)

def pedir_dato(mensaje, validacion, ocultar=False, revisar_formato=False):
    while True:
        try:
            if ocultar:
                entrada = pedir_contrasena(mensaje)
            else:
                entrada = input(mensaje).strip()
            if revisar_formato:
                return validacion(entrada, revisar_formato=True)
            return validacion(entrada)
        except ValueError as error:
            print("Dato inválido:", error)
            if ocultar:
                print("Intente con otra contraseña para continuar.")
            else:
                print("Corrija este dato para continuar.")

def pedir_rol(conexion=None, id_empleado=None):
    while True:
        rol = pedir_dato("Rol (Empleado/Gerente): ", validar_rol)
        if conexion is not None and id_empleado is not None and rol != "Gerente":
            if empleado_dirige_departamento(conexion, id_empleado):
                print("Dato invalido: dirige un departamento. Mantenga el rol Gerente o cambie primero el responsable.")
                print("Corrija solo el rol para continuar.")
                continue
        return rol

def pedir_empleado(id_empleado, conexion=None):
    nombre = pedir_dato("Nombre: ", validar_nombre, revisar_formato=True)
    direccion = pedir_dato("Dirección: ", validar_direccion, revisar_formato=True)
    telefono = pedir_dato("Teléfono (12 en total: + y 11 números): ", validar_telefono, revisar_formato=True)
    correo = pedir_dato("Correo (debe terminar en @gmail.com): ", validar_correo, revisar_formato=True)
    fecha = pedir_dato("Inicio del contrato (AAAA-MM-DD): ", validar_fecha)
    salario = pedir_dato("Salario, usando punto para los decimales: ", validar_salario)
    rol = pedir_rol(conexion, id_empleado)
    return Empleado(
        id_empleado, nombre, direccion, telefono, correo, fecha, salario, rol
    )

def pedir_cuenta(correo, servicio):
    nombre = pedir_dato("Nombre de usuario: ", validar_nombre_usuario, revisar_formato=True)
    print("La contraseña admite mayúsculas, minúsculas, números y símbolos permitidos (8 a 128 caracteres).")
    print("No se permiten comillas, paréntesis, barras (/ o \\), corchetes ni llaves.")
    contrasena = pedir_dato("Contraseña de la cuenta: ", validar_contrasena, ocultar=True)
    return CuentaUsuario(nombre, correo, servicio, contrasena)

def _registros_para_vincular(conexion, entidad, solo_gerentes):
    if entidad == "EMPLEADO":
        disponibles = consultar_empleados(conexion)
        if solo_gerentes:
            disponibles = [empleado for empleado in disponibles if empleado.get_rol() == "Gerente"]
        mensaje = "ID del gerente: " if solo_gerentes else "ID del empleado: "
    else:
        disponibles = consultar_proyectos(conexion)
        mensaje = "ID del proyecto: "
    if not disponibles:
        if solo_gerentes:
            raise ValueError("Primero debe agregar un empleado con rol Gerente o actualizar su rol.")
        raise ValueError("Primero debe agregar al menos un " + entidad.lower() + ".")
    return disponibles, mensaje


def pedir_id_vinculado(conexion, entidad, solo_gerentes=False):
    disponibles, mensaje = _registros_para_vincular(conexion, entidad, solo_gerentes)
    buscar = buscar_empleado if entidad == "EMPLEADO" else buscar_proyecto
    print("Registros disponibles:")
    for registro in disponibles:
        print('ID {}: {}'.format(registro.get_id(), registro.get_nombre()))
    while True:
        numero = pedir_id(mensaje)
        fila = buscar(conexion, numero)
        if fila is None:
            print("Dato inválido: no existe ese ID. Corrija solo este dato.")
        elif solo_gerentes and validar_rol(fila["rol"]) != "Gerente":
            print("Dato inválido: el empleado debe tener rol Gerente. Elija otro ID.")
        else:
            return numero

def pedir_registro(conexion, entidad, id_registro=None):
    if entidad == "PROYECTO":
        nombre = pedir_dato("Nombre del proyecto: ", validar_nombre_entidad)
        descripcion = pedir_dato("Descripción del proyecto: ", validar_descripcion)
        fecha = pedir_dato("Fecha de inicio (AAAA-MM-DD): ", validar_fecha)
        miembro = pedir_dato("Miembro o referencia del equipo: ", validar_miembro)
        presupuesto = pedir_dato("Presupuesto, usando punto para los decimales: ", validar_presupuesto)
        return Proyecto(id_registro, nombre, descripcion, fecha, miembro, presupuesto)
    if entidad == "DEPARTAMENTO":
        gerente_id = pedir_id_vinculado(conexion, "EMPLEADO", solo_gerentes=True)
        nombre = pedir_dato("Nombre del departamento: ", validar_nombre_entidad)
        departamento = pedir_dato("Descripción o área del departamento: ", validar_departamento)
        return Departamento(id_registro, nombre, gerente_id, departamento)
    if entidad == "ASIGNACION":
        id_empleado = pedir_id_vinculado(conexion, "EMPLEADO")
        id_proyecto = pedir_id_vinculado(conexion, "PROYECTO")
        fecha = pedir_dato("Fecha de la asignación (AAAA-MM-DD): ", validar_fecha)
        horas = pedir_dato("Horas trabajadas (número entero): ", validar_horas)
        tareas = pedir_dato("Tareas realizadas: ", validar_descripcion)
        return Asignacion(id_registro, fecha, horas, tareas, id_empleado, id_proyecto)
    raise ValueError("La entidad solicitada no está permitida.")

def pedir_configuracion_conexion():
    host = os.getenv("SUPABASE_DB_HOST", "").strip()
    usuario = os.getenv("SUPABASE_DB_USER", "").strip()
    if not host:
        host = input("Servidor de Supabase (host del Session pooler): ").strip()
    if not usuario:
        usuario = input("Usuario de la base (postgres.ID_DEL_PROYECTO): ").strip()
    puerto = os.getenv("SUPABASE_DB_PORT", str(SUPABASE_PUERTO))
    base = os.getenv("SUPABASE_DB_NAME", SUPABASE_BASE)
    contrasena = os.getenv("SUPABASE_DB_PASSWORD")
    if not contrasena:
        contrasena = pedir_contrasena("Contraseña de la base de Supabase: ")
    return usuario, contrasena, host, puerto, base
