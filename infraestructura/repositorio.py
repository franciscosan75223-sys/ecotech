import json

from psycopg import Error
from psycopg.sql import SQL, Identifier, Placeholder
from psycopg.rows import dict_row

from dominio import (
    Empleado,
    CuentaUsuario,
    Proyecto,
    Departamento,
    Asignacion
)

from validaciones import (
    validar_id,
    validar_rol,
    validar_horas_adicionales
)

from infraestructura.conexion import configuracion_entidad


REGISTRO_NO_ENCONTRADO = "No existe el registro solicitado."


class RegistroNoEncontradoError(LookupError):
    """El registro solicitado no existe en la base de datos."""


def leer_empleado(cursor, id_empleado):
    cursor.execute("""
        SELECT id_empleado, nombre, direccion, telefono,
               correo, fecha_inicio, salario, rol
        FROM empleado
        WHERE id_empleado = %s
        FOR UPDATE
    """, (id_empleado,))

    return cursor.fetchone()


def leer_cuenta(cursor, id_empleado):
    cursor.execute("""
        SELECT id_cuenta, id_empleado, nombre_usuario, correo
        FROM cuenta_usuario
        WHERE id_empleado = %s
        FOR UPDATE
    """, (id_empleado,))

    return cursor.fetchone()


def registrar_historial(
    cursor, operacion, entidad, id_empleado,
    detalle, anteriores=None, nuevos=None, id_registro=None
):
    antes = None
    despues = None

    if anteriores is not None:
        antes = json.dumps(
            anteriores,
            ensure_ascii=False,
            default=str
        )

    if nuevos is not None:
        despues = json.dumps(
            nuevos,
            ensure_ascii=False,
            default=str
        )

    if id_registro is None:
        if entidad == "EMPLEADO":
            id_registro = id_empleado

        elif entidad == "CUENTA_USUARIO":
            datos_cuenta = (
                nuevos if nuevos is not None else anteriores
            )
            id_registro = datos_cuenta["id_cuenta"]

    if id_registro is None:
        raise ValueError(
            "Falta el ID del registro para guardar su historial."
        )

    cursor.execute("""
        INSERT INTO historial_cambios
        (
            operacion,
            entidad,
            id_registro,
            id_empleado,
            usuario_mysql,
            detalle,
            datos_anteriores,
            datos_nuevos
        )
        VALUES (%s, %s, %s, %s, CURRENT_USER, %s, %s, %s)
    """, (
        operacion,
        entidad,
        id_registro,
        id_empleado,
        detalle,
        antes,
        despues
    ))


def agregar_empleado(conexion, empleado):
    cuenta = empleado.get_cuenta_usuario()

    if cuenta is None:
        raise ValueError(
            "Debe asignar una cuenta antes de guardar el empleado."
        )

    token = cuenta.get_contrasena_cifrada()
    cursor = conexion.cursor(row_factory=dict_row)

    try:
        with conexion.transaction():
            cursor.execute("""
                INSERT INTO empleado
                (
                    nombre,
                    direccion,
                    telefono,
                    correo,
                    fecha_inicio,
                    salario,
                    rol
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id_empleado
            """, (
                empleado.get_nombre(),
                empleado.get_direccion(),
                empleado.get_telefono(),
                empleado.get_correo(),
                empleado.get_fecha_inicio(),
                empleado.get_salario(),
                empleado.get_rol()
            ))

            id_nuevo = cursor.fetchone()["id_empleado"]

            cursor.execute("""
                INSERT INTO cuenta_usuario
                (
                    id_empleado,
                    nombre_usuario,
                    correo,
                    contrasena_cifrada
                )
                VALUES (%s, %s, %s, %s)
            """, (
                id_nuevo,
                cuenta.get_nombre(),
                cuenta.get_correo(),
                token
            ))

            datos_empleado = leer_empleado(cursor, id_nuevo)
            datos_cuenta = leer_cuenta(cursor, id_nuevo)

            registrar_historial(
                cursor,
                "AGREGAR",
                "EMPLEADO",
                id_nuevo,
                "Empleado creado.",
                nuevos=datos_empleado
            )

            registrar_historial(
                cursor,
                "AGREGAR",
                "CUENTA_USUARIO",
                id_nuevo,
                "Cuenta creada con contraseña cifrada.",
                nuevos=datos_cuenta
            )

            return id_nuevo

    finally:
        cursor.close()


