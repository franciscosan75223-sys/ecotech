import psycopg
from psycopg.sql import SQL, Identifier

SUPABASE_PUERTO = 5432
SUPABASE_BASE = 'postgres'

CONFIGURACION_ENTIDADES = {
    "PROYECTO": ("proyecto", "id_proyecto", (
        "nombre", "descripcion_proyecto", "fecha_de_inicio", "miembro", "presupuesto")),
    "DEPARTAMENTO": ("departamento", "id_departamento", (
        "nombre", "departamento", "gerente_id")),
    "ASIGNACION": ("asignacion", "id_asignacion", (
        "fecha", "horas_trabajadas", "tareas_realizadas", "id_empleado", "id_proyecto"))
}

def conectar_supabase(usuario, contrasena, host, puerto=SUPABASE_PUERTO, base=SUPABASE_BASE):
    if not host or not usuario or not contrasena or not base:
        raise ValueError("Complete el servidor, usuario, contrasena y base de Supabase.")
    try:
        puerto = int(str(puerto))
    except ValueError as error:
        raise ValueError("El puerto debe ser un numero entero.") from error
    if not 1 <= puerto <= 65535:
        raise ValueError("El puerto debe estar entre 1 y 65535.")
    try:
        return psycopg.connect(
            host=host, port=puerto, user=usuario, password=contrasena, dbname=base,
            sslmode="require", autocommit=True, connect_timeout=10,
            options="-c search_path=ecotech,pg_catalog", prepare_threshold=None
        )
    except psycopg.errors.InvalidCatalogName as error:
        raise ValueError("La base de datos indicada no existe.") from error
    except (psycopg.OperationalError, psycopg.InterfaceError) as error:
        estado = error.sqlstate
        if estado and estado.startswith("28"):
            raise PermissionError("El usuario o la contrasena de Supabase son incorrectos.") from error
        if estado == "3D000":
            raise ValueError("La base de datos indicada no existe.") from error
        raise ConnectionError(
            "No se pudo conectar con Supabase. Revise el servidor, puerto, credenciales, red y disponibilidad del servicio."
        ) from error

def verificar_tablas(conexion):
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT id_empleado, nombre, direccion, telefono, correo, fecha_inicio, salario, rol FROM empleado LIMIT 0")
        cursor.fetchall()
        cursor.execute("SELECT id_cuenta, id_empleado, nombre_usuario, correo, contrasena_cifrada FROM cuenta_usuario LIMIT 0")
        cursor.fetchall()
        cursor.execute("SELECT id_historial, fecha, operacion, entidad, id_registro, id_empleado, usuario_mysql, detalle, datos_anteriores, datos_nuevos FROM historial_cambios LIMIT 0")
        cursor.fetchall()
        for entidad in CONFIGURACION_ENTIDADES:
            tabla, campo_id, campos = CONFIGURACION_ENTIDADES[entidad]
            columnas = SQL(", ").join(Identifier(campo) for campo in (campo_id,) + campos)
            consulta = SQL("SELECT {} FROM {} LIMIT 0").format(columnas, Identifier(tabla))
            cursor.execute(consulta)
            cursor.fetchall()
    finally:
        cursor.close()

def configuracion_entidad(entidad):
    if entidad not in CONFIGURACION_ENTIDADES:
        raise ValueError("La entidad solicitada no esta permitida.")
    return CONFIGURACION_ENTIDADES[entidad]

def es_error_conexion(error, conexion=None):
    estado = error.sqlstate
    if conexion is not None and (conexion.closed or conexion.broken):
        return True
    if estado and (estado.startswith("08") or estado in ("57P01", "57P02", "57P03")):
        return True
    return isinstance(error, psycopg.OperationalError) and estado is None