import json
from psycopg import (
    IntegrityError, DataError, OperationalError, InterfaceError, ProgrammingError
)
from dominio import (
    Tiempo
)
from dominio.validaciones import (
    validar_fecha,
    validar_descripcion,
    validar_id,
    validar_horas_adicionales,
    validar_nombre_usuario,
    validar_contrasena
)
from infraestructura.repositorio import (
    agregar_empleado,
    consultar_empleados,
    buscar_empleado,
    actualizar_empleado,
    eliminar_empleado,
    consultar_cuentas,
    agregar_cuenta,
    actualizar_cuenta,
    eliminar_cuenta,
    comprobar_acceso,
    buscar_registro,
    objeto_desde_fila,
    consultar_registros,
    guardar_registro,
    eliminar_registro,
    consultar_proyectos,
    consultar_departamentos,
    consultar_asignaciones,
    registrar_horas_asignacion,
    consultar_historial,
    consultar_detalle_historial,
    guardar_tiempo
)
from infraestructura.conexion import (
    configuracion_entidad
)
from infraestructura.reportes import (
    Informes
)
from presentacion.entradas import (
    pedir_id,
    pedir_dato,
    pedir_empleado,
    pedir_cuenta,
    pedir_id_vinculado,
    pedir_registro
)
from presentacion.errores import (
    mostrar_error_supabase
)


def mostrar_historial(conexion):
    entidad = input("Entidad: EMPLEADO, CUENTA_USUARIO, PROYECTO, DEPARTAMENTO o ASIGNACION (Enter para todas): ").strip().upper()
    entrada = input("ID del registro de esa entidad (Enter para todos): ").strip()
    id_registro = validar_id(entrada) if entrada else None
    entrada = input("ID del empleado (Enter para todos): ").strip()
    id_empleado = int(entrada) if entrada else None
    operacion = input(
        "Operación: AGREGAR, ACTUALIZAR o ELIMINAR (Enter para todas): "
    ).strip().upper()
    texto = input("Buscar nombre, usuario u otro texto (Enter para todos): ").strip()
    entrada = input("Cantidad de resultados, 1 a 200 [20]: ").strip()
    limite = int(entrada) if entrada else 20
    registros = consultar_historial(
        conexion, id_empleado, operacion or None, texto, limite, entidad or None, id_registro
    )
    if not registros:
        print("No hay cambios que coincidan con la búsqueda.")
        return
    for fila in registros:
        print(
            'Historial {} | {} | {} | {} {} | Empleado {} | Base de datos: {}'.format(fila['id_historial'], fila['fecha'], fila['operacion'], fila['entidad'], fila['id_registro'], fila['id_empleado'], fila['usuario_mysql'])
        )
        print(" ", fila["detalle"])
    entrada = input("ID del historial para ver antes/después (Enter para volver): ").strip()
    if not entrada:
        return
    id_historial = int(entrada)
    if id_historial <= 0:
        raise ValueError("El ID debe ser mayor que cero.")
    fila = consultar_detalle_historial(conexion, id_historial)
    if fila is None:
        print("No existe ese registro de historial.")
        return
    print('\nHistorial {}: {}'.format(fila['id_historial'], fila['detalle']))
    for campo, titulo in (
        ("datos_anteriores", "ANTES"), ("datos_nuevos", "DESPUÉS")
    ):
        print(titulo + ":")
        if fila[campo] is None:
            print("No corresponde.")
        else:
            print(json.dumps(json.loads(fila[campo]), ensure_ascii=False, indent=2))