def consultar_empleados(conexion):
    cursor = conexion.cursor(row_factory=dict_row)

    try:
        cursor.execute("""
            SELECT id_empleado, nombre, direccion, telefono,
                   correo, fecha_inicio, salario, rol
            FROM empleado
            ORDER BY id_empleado
        """)

        empleados = []

        for fila in cursor.fetchall():
            empleados.append(
                Empleado(
                    fila["id_empleado"],
                    fila["nombre"],
                    fila["direccion"],
                    fila["telefono"],
                    fila["correo"],
                    fila["fecha_inicio"],
                    fila["salario"],
                    fila["rol"]
                )
            )

        return empleados

    finally:
        cursor.close()


def buscar_empleado(conexion, id_empleado):
    cursor = conexion.cursor(row_factory=dict_row)

    try:
        cursor.execute("""
            SELECT id_empleado, nombre, correo, rol
            FROM empleado
            WHERE id_empleado = %s
        """, (id_empleado,))

        return cursor.fetchone()

    finally:
        cursor.close()


def actualizar_empleado(conexion, empleado):
    cursor = conexion.cursor(row_factory=dict_row)

    try:
        cursor.execute("BEGIN")

        anteriores = leer_empleado(
            cursor,
            empleado.get_id()
        )

        if anteriores is None:
            raise RegistroNoEncontradoError(
                REGISTRO_NO_ENCONTRADO
            )

        cuenta_anterior = leer_cuenta(
            cursor,
            empleado.get_id()
        )

        if empleado.get_rol() != "Gerente":
            cursor.execute("""
                SELECT id_departamento
                FROM departamento
                WHERE gerente_id = %s
                LIMIT 1
            """, (empleado.get_id(),))

            if cursor.fetchone() is not None:
                raise ValueError(
                    "Ese empleado dirige un departamento. "
                    "Cambie primero el gerente del departamento."
                )

        cursor.execute("""
            UPDATE empleado
            SET nombre = %s,
                direccion = %s,
                telefono = %s,
                correo = %s,
                fecha_inicio = %s,
                salario = %s,
                rol = %s
            WHERE id_empleado = %s
        """, (
            empleado.get_nombre(),
            empleado.get_direccion(),
            empleado.get_telefono(),
            empleado.get_correo(),
            empleado.get_fecha_inicio(),
            empleado.get_salario(),
            empleado.get_rol(),
            empleado.get_id()
        ))

        cursor.execute("""
            UPDATE cuenta_usuario
            SET correo = %s
            WHERE id_empleado = %s
        """, (
            empleado.get_correo(),
            empleado.get_id()
        ))

        nuevos = leer_empleado(
            cursor,
            empleado.get_id()
        )

        cuenta_nueva = leer_cuenta(
            cursor,
            empleado.get_id()
        )

        if anteriores != nuevos:
            registrar_historial(
                cursor,
                "ACTUALIZAR",
                "EMPLEADO",
                empleado.get_id(),
                "Datos del empleado actualizados.",
                anteriores,
                nuevos
            )

        if cuenta_anterior != cuenta_nueva:
            registrar_historial(
                cursor,
                "ACTUALIZAR",
                "CUENTA_USUARIO",
                empleado.get_id(),
                "Correo sincronizado con el empleado.",
                cuenta_anterior,
                cuenta_nueva
            )

        conexion.commit()
        return True

    except RegistroNoEncontradoError:
        if not conexion.closed:
            conexion.rollback()

        return False

    except (Error, ValueError, TypeError, KeyError):
        if not conexion.closed:
            conexion.rollback()

        raise

    finally:
        cursor.close()


