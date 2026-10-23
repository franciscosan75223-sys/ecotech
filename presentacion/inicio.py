from pathlib import Path
import os

from dotenv import load_dotenv
from psycopg import (
    IntegrityError,
    DataError,
    OperationalError,
    InterfaceError,
    ProgrammingError
)

from infraestructura.conexion import conectar_supabase, verificar_tablas
from infraestructura.repositorio import contar_cuentas
from dominio.servicioCifrado import ServicioCifrado
from presentacion.entradas import (
    pedir_configuracion_conexion,
    pedir_contrasena
)
from presentacion.errores import mostrar_error_supabase
from presentacion.menu import menu


def confirmar_reintento():
    while True:
        respuesta = input(
            "¿Desea intentar con otra contraseña? (S/N): "
        ).strip().upper()

        if respuesta in ("S", "N"):
            return respuesta == "S"

        print("Ingrese S para reintentar o N para salir.")


def conectar_con_reintentos():
    usuario, contrasena, host, puerto, base = pedir_configuracion_conexion()

    while True:
        if not contrasena:
            print("La contraseña no puede estar vacía.")
            contrasena = pedir_contrasena(
                "Contraseña de la base de Supabase: "
            )
            continue

        try:
            return conectar_supabase(
                usuario, contrasena, host, puerto, base
            )

        except ConnectionError as error:
            print(error)
            return None

        except PermissionError as error:
            print(error)

            if not confirmar_reintento():
                print("Programa finalizado.")
                return None

            contrasena = pedir_contrasena(
                "Ingrese nuevamente la contraseña de Supabase: "
            )


def confirmar_recuperacion_clave():
    print("Falta la clave de cifrado y existen cuentas guardadas.")
    print("Si conserva la clave original, restaurela antes de continuar.")
    print("Con una clave nueva debera restablecer las contrasenas de las cuentas.")
    print("Se conservan los empleados, proyectos, departamentos, horas e historial.")
    respuesta = input("Escriba CREAR NUEVA CLAVE para confirmar, o Enter para salir: ")
    return respuesta.strip() == "CREAR NUEVA CLAVE"


def preparar_servicio_cifrado(conexion, carpeta_proyecto):
    ruta_configurada = os.getenv("ECOTECH_FERNET_KEY_FILE", "").strip()
    archivo_clave = Path(ruta_configurada or "clave_fernet.key").expanduser()
    if not archivo_clave.is_absolute():
        archivo_clave = carpeta_proyecto / archivo_clave

    if archivo_clave.exists():
        return ServicioCifrado(archivo_clave)

    recuperar = contar_cuentas(conexion) > 0
    if recuperar and not confirmar_recuperacion_clave():
        return None

    servicio = ServicioCifrado(archivo_clave)
    if recuperar:
        print("Clave nueva creada. Guarde una copia privada de este archivo.")
        print("Use la opcion 7 para consultar las cuentas y la 5 para restablecer cada contrasena.")
    return servicio


def mostrar_error_base_datos(error, conexion):
    try:
        mostrar_error_supabase(error, conexion)
    except ConnectionError as error_conexion:
        print("Error de conexión:", error_conexion)


def iniciar_programa():
    conexion = None
    carpeta_proyecto = Path(__file__).resolve().parent.parent

    try:
        load_dotenv(carpeta_proyecto / ".env")
        print("ECOTECH - SUPABASE (POSTGRESQL)")

        conexion = conectar_con_reintentos()

        if conexion is None:
            return

        verificar_tablas(conexion)

        servicio = preparar_servicio_cifrado(
            conexion, carpeta_proyecto
        )

        if servicio is None:
            print("Recuperacion cancelada. Programa finalizado.")
            return

        print("Conexión a Supabase lista.")
        menu(conexion, servicio)

    except ConnectionError as error:
        print("Error de conexión:", error)

    except (
        IntegrityError,
        DataError,
        OperationalError,
        InterfaceError,
        ProgrammingError
    ) as error:
        mostrar_error_base_datos(error, conexion)

    except PermissionError as error:
        print("No se pudo acceder al servicio o al archivo:", error)

    except FileNotFoundError as error:
        print("No se encontró un archivo necesario:", error)

    except (OSError, ValueError) as error:
        print("No se pudo iniciar o completar el programa:", error)

    except (KeyboardInterrupt, EOFError):
        print("\nPrograma finalizado.")

    finally:
        if conexion is not None:
            conexion.close()
