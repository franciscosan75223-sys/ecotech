# EcoTech: gestión de empleados y proyectos

Aplicación de consola en Python con PostgreSQL/Supabase. Permite administrar empleados, cuentas, proyectos, departamentos, asignaciones y horas, consultar el historial y exportar informes a Excel y PDF.

## Instalación en Windows

Requiere Python 3.10 o posterior. Extrae `ecotech_listo.zip` en una carpeta nueva y abre esa carpeta en Visual Studio Code. El ZIP contiene directamente `main.py`, `requirements.txt`, `supabase-ca.crt` y las carpetas del proyecto, sin una carpeta contenedora adicional. Crea el entorno virtual desde esa misma carpeta. Desde una terminal situada en esa carpeta ejecuta:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

En Visual Studio Code, usa **Python: Select Interpreter** y selecciona `.venv\Scripts\python.exe`. Así el editor y el programa utilizan las mismas librerías.

Hay un único archivo de dependencias: `requirements.txt`.

| Librería | Uso en la aplicación |
| --- | --- |
| `psycopg[binary]` | Conexión, consultas y transacciones PostgreSQL. |
| `python-dotenv` | Lectura de la configuración de `.env`. |
| `cryptography` | Cifrado Fernet y derivación de contraseñas con Argon2id. |
| `openpyxl` | Exportación a Excel. |
| `reportlab` | Exportación a PDF. |

Las dependencias indirectas se instalan automáticamente. No se incluyen archivos de pruebas, el ejemplo de informes ni un archivo adicional de requisitos de desarrollo.

## Configuración y ejecución

1. Copia `.env.example` como `.env` y completa servidor, usuario, puerto y nombre de base con los datos de **Connect > Session pooler** de Supabase. La contraseña solicitada es la de PostgreSQL, no la de tu cuenta del sitio de Supabase.
2. Puedes dejar `SUPABASE_DB_PASSWORD` vacío para escribirla al iniciar. En Windows se muestran asteriscos; en otros sistemas se utiliza la entrada oculta de `getpass`.
3. Si ya usabas el proyecto, conserva tu `.env` y **la misma `clave_fernet.key`**. También puedes indicar la ruta de esa clave en `ECOTECH_FERNET_KEY_FILE`. Si existen cuentas y falta la clave, ofrece una recuperacion con confirmacion expresa, explicada mas abajo.
4. Para una base nueva, ejecuta `ecotech_supabase.sql` en el editor SQL de Supabase. Si ya tienes las tablas y los datos funcionando, conserva esa base; estos cambios no requieren volver a ejecutar el SQL.
5. Inicia el programa:

```powershell
.\.venv\Scripts\python.exe main.py
```

Si el servidor rechaza las credenciales, el programa permite volver a escribir la contraseña. Los errores de certificado o red se convierten en `ConnectionError` dentro de `infraestructura/conexion.py`; `presentacion/inicio.py` muestra un mensaje breve y finaliza para que puedas corregir la configuración. La causa original se conserva internamente, sin imprimir detalles técnicos en la consola.

La conexión utiliza `sslmode="verify-full"`, comprueba el nombre del servidor y requiere como mínimo TLS 1.2. Se incluye **`supabase-ca.crt`**, el certificado raíz público de Supabase, junto a `main.py`. Se carga automáticamente desde la carpeta del proyecto, aunque ejecutes el programa desde otra ubicación. Deja `SUPABASE_SSLROOTCERT=` vacío para utilizarlo. Este certificado público se puede distribuir junto al código; no contiene una clave privada.

Si necesitas utilizar otro certificado descargado de la configuración de tu proyecto Supabase, indica su ruta en `SUPABASE_SSLROOTCERT`. Las rutas relativas se resuelven desde la carpeta de `main.py`. Una ruta configurada tiene prioridad: si apunta a un archivo inexistente, corrígela o déjala vacía para volver al certificado incluido.

