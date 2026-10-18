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
from infraestructura.seguridad import ServicioCifrado
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

        except (PermissionError, ConnectionError) as error:
            print("No se pudo conectar:", error)

            if not confirmar_reintento():
                print("Programa finalizado.")
                return None

            contrasena = pedir_contrasena(
                "Ingrese nuevamente la contraseña de Supabase: "
            )


def preparar_servicio_cifrado(conexion, carpeta_proyecto):
    ruta_configurada = os.getenv("ECOTECH_FERNET_KEY_FILE")

    if ruta_configurada:
        archivo_clave = Path(ruta_configurada)
    else:
        archivo_clave = carpeta_proyecto / "clave_fernet.key"

    if contar_cuentas(conexion) > 0 and not archivo_clave.exists():
        raise ValueError(
            "Falta clave_fernet.key. Restaure la clave original."
        )

    return ServicioCifrado(archivo_clave)


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