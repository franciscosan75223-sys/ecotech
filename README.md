# EcoTech — POO con Supabase

El programa reúne el avance del equipo y las clases Tiempo e Informes en `main.py`, con el mismo orden del archivo de tus compañeros: validaciones, clases, funciones de base de datos, ingreso de datos y menú. Las clases siguen separadas aunque estén en el mismo archivo.

## Qué cambió

- Se reemplazó la conexión MySQL por PostgreSQL de Supabase usando `psycopg`.
- Se conservaron las clases y las operaciones del equipo. Los comentarios `CAMBIO SUPABASE` identifican las adaptaciones.
- La opción **14** usa tu clase Tiempo y guarda sus datos en la tabla `asignacion`, que ya tenía el equipo. No crea una segunda copia de las horas.
- La opción **15** consulta empleados, proyectos, departamentos y registros de tiempo guardados, y muestra un informe en la consola.
- Los datos de conexión se leen de `.env`. La contraseña también puede ingresarse al iniciar el programa, sin guardarla en ese archivo.

Las clases del programa están en `main.py`. Los antiguos archivos de clases separados ya no son necesarios para ejecutar esta versión.

## Preparar Supabase una vez

1. Crear el proyecto **EcoTech** y guardar la contraseña de su base de datos.
2. En **SQL Editor**, pegar y ejecutar todo `ecotech_supabase.sql`. La consulta final debe mostrar seis tablas con `seguridad_activa = true`.
3. Abrir **Connect**, elegir **Session pooler** y copiar el servidor (host), el puerto y el usuario. Normalmente el usuario tiene la forma `postgres.ID_DEL_PROYECTO`. Usar los valores del panel, sin inventarlos.
4. Copiar `.env.example` con el nombre `.env`. Completar `SUPABASE_DB_HOST` y `SUPABASE_DB_USER`. El puerto del Session pooler suele ser `5432` y la base se llama `postgres`.
5. Dejar `SUPABASE_DB_PASSWORD` vacío si se prefiere escribir la contraseña cada vez que se abre el programa.

La conexión de este programa usa PostgreSQL directamente con SSL; no utiliza una clave `anon` ni `service_role`. Las tablas están en el esquema privado `ecotech` y no se exponen mediante la API pública. No es necesario habilitar ese esquema en Data API.

## Instalar y ejecutar

Abrir una terminal en la carpeta de este repositorio. Requiere Python 3.10 o posterior.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Ejecutar `main.py`, no los archivos de prueba de `dominio`. Si VS Code usa otro Python, seleccionar el intérprete `.venv\Scripts\python.exe` de este proyecto.

## Recorrido para entender tu parte

1. Registrar un empleado y su cuenta con la opción 1.
2. Crear un proyecto en la opción 11. Para un departamento, primero registrar un empleado con rol Gerente y usar la opción 12.
3. Elegir la opción 14: seleccionar los IDs del empleado y proyecto, escribir fecha, horas y descripción.
4. `Tiempo(...)` reúne esos datos en un objeto. `guardar_tiempo(...)` los entrega a la función que ya usaba el equipo para guardar asignaciones.
5. La opción 15 lee las filas guardadas y crea objetos Tiempo para mostrarlos mediante Informes.

El avance original permite asignaciones con cero horas, mientras que la opción 14 exige horas mayores que cero. Se conserva ese comportamiento del equipo. Ambos menús trabajan sobre los mismos registros.

## Guardar Excel y PDF en tu computador

Las exportaciones son métodos de `Informes`: `exportar_excel()` y `exportar_pdf()`. Se retiraron las clases separadas Excel y PDF de `main.py`.

- Opción **16**: exportar todos los datos consultados a un Excel con cuatro hojas.
- Opción **17**: exportar esos datos a un PDF con secciones y páginas automáticas.
- Los archivos se guardan en `reportes`, dentro del proyecto. El nombre incluye fecha y hora para conservar los anteriores.
- Para probar sin conectarte a Supabase, ejecuta `.\.venv\Scripts\python.exe ejemplo_informes.py`. Usa datos ficticios y crea ambos archivos.

La explicación paso a paso está en [COMO_EXPORTAR.md](COMO_EXPORTAR.md). Las bibliotecas se instalaron en `.venv` y figuran en `requirements.txt` para otros equipos.

## Qué sigue pendiente en el trabajo

- **Empleado por departamento:** el modelo del equipo relaciona el departamento con su gerente, pero no asigna cada empleado a un departamento. Por eso los informes no inventan ese dato.
- **Autorización de usuarios:** se conserva la comprobación de cuentas del equipo, pero el menú no restringe sus opciones según una sesión o rol. Este avance es una consola administrativa de clase, no una aplicación lista para entregar a empleados.
- **Contraseñas y datos personales:** se conserva Fernet para las contraseñas del avance original. Supabase no convierte eso en Auth ni cifra automáticamente cada campo personal del modelo. Si se completa el requisito de autenticación, conviene usar Supabase Auth o hashes adecuados y autorización por rol.
- Este archivo SQL prepara un proyecto nuevo. **No importa registros de una base MySQL existente.**

## Archivos que no se suben a GitHub

`.env`, `clave_fernet.key` y `.venv` están excluidos por `.gitignore`. La clave Fernet se crea al iniciar una base sin cuentas. Conservarla: si ya existen cuentas cifradas, hace falta la misma clave para comprobarlas. Para usar una clave existente, completar `ECOTECH_FERNET_KEY_FILE` con su ruta local. No compartir esa clave en el repositorio.

Se dejó una copia del código anterior en el espacio de trabajo de esta conversación. No se realizó ningún commit ni push.

Referencia de conexión: [documentación oficial de Supabase](https://supabase.com/docs/guides/database/connecting-to-postgres).

## Comprobaciones realizadas

Las siete pruebas locales de `test_ecotech.py` pasan. Se ejecutaron también pruebas SQL en el proyecto EcoTech: creación de IDs, relaciones entre tablas, suma de horas, historial, rechazo de valores inválidos y reversión de cambios. Los datos ficticios se revirtieron; la base quedó vacía.

El asesor de Supabase puede informar `RLS Enabled No Policy`: es intencional en este diseño, ya que la consola administrativa usa una conexión PostgreSQL y no concede acceso a las tablas desde la API. Los avisos de índices sin uso son normales en una base nueva. Se retiró el permiso público sobre la función de RLS automático creada por Supabase.

La conexión completa desde Python queda pendiente de que ingreses tu contraseña al iniciar. Se dejó la contraseña vacía por tu preferencia; no se comprobó usando credenciales inventadas.

```powershell
.\.venv\Scripts\python.exe -m unittest -v test_ecotech
```

Las exportaciones se comprobaron reabriendo los archivos, revisando sus datos y páginas, y probando el menú. Para repetir todas las pruebas: instalar `requirements-dev.txt` y ejecutar `python -m unittest -v test_ecotech test_exportaciones`.
