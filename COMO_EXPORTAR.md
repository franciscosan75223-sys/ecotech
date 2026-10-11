# Crear Excel y PDF con Informes

Las exportaciones son métodos de `Informes`, dentro de `main.py`. No hay que crear objetos de clases PDF o Excel.

## Probar ahora, sin Supabase

En la terminal de VS Code:

```powershell
cd C:\Users\franc\Downloads\ecotech
.\.venv\Scripts\python.exe ejemplo_informes.py
```

El ejemplo usa datos ficticios y genera los dos archivos en `C:\Users\franc\Downloads\ecotech\reportes`. No guarda empleados de prueba en la base. Abre esa carpeta y haz doble clic en el archivo que quieras ver. El Excel requiere Excel, LibreOffice u otro visor compatible.

## Exportar los registros guardados en Supabase

```powershell
.\.venv\Scripts\python.exe main.py
```

Ingresa la contraseña de la base cuando la pida. Luego elige:

- **16:** guardar informe en Excel (`.xlsx`).
- **17:** guardar informe en PDF (`.pdf`).

El programa muestra la ruta del archivo. Los nombres incluyen fecha y hora para conservar los informes anteriores. Si no hay datos, el archivo indica `Sin registros`.

## Entender el código paso a paso

1. `Informes(...)` recibe los datos que se van a mostrar. Admite tu ejemplo con un Tiempo o las listas del informe general.
2. `obtener_secciones()` organiza los datos en encabezados y filas. Se llama desde ambas exportaciones para que usen la misma información.
3. `preparar_ruta()` crea la carpeta reportes si no existe y prepara el nombre del archivo.
4. `exportar_excel()` crea un libro, añade una hoja por sección, escribe sus filas y lo guarda. La biblioteca `openpyxl` se ocupa del formato Excel.
5. `exportar_pdf()` convierte los datos en párrafos y los guarda en un documento. La biblioteca `reportlab` distribuye el contenido en páginas.
6. Ambos métodos usan `return ruta` para que el menú pueda indicar dónde se guardó el archivo.

Con un informe ya creado, las llamadas son:

```python
informe.exportar_excel()
informe.exportar_pdf()
```

El informe general contiene empleados, proyectos, departamentos y tiempo. Conserva los IDs además de los nombres para distinguir registros. El total de horas se calcula una sola vez con todos los registros. Es una copia de los datos al exportar; si cambian en Supabase, genera otro informe.

En el UML, agrega `exportar_excel()` y `exportar_pdf()` a Informes y retira las clases independientes PDF y Excel.

## Dependencias y pruebas

En este equipo ya se instalaron las bibliotecas. En otro equipo:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Para ejecutar todas las pruebas:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest -v test_ecotech test_exportaciones
```

La carpeta `reportes` queda excluida de GitHub. Las exportaciones no incluyen contraseñas ni claves.

Referencias: [guardar libros con openpyxl](https://openpyxl.readthedocs.io/en/stable/tutorial.html#saving-to-a-file) y [párrafos de ReportLab](https://docs.reportlab.com/reportlab/userguide/ch6_paragraphs/).
