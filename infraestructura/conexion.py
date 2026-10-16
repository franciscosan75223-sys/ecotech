import psycopg

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
    if not host or not usuario or not contrasena:
        raise ValueError("Complete el servidor, usuario y contrasena de la base de Supabase.")
    return psycopg.connect(
        host=host, port=puerto, user=usuario, password=contrasena, dbname=base,
        sslmode="require", autocommit=True, connect_timeout=10,
        options="-c search_path=ecotech,pg_catalog", prepare_threshold=None
    )

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
            columnas = ", ".join((campo_id,) + campos)
            cursor.execute(f"SELECT {columnas} FROM {tabla} LIMIT 0")
            cursor.fetchall()
    finally:
        cursor.close()

def configuracion_entidad(entidad):
    if entidad not in CONFIGURACION_ENTIDADES:
        raise ValueError("La entidad solicitada no esta permitida.")
    return CONFIGURACION_ENTIDADES[entidad]

def mostrar_error_supabase(error):
    estado = error.sqlstate
    if estado == "23505":
        print("Ese usuario ya existe o el empleado ya tiene una cuenta.")
    elif estado == "23503":
        print("Revise los registros relacionados: el ID no existe o el registro todavia esta en uso.")
    elif estado in ("23514", "23502", "22001", "22003", "22007"):
        print("Un dato no cumple las restricciones de la base. Revise los valores ingresados.")
    elif estado in ("40P01", "40001", "55P03"):
        print("Otro cambio esta utilizando esos registros. Intente nuevamente.")
    elif estado in ("42P01", "42703", "3F000"):
        print("Falta el esquema de EcoTech. Ejecute ecotech_supabase.sql en el proyecto correcto.")
    elif estado == "42501":
        print("El usuario de la base no tiene permiso para realizar esta operacion.")
    elif estado and estado.startswith("28"):
        print("El usuario o la contrasena de la base son incorrectos.")
    elif estado and estado.startswith("08"):
        print("No se pudo mantener la conexion. Revise el servidor y la red.")
    else:
        print("No se completo la operacion en Supabase. Codigo:", estado or "conexion/configuracion")