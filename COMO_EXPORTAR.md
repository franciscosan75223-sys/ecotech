# Exportar informes de EcoTech

## Preparación

Instala las librerías desde el único archivo `requirements.txt` y configura la conexión siguiendo [README.md](README.md). Desde la raíz del proyecto ejecuta:

```powershell
.\.venv\Scripts\python.exe main.py
```

Conéctate a tu base de Supabase y selecciona una opción:

| Opción | Resultado |
| --- | --- |
| 15 | Muestra el informe general en la consola. |
| 16 | Guarda un archivo Excel con cuatro hojas. |
| 17 | Guarda un archivo PDF con las mismas secciones. |

Excel y PDF contienen Empleados, Proyectos, Departamentos y Tiempo, incluido el total de horas. Si una sección está vacía, aparece «Sin registros». El informe muestra los datos actuales de la base; no incluye contraseñas ni claves.

## Dónde quedan los archivos

Se crea la carpeta `reportes/` dentro de la carpeta del proyecto. El menú muestra la ruta del archivo generado. Cada nombre contiene fecha y hora, por ejemplo `informe_ecotech_2026-10-22_18-30-00_123456.xlsx`.

Los archivos anteriores se conservan. Si no tienes permiso para escribir en la carpeta o un archivo está bloqueado, el programa informa del error. Comprueba que la carpeta del proyecto permita escritura. Los informes contienen datos personales: compártelos solo con las personas autorizadas.

## Código que realiza la exportación

La clase `Informes` está en `dominio/informe.py`. `crear_informe_desde_supabase()` en `presentacion/menu.py` carga los datos y construye el objeto utilizado por las tres opciones.

1. `obtener_secciones()` prepara encabezados y filas.
2. `calcular_total_horas()` calcula el total compartido por consola, Excel y PDF.
3. `generar_informes()` muestra las secciones en consola.
4. `exportar_excel()` usa `openpyxl` y `exportar_pdf()` usa `reportlab`; ambas devuelven la ruta del archivo.

Para utilizar la clase desde código con listas de objetos ya cargadas:

```python
from dominio.informe import Informes

informe = Informes(empleados, proyectos, departamentos, asignaciones)
ruta_excel = informe.exportar_excel()
ruta_pdf = informe.exportar_pdf()
```

Puedes indicar otra carpeta con `informe.exportar_excel("mis_reportes")` o `informe.exportar_pdf("mis_reportes")`. Sin ese argumento se utiliza `reportes/`.

La entrega no incluye un programa de ejemplo ni archivos de pruebas. No necesitas instalar otras librerías para exportar además de las de `requirements.txt`.
