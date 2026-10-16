"""Ejemplo con datos ficticios. Crea archivos en tu PC sin usar Supabase."""
from dominio import Empleado, Proyecto, Departamento, Asignacion
from main import Informes


def crear_informe_ejemplo():
    empleado = Empleado(1, "José Muñoz", "Calle de ejemplo 123", "912345678",
                        "jose@example.com", "2026-01-01", 1250, "Gerente")
    proyecto = Proyecto(2, "Energía limpia", "Investigación & desarrollo",
                        "2026-01-01", "Equipo de prueba", 2000)
    departamento = Departamento(3, "Desarrollo", 1, "Sostenibilidad")
    registro_uno = Asignacion(1, "2026-01-10", 8, "Revisión de equipos y documentación.", 1, 2)
    registro_dos = Asignacion(2, "2026-01-11", 3, "Pruebas de los equipos y preparación del informe.", 1, 2)

    # Los corchetes forman listas: así un informe puede incluir varios registros.
    return Informes([empleado], [proyecto], [departamento], [registro_uno, registro_dos])


if __name__ == "__main__":
    informe = crear_informe_ejemplo()
    print("Excel creado en:", informe.exportar_excel())
    print("PDF creado en:", informe.exportar_pdf())