def menu_entidad(conexion, entidad):
    configuracion_entidad(entidad)
    while True:
        print("\nGESTIÓN DE " + entidad)
        print("1. Agregar")
        print("2. Consultar todos")
        print("3. Actualizar por ID")
        print("4. Eliminar por ID")
        print("5. Buscar por ID")
        if entidad == "ASIGNACION":
            print("6. Sumar horas trabajadas")
        print("0. Volver al menú principal")
        opcion = input("Seleccione una opción: ").strip()
        try:
            if opcion == "0":
                return
            if opcion == "1":
                registro = pedir_registro(conexion, entidad)
                id_nuevo = guardar_registro(conexion, entidad, registro)
                print("Registro guardado en Supabase; cambio registrado. ID:", id_nuevo)
            elif opcion == "2":
                registros = consultar_registros(conexion, entidad)
                if not registros:
                    print("No hay registros de esta entidad.")
                for registro in registros:
                    print(registro)
            elif opcion == "3":
                id_registro = pedir_id("ID del registro a actualizar: ")
                if buscar_registro(conexion, entidad, id_registro) is None:
                    print("No existe ese registro.")
                    continue
                registro = pedir_registro(conexion, entidad, id_registro)
                if guardar_registro(conexion, entidad, registro, actualizar=True):
                    print("Registro actualizado en Supabase; cambio registrado.")
                else:
                    print("El registro ya no existe.")
            elif opcion == "4":
                id_registro = pedir_id("ID del registro a eliminar: ")
                confirmar = input("¿Eliminar este registro? (s/n): ").strip().lower()
                if confirmar != "s":
                    print("Eliminación cancelada.")
                elif eliminar_registro(conexion, entidad, id_registro):
                    print("Registro eliminado de Supabase; historial conservado.")
                else:
                    print("No existe ese registro.")
            elif opcion == "5":
                id_registro = pedir_id("ID del registro a buscar: ")
                fila = buscar_registro(conexion, entidad, id_registro)
                if fila is None:
                    print("No existe ese registro.")
                else:
                    print(objeto_desde_fila(entidad, fila))
            elif opcion == "6" and entidad == "ASIGNACION":
                id_asignacion = pedir_id("ID de la asignación: ")
                horas = pedir_dato("Horas adicionales: ", validar_horas_adicionales)
                total = registrar_horas_asignacion(conexion, id_asignacion, horas)
                if total is None:
                    print("No existe esa asignación.")
                else:
                    print('Horas guardadas en Base de datos: {}. Cambio registrado.'.format(total))
            else:
                print("Opción inválida. Elija una de las opciones mostradas.")
        except ValueError as error:
            print("Dato inválido:", error)
        except (IntegrityError, DataError, OperationalError, InterfaceError, ProgrammingError) as error:
            mostrar_error_supabase(error, conexion)

def pedir_y_guardar_tiempo(conexion):
    id_empleado = pedir_id_vinculado(conexion, "EMPLEADO")
    id_proyecto = pedir_id_vinculado(conexion, "PROYECTO")
    fecha = pedir_dato("Fecha del trabajo (AAAA-MM-DD): ", validar_fecha)
    horas = pedir_dato("Horas trabajadas (entero mayor que cero): ", validar_horas_adicionales)
    descripcion = pedir_dato("Descripción de las tareas: ", validar_descripcion)
    tiempo = Tiempo(fecha, horas, descripcion, id_empleado, id_proyecto)
    id_registro = guardar_tiempo(conexion, tiempo)
    print("Registro de tiempo guardado en Supabase. ID:", id_registro)

def mostrar_informes_desde_supabase(conexion):
    informe = Informes(
        consultar_empleados(conexion), consultar_proyectos(conexion),
        consultar_departamentos(conexion), consultar_asignaciones(conexion)
    )
    print("\nINFORME GENERAL DE ECOTECH")
    informe.generar_informes()

def exportar_informe_desde_supabase(conexion, formato):
    informe = Informes(
        consultar_empleados(conexion), consultar_proyectos(conexion),
        consultar_departamentos(conexion), consultar_asignaciones(conexion)
    )
    if formato == "excel":
        ruta = informe.exportar_excel()
    elif formato == "pdf":
        ruta = informe.exportar_pdf()
    else:
        raise ValueError("Formato no reconocido.")
    print("Informe guardado en:", ruta)
    return ruta