El certificado se descargó por HTTPS desde [el enlace de distribución de Supabase](https://supabase-downloads.s3-ap-southeast-1.amazonaws.com/prod/ssl/prod-ca-2021.crt), utilizado por [el código oficial de su panel](https://github.com/supabase/supabase/blob/master/apps/studio/hooks/custom-content/custom-content.json). Emisor: Supabase Root 2021 CA; vence el 26 de abril de 2031. Huella SHA-256: `807025ad50d4ed219d2c9c7d299c004f824eb00cf7f65afef607d07b72e6cafa`. Se comprobó su firma y que permite cargar un almacén de confianza con verificación obligatoria. Si Supabase cambia la autoridad de tu servidor, obtén el certificado correspondiente desde su panel. Referencia: [conexiones SSL de Supabase](https://supabase.com/docs/guides/database/connecting-to-postgres#connecting-with-ssl).

## Organización

| Archivo o carpeta | Responsabilidad |
| --- | --- |
| `main.py` | Punto de entrada: llama a `iniciar_programa()`. |
| `dominio/` | Las clases `Persona`, `Empleado`, `CuentaUsuario`, `Proyecto`, `Departamento`, `Asignacion`, `Tiempo`, `Informes` y `ServicioCifrado`. |
| `dominio/__init__.py` | Exporta las clases para facilitar sus importaciones. |
| `validaciones.py` | Reglas compartidas por clases, formularios y repositorio. |
| `infraestructura/conexion.py` | Configuración de entidades, carga del certificado, conexión y verificación de tablas. |
| `supabase-ca.crt` | Certificado raíz público de Supabase utilizado para verificar el servidor. |
| `infraestructura/repositorio.py` | CRUD, relaciones, historial y `RegistroNoEncontradoError`. |
| `presentacion/inicio.py` | Inicio, reintentos, preparación del cifrado y cierre de la conexión. |
| `presentacion/menu.py` | Menús y funciones que ejecutan cada opción. |
| `presentacion/entradas.py` | Ingreso, validación y corrección de datos. |
| `presentacion/errores.py` | Traducción de errores conocidos a mensajes de consola. |

El menú queda en presentación y `main.py` solo inicia la aplicación. Las validaciones están en un archivo en la raíz; no hay una carpeta `comun`. La excepción del repositorio se define en ese mismo archivo para evitar un módulo separado con una sola clase.

## Transacciones y excepciones

- **Actualizar y eliminar:** `commit()` confirma conjuntamente el cambio y su historial. Ante los errores contemplados se ejecuta `rollback()` en `except`; `finally` cierra el cursor. Sumar horas también es una actualización y sigue ese tratamiento.
- **Insertar:** `with conexion.transaction()` confirma al finalizar o revierte si ocurre una excepción, sin llamadas manuales a commit o rollback.
- **Consultar:** no llama manualmente a commit ni rollback.

`rollback()` revierte una transacción que todavía no se confirmó. Una actualización exitosa ya confirmada no se deshace al salir del menú; el historial permite consultar lo que cambió. No se utiliza `except: pass`.

Las acciones del menú y de los informes se dividieron en funciones pequeñas. Se centralizaron mensajes repetidos, el cálculo del total de horas y la preparación de las secciones de informes. Se retiraron variables e importaciones sin uso.

## Contraseñas y archivos

Las contraseñas de cuentas nuevas o modificadas se procesan con Argon2id, con sal aleatoria de 16 bytes, 64 MiB de memoria, tres iteraciones y cuatro vías. El resultado se cifra con Fernet para conservar el formato de almacenamiento existente. La verificación de las cuentas antiguas sigue admitida con su clave original; no se migran ni modifican automáticamente los registros ya guardados.

La clave nueva y los informes nuevos se crean sin sobrescribir archivos existentes y con permisos de propietario en sistemas POSIX. En Windows el acceso depende también de los permisos de la carpeta. Protege tanto la clave como el archivo `.env` y los informes, que contienen datos personales. `.gitignore` excluye esos archivos locales del repositorio.

El menú conserva el alcance administrativo del proyecto: la comprobación de contraseña de una cuenta no crea una sesión ni restringe cada operación por rol. La conexión utiliza los permisos del usuario PostgreSQL configurado. Antes de utilizar datos reales en un entorno compartido, se necesita definir y probar la autorización de usuarios y los permisos de ese usuario de base de datos.

## Recuperación cuando se perdió la clave Fernet

Si ya no tienes `clave_fernet.key`, las contraseñas cifradas con esa clave no se pueden recuperar. La contraseña de conexión a PostgreSQL/Supabase es independiente y se conserva.

1. Inicia el programa y conéctate normalmente a Supabase.
2. Si hay cuentas y falta la clave local, aparecerá la explicación de recuperación. Escribe exactamente **`CREAR NUEVA CLAVE`** para crear una clave; Enter u otra respuesta cancela el inicio sin crearla.
3. Guarda una copia privada del nuevo archivo `clave_fernet.key`.
4. En el menú, usa **7. Consultar cuentas de usuario** y anota el ID del empleado y el nombre de usuario de cada cuenta.
5. Usa **5. Actualizar cuenta de usuario**. Ingresa el **ID del empleado**, conserva el nombre de usuario si deseas mantenerlo y establece una contraseña nueva. Repite el proceso para cada cuenta que necesites utilizar.
6. Comprueba la contraseña nueva con **6. Comprobar acceso**.

Crear la clave solo escribe el archivo local: no cambia automáticamente las contraseñas ni otros registros de Supabase. Las cuentas pendientes de restablecer conservan sus tokens anteriores, que no se pueden verificar con la clave nueva. Cada actualización confirmada por la opción 5 guarda la nueva contraseña y registra el cambio en el historial mediante el CRUD existente. Los empleados, proyectos, departamentos, horas y sus relaciones se conservan.

La recuperación está destinada al administrador que ya dispone de las credenciales PostgreSQL y sus permisos de actualización. Mantén privada la clave y conserva su misma copia al utilizar el proyecto en otro equipo. Una clave existente, incluso si es inválida, no se sobrescribe automáticamente.

## Informes

Desde el menú: opción **15** para mostrar el informe, **16** para Excel y **17** para PDF. Se guardan en `reportes/`, dentro de la carpeta del proyecto. Las exportaciones no incluyen contraseñas ni claves; los textos de Excel se guardan como texto para evitar interpretarlos como fórmulas y el contenido PDF se escapa antes de formatearlo.

Las instrucciones completas están en [COMO_EXPORTAR.md](COMO_EXPORTAR.md).

## Comprobaciones de esta entrega

Revisión local realizada el **22 de octubre de 2026**, sobre los 18 archivos Python de la aplicación:

| Comprobación | Resultado |
| --- | --- |
| SonarQube para IDE / SonarLint Language Server 6.1.0.79799, analizador Python 5.21.0.32726 | 18 archivos analizados, cero avisos con las reglas activas predeterminadas. |
| Bandit 1.9.4, sin exclusiones ni supresiones de hallazgos | Cero hallazgos y cero errores de análisis. |
| pip-audit 2.10.1, sobre `requirements.txt` y sus dependencias resueltas | Cero vulnerabilidades conocidas detectadas. |
| Pyflakes | Sin importaciones o variables sin uso detectadas. |
| Comprobaciones privadas de funcionamiento | 51 pruebas correctas: clases, cifrado, transacciones simuladas, archivos Excel/PDF reales, certificado incluido, rutas independientes del directorio de ejecución y mensajes sin causa técnica y recuperación confirmada de la clave perdida. |
| Comparación del menú anterior y el refactorizado | 82 escenarios con los mismos mensajes, llamadas y errores. |

Los resultados de los tres analizadores están en `auditoria/`; son informes, no dependencias de ejecución. Las pruebas utilizadas para la revisión quedan fuera de la entrega, como se solicitó.

Se usó el motor oficial local de SonarQube para IDE; no se ejecutó un análisis conectado a SonarQube Server ni un perfil personalizado de tu institución. No se logró probar la conexión remota desde este entorno: la consulta DNS del servidor devolvió un error de resolución. No se completó una conexión autenticada ni se modificaron datos reales. Estas comprobaciones no garantizan la ausencia total de vulnerabilidades; las dependencias y los avisos publicados pueden cambiar después de esta fecha.