def eliminar_empleado(conexion, id_empleado):
    cursor = conexion.cursor(row_factory=dict_row)

    try:
        cursor.execute("BEGIN")

        anteriores = leer_empleado(cursor, id_empleado)

        if anteriores is None:
            raise RegistroNoEncontradoError(
                REGISTRO_NO_ENCONTRADO
            )

        cuenta = leer_cuenta(cursor, id_empleado)

        cursor.execute("""
            DELETE FROM empleado
            WHERE id_empleado = %s
        """, (id_empleado,))

        registrar_historial(
            cursor,
            "ELIMINAR",
            "EMPLEADO",
            id_empleado,
            "Empleado eliminado.",
            anteriores=anteriores
        )

        if cuenta is not None:
            registrar_historial(
                cursor,
                "ELIMINAR",
                "CUENTA_USUARIO",
                id_empleado,
                "Cuenta eliminada junto con su empleado.",
                anteriores=cuenta
            )

        conexion.commit()
        return True

    except RegistroNoEncontradoError:
        if not conexion.closed:
            conexion.rollback()

        return False

    except (Error, ValueError, TypeError, KeyError):
        if not conexion.closed:
            conexion.rollback()

        raise

    finally:
        cursor.close()


def consultar_cuentas(conexion):
    cursor = conexion.cursor(row_factory=dict_row)

    try:
        cursor.execute("""
            SELECT c.id_cuenta,
                   c.id_empleado,
                   c.nombre_usuario,
                   c.correo,
                   e.nombre AS empleado
            FROM cuenta_usuario c
            INNER JOIN empleado e
                ON e.id_empleado = c.id_empleado
            ORDER BY c.id_cuenta
        """)

        return cursor.fetchall()

    finally:
        cursor.close()


def agregar_cuenta(conexion, id_empleado, cuenta):
    token = cuenta.get_contrasena_cifrada()
    cursor = conexion.cursor(row_factory=dict_row)

    try:
        with conexion.transaction():
            empleado = leer_empleado(
                cursor,
                id_empleado
            )

            if empleado is None:
                return None

            if cuenta.get_correo() != empleado["correo"]:
                raise ValueError(
                    "La cuenta debe usar el correo del empleado."
                )

            cursor.execute("""
                INSERT INTO cuenta_usuario
                (
                    id_empleado,
                    nombre_usuario,
                    correo,
                    contrasena_cifrada
                )
                VALUES (%s, %s, %s, %s)
                RETURNING id_cuenta
            """, (
                id_empleado,
                cuenta.get_nombre(),
                cuenta.get_correo(),
                token
            ))

            id_cuenta = cursor.fetchone()["id_cuenta"]
            datos = leer_cuenta(cursor, id_empleado)

            registrar_historial(
                cursor,
                "AGREGAR",
                "CUENTA_USUARIO",
                id_empleado,
                "Cuenta creada para un empleado existente.",
                nuevos=datos
            )

            return id_cuenta

    finally:
        cursor.close()


def actualizar_cuenta(conexion, id_empleado, cuenta):
    token = cuenta.get_contrasena_cifrada()
    cursor = conexion.cursor(row_factory=dict_row)

    try:
        cursor.execute("BEGIN")

        empleado = leer_empleado(
            cursor,
            id_empleado
        )

        if empleado is None:
            raise RegistroNoEncontradoError(
                REGISTRO_NO_ENCONTRADO
            )

        if cuenta.get_correo() != empleado["correo"]:
            raise ValueError(
                "La cuenta debe usar el correo del empleado."
            )

        anteriores = leer_cuenta(
            cursor,
            id_empleado
        )

        if anteriores is None:
            raise RegistroNoEncontradoError(
                REGISTRO_NO_ENCONTRADO
            )

        cursor.execute("""
            UPDATE cuenta_usuario
            SET nombre_usuario = %s,
                contrasena_cifrada = %s
            WHERE id_empleado = %s
        """, (
            cuenta.get_nombre(),
            token,
            id_empleado
        ))

        nuevos = leer_cuenta(cursor, id_empleado)

        registrar_historial(
            cursor,
            "ACTUALIZAR",
            "CUENTA_USUARIO",
            id_empleado,
            "Usuario y contraseña actualizados; contraseña oculta.",
            anteriores,
            nuevos
        )

        conexion.commit()
        return True

    except RegistroNoEncontradoError:
        if not conexion.closed:
            conexion.rollback()

        return False

    except (Error, ValueError, TypeError, KeyError):
        if not conexion.closed:
            conexion.rollback()

        raise

    finally:
        cursor.close()