def menu(conexion, servicio):
    while True:
        print("\nCRUD DE EMPLEADOS Y CUENTAS - SUPABASE")
        print("1. Agregar empleado y cuenta")
        print("2. Consultar empleados")
        print("3. Actualizar empleado")
        print("4. Eliminar empleado y su cuenta")
        print("5. Actualizar cuenta de usuario")
        print("6. Comprobar acceso")
        print("7. Consultar cuentas de usuario")
        print("8. Agregar cuenta a un empleado existente")
        print("9. Eliminar solamente una cuenta")
        print("10. Consultar historial de cambios")
        print("11. Gestionar proyectos")
        print("12. Gestionar departamentos")
        print("13. Gestionar asignaciones y horas")
        print("14. Registrar tiempo (tu clase Tiempo)")
        print("15. Generar informes de Supabase")
        print("16. Guardar informe en Excel (.xlsx)")
        print("17. Guardar informe en PDF (.pdf)")
        print("0. Salir")
        opcion = input("Seleccione una opción: ").strip()
        try:
            if opcion == "1":
                empleado = pedir_empleado(None, conexion)
                empleado.asignar_cuenta(
                    pedir_cuenta(empleado.get_correo(), servicio)
                )
                id_nuevo = agregar_empleado(conexion, empleado)
                print("Empleado y cuenta guardados en Supabase. ID:", id_nuevo)
            elif opcion == "2":
                empleados = consultar_empleados(conexion)
                if not empleados:
                    print("No hay empleados registrados.")
                for empleado in empleados:
                    print(empleado)
            elif opcion == "3":
                id_empleado = pedir_id("ID del empleado a actualizar: ")
                if buscar_empleado(conexion, id_empleado) is None:
                    print("No existe un empleado con ese ID.")
                    continue
                empleado = pedir_empleado(id_empleado, conexion)
                if actualizar_empleado(conexion, empleado):
                    print("Datos guardados en Supabase; los cambios quedan en el historial.")
                else:
                    print("No existe un empleado con ese ID.")
            elif opcion == "4":
                id_empleado = pedir_id("ID del empleado a eliminar: ")
                confirmar = input("Se eliminará también su cuenta. ¿Continuar? (s/n): ")
                if confirmar.strip().lower() != "s":
                    print("Eliminación cancelada.")
                elif eliminar_empleado(conexion, id_empleado):
                    print("Empleado y cuenta eliminados de Supabase; historial conservado.")
                else:
                    print("No existe un empleado con ese ID.")
            elif opcion in ("5", "8"):
                id_empleado = pedir_id("ID del empleado: ")
                empleado = buscar_empleado(conexion, id_empleado)
                if empleado is None:
                    print("No existe un empleado con ese ID.")
                    continue
                cuenta = pedir_cuenta(empleado["correo"], servicio)
                if opcion == "5":
                    if actualizar_cuenta(conexion, id_empleado, cuenta):
                        print("Cuenta actualizada en Supabase; cambio registrado.")
                    else:
                        print("No existe una cuenta para ese empleado.")
                else:
                    id_cuenta = agregar_cuenta(conexion, id_empleado, cuenta)
                    if id_cuenta is None:
                        print("No existe un empleado con ese ID.")
                    else:
                        print("Cuenta guardada en Supabase. ID de cuenta:", id_cuenta)
            elif opcion == "6":
                nombre = pedir_dato("Nombre de usuario: ", validar_nombre_usuario, revisar_formato=True)
                contrasena = pedir_dato("Contraseña: ", validar_contrasena, ocultar=True)
                if comprobar_acceso(conexion, nombre, contrasena, servicio):
                    print("Acceso autorizado.")
                else:
                    print("Acceso rechazado.")
            elif opcion == "7":
                cuentas = consultar_cuentas(conexion)
                if not cuentas:
                    print("No hay cuentas registradas.")
                for cuenta in cuentas:
                    print(
                        'Cuenta {} | Empleado {}: {} | Usuario: {} | {}'.format(cuenta['id_cuenta'], cuenta['id_empleado'], cuenta['empleado'], cuenta['nombre_usuario'], cuenta['correo'])
                    )
            elif opcion == "9":
                id_cuenta = pedir_id("ID de la cuenta a eliminar (opción 7): ")
                confirmar = input("El empleado se conservará. ¿Eliminar cuenta? (s/n): ")
                if confirmar.strip().lower() != "s":
                    print("Eliminación cancelada.")
                elif eliminar_cuenta(conexion, id_cuenta):
                    print("Cuenta eliminada de Supabase; empleado e historial conservados.")
                else:
                    print("No existe una cuenta con ese ID.")
            elif opcion == "10":
                mostrar_historial(conexion)
            elif opcion == "11":
                menu_entidad(conexion, "PROYECTO")
            elif opcion == "12":
                menu_entidad(conexion, "DEPARTAMENTO")
            elif opcion == "13":
                menu_entidad(conexion, "ASIGNACION")
            elif opcion == "14":
                pedir_y_guardar_tiempo(conexion)
            elif opcion == "15":
                mostrar_informes_desde_supabase(conexion)
            elif opcion == "16":
                exportar_informe_desde_supabase(conexion, "excel")
            elif opcion == "17":
                exportar_informe_desde_supabase(conexion, "pdf")
            elif opcion == "0":
                break
            else:
                print("Opción inválida. Elige una opción del 0 al 17.")
        except ValueError as error:
            print("Dato inválido:", error)
        except ConnectionError:
            raise
        except PermissionError as error:
            print("No se pudo guardar el informe por falta de permisos:", error)
        except FileNotFoundError as error:
            print("No se encontro el archivo o la carpeta:", error)
        except OSError as error:
            print("No se pudo guardar el archivo:", error)
        except ModuleNotFoundError:
            print("Falta una biblioteca. Instale las dependencias de requirements.txt.")
        except (IntegrityError, DataError, OperationalError, InterfaceError, ProgrammingError) as error:
            mostrar_error_supabase(error, conexion)
