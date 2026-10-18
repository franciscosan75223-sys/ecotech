from pathlib import Path
import os

from dotenv import load_dotenv
from psycopg import (
    IntegrityError, DataError, OperationalError, InterfaceError, ProgrammingError
)

from infraestructura.conexion import conectar_supabase, verificar_tablas
from infraestructura.repositorio import contar_cuentas
from infraestructura.seguridad import ServicioCifrado
from presentacion.entradas import pedir_configuracion_conexion
from presentacion.errores import mostrar_error_supabase
from presentacion.menu import menu


def iniciar_programa():
    conexion = None
    carpeta_proyecto = Path(__file__).resolve().parent.parent
    try:
        load_dotenv(carpeta_proyecto / ".env")
        print("ECOTECH - SUPABASE (POSTGRESQL)")
        configuracion = pedir_configuracion_conexion()
        conexion = conectar_supabase(*configuracion)
        verificar_tablas(conexion)

        archivo_clave = Path(
            os.getenv("ECOTECH_FERNET_KEY_FILE")
            or (carpeta_proyecto / "clave_fernet.key")
        )
        if contar_cuentas(conexion) > 0 and not archivo_clave.exists():
            raise ValueError("Falta clave_fernet.key. Restaure la clave original.")
        servicio = ServicioCifrado(archivo_clave)

        print("Conexion a Supabase lista.")
        menu(conexion, servicio)
    except ConnectionError as error:
        print("Error de conexion:", error)
    except (IntegrityError, DataError, OperationalError, InterfaceError, ProgrammingError) as error:
        try:
            mostrar_error_supabase(error, conexion)
        except ConnectionError as error_conexion:
            print("Error de conexion:", error_conexion)
    except PermissionError as error:
        print("No se pudo acceder al servicio o al archivo:", error)
    except FileNotFoundError as error:
        print("No se encontro un archivo necesario:", error)
    except (OSError, ValueError) as error:
        print("No se pudo iniciar o completar el programa:", error)
    except (KeyboardInterrupt, EOFError):
        print("\nPrograma finalizado.")
    finally:
        if conexion is not None:
            conexion.close()