def eliminar_cuenta(conexion, id_cuenta):
    cursor = conexion.cursor(row_factory=dict_row)

    try:
        cursor.execute("BEGIN")

        cursor.execute("""
            SELECT id_cuenta,
                   id_empleado,
                   nombre_usuario,
                   correo
            FROM cuenta_usuario
            WHERE id_cuenta = %s
            FOR UPDATE
        """, (id_cuenta,))

        anteriores = cursor.fetchone()

        if anteriores is None:
            raise RegistroNoEncontradoError(
                REGISTRO_NO_ENCONTRADO
            )

        cursor.execute("""
            DELETE FROM cuenta_usuario
            WHERE id_cuenta = %s
        """, (id_cuenta,))

        registrar_historial(
            cursor,
            "ELIMINAR",
            "CUENTA_USUARIO",
            anteriores["id_empleado"],
            "Cuenta eliminada; el empleado se conserva.",
            anteriores=anteriores
        )

        conexion.commit()
        return True

    except RegistroNoEncontradoError:
        if not conexion.closed:
            conexion.rollback()

        return False

    except (Error, ValueError, TypeError, KeyError):
        if not conexion.closed:
            conexion.rollback()

        raise

    finally:
        cursor.close()


def comprobar_acceso(conexion, nombre, contrasena, servicio):
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            SELECT nombre_usuario,
                   correo,
                   contrasena_cifrada
            FROM cuenta_usuario
            WHERE nombre_usuario = %s
        """, (nombre,))

        fila = cursor.fetchone()

        if fila is None:
            return False

        cuenta = CuentaUsuario(
            fila[0],
            fila[1],
            servicio
        )

        cuenta.cargar_contrasena_cifrada(fila[2])

        return cuenta.acceso_cuenta(
            nombre,
            contrasena
        )

    finally:
        cursor.close()


def leer_registro(cursor, entidad, id_registro, bloquear=False):
    tabla, campo_id, campos = configuracion_entidad(entidad)

    columnas = SQL(", ").join(
        Identifier(campo)
        for campo in (campo_id,) + campos
    )

    consulta = SQL(
        "SELECT {} FROM {} WHERE {} = %s"
    ).format(
        columnas,
        Identifier(tabla),
        Identifier(campo_id)
    )

    if bloquear:
        consulta += SQL(" FOR UPDATE")

    cursor.execute(
        consulta,
        (validar_id(id_registro),)
    )

    return cursor.fetchone()


def buscar_registro(conexion, entidad, id_registro):
    cursor = conexion.cursor(row_factory=dict_row)

    try:
        return leer_registro(
            cursor,
            entidad,
            id_registro
        )

    finally:
        cursor.close()


def objeto_desde_fila(entidad, fila):
    if entidad == "PROYECTO":
        return Proyecto(
            fila["id_proyecto"],
            fila["nombre"],
            fila["descripcion_proyecto"],
            fila["fecha_de_inicio"],
            fila["miembro"],
            fila["presupuesto"]
        )

    if entidad == "DEPARTAMENTO":
        return Departamento(
            fila["id_departamento"],
            fila["nombre"],
            fila["gerente_id"],
            fila["departamento"]
        )

    if entidad == "ASIGNACION":
        return Asignacion(
            fila["id_asignacion"],
            fila["fecha"],
            fila["horas_trabajadas"],
            fila["tareas_realizadas"],
            fila["id_empleado"],
            fila["id_proyecto"]
        )

    raise ValueError(
        "La entidad solicitada no está permitida."
    )


def consultar_registros(conexion, entidad):
    tabla, campo_id, campos = configuracion_entidad(entidad)

    columnas = SQL(", ").join(
        Identifier(campo)
        for campo in (campo_id,) + campos
    )

    consulta = SQL(
        "SELECT {} FROM {} ORDER BY {}"
    ).format(
        columnas,
        Identifier(tabla),
        Identifier(campo_id)
    )

    cursor = conexion.cursor(row_factory=dict_row)

    try:
        cursor.execute(consulta)

        return [
            objeto_desde_fila(entidad, fila)
            for fila in cursor.fetchall()
        ]

    finally:
        cursor.close()


def verificar_relaciones(cursor, entidad, datos):
    if entidad == "DEPARTAMENTO":
        gerente = leer_empleado(
            cursor,
            datos["gerente_id"]
        )

        if gerente is None:
            raise ValueError(
                "No existe el empleado elegido como gerente."
            )

        if validar_rol(gerente["rol"]) != "Gerente":
            raise ValueError(
                "El responsable del departamento debe tener el rol Gerente."
            )

    elif entidad == "ASIGNACION":
        if (
            datos["id_empleado"] is None
            or datos["id_proyecto"] is None
        ):
            raise ValueError(
                "Debe vincular la asignación con un empleado y un proyecto."
            )

        if leer_empleado(cursor, datos["id_empleado"]) is None:
            raise ValueError(
                "No existe el empleado de la asignación."
            )

        proyecto = leer_registro(
            cursor,
            "PROYECTO",
            datos["id_proyecto"],
            bloquear=True
        )

        if proyecto is None:
            raise ValueError(
                "No existe el proyecto de la asignación."
            )


def empleado_relacionado(entidad, datos):
    if entidad == "DEPARTAMENTO":
        return datos["gerente_id"]

    if entidad == "ASIGNACION":
        return datos["id_empleado"]

    return None


def guardar_registro(
    conexion, entidad, registro, actualizar=False
):
    if actualizar:
        return actualizar_registro(
            conexion,
            entidad,
            registro
        )

    return agregar_registro(
        conexion,
        entidad,
        registro
    )


def agregar_registro(conexion, entidad, registro):
    tabla, campo_id, campos = configuracion_entidad(entidad)

    datos = registro.get_datos()
    valores = tuple(datos[campo] for campo in campos)

    columnas = SQL(", ").join(
        Identifier(campo)
        for campo in campos
    )

    parametros = SQL(", ").join(
        Placeholder()
        for _ in campos
    )

    consulta = SQL(
        "INSERT INTO {} ({}) VALUES ({}) RETURNING {}"
    ).format(
        Identifier(tabla),
        columnas,
        parametros,
        Identifier(campo_id)
    )

    cursor = conexion.cursor(row_factory=dict_row)

    try:
        with conexion.transaction():
            verificar_relaciones(
                cursor,
                entidad,
                datos
            )

            cursor.execute(consulta, valores)

            id_registro = cursor.fetchone()[campo_id]

            nuevos = leer_registro(
                cursor,
                entidad,
                id_registro
            )

            registrar_historial(
                cursor,
                "AGREGAR",
                entidad,
                empleado_relacionado(entidad, nuevos),
                entidad + ": registro guardado.",
                nuevos=nuevos,
                id_registro=id_registro
            )

        return id_registro

    finally:
        cursor.close()


def actualizar_registro(conexion, entidad, registro):
    tabla, campo_id, campos = configuracion_entidad(entidad)

    id_registro = validar_id(registro.get_id())
    datos = registro.get_datos()
    valores = tuple(datos[campo] for campo in campos)

    cambios = SQL(", ").join(
        SQL("{} = %s").format(Identifier(campo))
        for campo in campos
    )

    consulta = SQL(
        "UPDATE {} SET {} WHERE {} = %s"
    ).format(
        Identifier(tabla),
        cambios,
        Identifier(campo_id)
    )

    cursor = conexion.cursor(row_factory=dict_row)

    try:
        cursor.execute("BEGIN")

        anteriores = leer_registro(
            cursor,
            entidad,
            id_registro,
            bloquear=True
        )

        if anteriores is None:
            raise RegistroNoEncontradoError(
                REGISTRO_NO_ENCONTRADO
            )

        verificar_relaciones(
            cursor,
            entidad,
            datos
        )

        cursor.execute(
            consulta,
            valores + (id_registro,)
        )

        nuevos = leer_registro(
            cursor,
            entidad,
            id_registro
        )

        if anteriores != nuevos:
            registrar_historial(
                cursor,
                "ACTUALIZAR",
                entidad,
                empleado_relacionado(entidad, nuevos),
                entidad + ": registro actualizado.",
                anteriores,
                nuevos,
                id_registro
            )

        conexion.commit()
        return True

    except RegistroNoEncontradoError:
        if not conexion.closed:
            conexion.rollback()

        return False

    except (Error, ValueError, TypeError, KeyError):
        if not conexion.closed:
            conexion.rollback()

        raise

    finally:
        cursor.close()


def eliminar_registro(conexion, entidad, id_registro):
    tabla, campo_id, _ = configuracion_entidad(entidad)
    id_registro = validar_id(id_registro)

    cursor = conexion.cursor(row_factory=dict_row)

    try:
        cursor.execute("BEGIN")

        anteriores = leer_registro(
            cursor,
            entidad,
            id_registro,
            bloquear=True
        )

        if anteriores is None:
            raise RegistroNoEncontradoError(
                REGISTRO_NO_ENCONTRADO
            )

        consulta = SQL(
            "DELETE FROM {} WHERE {} = %s"
        ).format(
            Identifier(tabla),
            Identifier(campo_id)
        )

        cursor.execute(
            consulta,
            (id_registro,)
        )

        registrar_historial(
            cursor,
            "ELIMINAR",
            entidad,
            empleado_relacionado(entidad, anteriores),
            "{}: registro eliminado.".format(entidad),
            anteriores=anteriores,
            id_registro=id_registro
        )

        conexion.commit()
        return True

    except RegistroNoEncontradoError:
        if not conexion.closed:
            conexion.rollback()

        return False

    except (Error, ValueError, TypeError, KeyError):
        if not conexion.closed:
            conexion.rollback()

        raise

    finally:
        cursor.close()


def agregar_proyecto(conexion, proyecto):
    return guardar_registro(conexion, 'PROYECTO', proyecto)


def actualizar_proyecto(conexion, proyecto):
    return guardar_registro(conexion, 'PROYECTO', proyecto, actualizar=True)


def consultar_proyectos(conexion):
    return consultar_registros(conexion, 'PROYECTO')


def buscar_proyecto(conexion, id_proyecto):
    return buscar_registro(conexion, 'PROYECTO', id_proyecto)


def eliminar_proyecto(conexion, id_proyecto):
    return eliminar_registro(conexion, 'PROYECTO', id_proyecto)


def agregar_departamento(conexion, departamento):
    return guardar_registro(conexion, 'DEPARTAMENTO', departamento)


def actualizar_departamento(conexion, departamento):
    return guardar_registro(conexion, 'DEPARTAMENTO', departamento, actualizar=True)


def consultar_departamentos(conexion):
    return consultar_registros(conexion, 'DEPARTAMENTO')


def buscar_departamento(conexion, id_departamento):
    return buscar_registro(conexion, 'DEPARTAMENTO', id_departamento)


def eliminar_departamento(conexion, id_departamento):
    return eliminar_registro(conexion, 'DEPARTAMENTO', id_departamento)


def agregar_asignacion(conexion, asignacion):
    return guardar_registro(conexion, 'ASIGNACION', asignacion)


def actualizar_asignacion(conexion, asignacion):
    return guardar_registro(conexion, 'ASIGNACION', asignacion, actualizar=True)


def consultar_asignaciones(conexion):
    return consultar_registros(conexion, 'ASIGNACION')


def buscar_asignacion(conexion, id_asignacion):
    return buscar_registro(conexion, 'ASIGNACION', id_asignacion)


def eliminar_asignacion(conexion, id_asignacion):
    return eliminar_registro(conexion, 'ASIGNACION', id_asignacion)


def registrar_horas_asignacion(
    conexion, id_asignacion, horas
):
    horas = validar_horas_adicionales(horas)
    cursor = conexion.cursor(row_factory=dict_row)

    try:
        cursor.execute("BEGIN")

        anteriores = leer_registro(
            cursor,
            "ASIGNACION",
            id_asignacion,
            bloquear=True
        )

        if anteriores is None:
            raise RegistroNoEncontradoError(
                REGISTRO_NO_ENCONTRADO
            )

        asignacion = objeto_desde_fila(
            "ASIGNACION",
            anteriores
        )

        asignacion.sumar_horas(horas)

        cursor.execute("""
            UPDATE asignacion
            SET horas_trabajadas = horas_trabajadas + %s
            WHERE id_asignacion = %s
        """, (
            horas,
            id_asignacion
        ))

        nuevos = leer_registro(
            cursor,
            "ASIGNACION",
            id_asignacion
        )

        registrar_historial(
            cursor,
            "ACTUALIZAR",
            "ASIGNACION",
            nuevos["id_empleado"],
            "Se agregaron {} horas.".format(horas),
            anteriores,
            nuevos,
            id_asignacion
        )

        total = nuevos["horas_trabajadas"]

        conexion.commit()
        return total

    except RegistroNoEncontradoError:
        if not conexion.closed:
            conexion.rollback()

        return None

    except (Error, ValueError, TypeError, KeyError):
        if not conexion.closed:
            conexion.rollback()

        raise

    finally:
        cursor.close()


def consultar_historial(
    conexion, id_empleado=None, operacion=None,
    texto="", limite=20, entidad=None, id_registro=None
):
    if id_empleado is not None and id_empleado <= 0:
        raise ValueError(
            "El ID debe ser mayor que cero."
        )

    if operacion is not None and operacion not in (
        "AGREGAR",
        "ACTUALIZAR",
        "ELIMINAR"
    ):
        raise ValueError(
            "Operación de historial inválida."
        )

    if not 1 <= limite <= 200:
        raise ValueError(
            "El límite debe estar entre 1 y 200."
        )

    entidades_permitidas = (
        "EMPLEADO",
        "CUENTA_USUARIO",
        "PROYECTO",
        "DEPARTAMENTO",
        "ASIGNACION"
    )

    if entidad is not None and entidad not in entidades_permitidas:
        raise ValueError(
            "Entidad de historial inválida."
        )

    if id_registro is not None:
        validar_id(id_registro)

        if entidad is None:
            raise ValueError(
                "Seleccione una entidad para filtrar por el ID de un registro."
            )

    consulta = """
        SELECT id_historial, fecha, operacion, entidad,
               id_registro, id_empleado, usuario_mysql, detalle
        FROM historial_cambios
        WHERE 1 = 1
    """

    datos = []

    if entidad is not None:
        consulta += " AND entidad = %s"
        datos.append(entidad)

    if id_registro is not None:
        consulta += " AND id_registro = %s"
        datos.append(id_registro)

    if id_empleado is not None:
        consulta += " AND id_empleado = %s"
        datos.append(id_empleado)

    if operacion is not None:
        consulta += " AND operacion = %s"
        datos.append(operacion)

    if texto:
        consulta += """
            AND (
                strpos(detalle, %s) > 0
                OR strpos(COALESCE(datos_anteriores, ''), %s) > 0
                OR strpos(COALESCE(datos_nuevos, ''), %s) > 0
            )
        """

        datos.extend([texto, texto, texto])

    consulta += " ORDER BY fecha DESC, id_historial DESC LIMIT %s"
    datos.append(limite)

    cursor = conexion.cursor(row_factory=dict_row)

    try:
        cursor.execute(
            consulta,
            tuple(datos)
        )

        return cursor.fetchall()

    finally:
        cursor.close()


def consultar_detalle_historial(conexion, id_historial):
    cursor = conexion.cursor(row_factory=dict_row)

    try:
        cursor.execute("""
            SELECT id_historial, fecha, operacion, entidad,
                   id_registro, id_empleado, usuario_mysql,
                   detalle, datos_anteriores, datos_nuevos
            FROM historial_cambios
            WHERE id_historial = %s
        """, (id_historial,))

        return cursor.fetchone()

    finally:
        cursor.close()


def contar_cuentas(conexion):
    cursor = conexion.cursor()

    try:
        cursor.execute(
            "SELECT COUNT(*) FROM cuenta_usuario"
        )

        return cursor.fetchone()[0]

    finally:
        cursor.close()


def empleado_dirige_departamento(conexion, id_empleado):
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            SELECT id_departamento
            FROM departamento
            WHERE gerente_id = %s
            LIMIT 1
        """, (validar_id(id_empleado),))

        return cursor.fetchone() is not None

    finally:
        cursor.close()


def guardar_tiempo(conexion, tiempo):
    horas = validar_horas_adicionales(
        tiempo.get_horas_trabajadas()
    )

    asignacion = Asignacion(
        None,
        tiempo.fecha,
        horas,
        tiempo.get_descripcion_de_tareas(),
        tiempo.empleado,
        tiempo.proyecto
    )

    return agregar_asignacion(
        conexion,
        asignacion
    )
