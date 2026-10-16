# EcoTech: organización del avance del equipo, adaptada a Supabase.
# Orden: validaciones, clases, acceso a datos, entrada de datos, menú y main.
# Los comentarios CAMBIO SUPABASE explican la adaptación de MySQL a PostgreSQL.
# EcoTech: organizacion del avance del equipo, adaptada a Supabase.
from datetime import datetime
from getpass import getpass
from pathlib import Path
import json
import os
import psycopg
from psycopg import Error
from psycopg.rows import dict_row
from dotenv import load_dotenv
from cryptography.fernet import Fernet, InvalidToken

# Importaciones de la capa de dominio
from dominio import Empleado, CuentaUsuario, Proyecto, Departamento, Asignacion, Tiempo
from dominio.validaciones import (
    validar_fecha, validar_horas_adicionales, validar_nombre_usuario, 
    validar_contrasena, validar_id, validar_rol
)

load_dotenv(Path(__file__).with_name('.env'))
SUPABASE_PUERTO = 5432
SUPABASE_BASE = 'postgres'

# A partir de aqui comienza la clase Informes y ServicioCifrado...


def validar_nombre(nombre, revisar_formato=False):
    if not nombre.strip() or len(nombre) > 100:
        raise ValueError("El nombre debe tener entre 1 y 100 caracteres.")
    nombre = nombre.strip()
    if revisar_formato:
        letras = nombre.replace(" ", "").replace("-", "")
        letras = letras.replace("'", "").replace("’", "")
        if not letras.isalpha():
            raise ValueError("El nombre debe contener letras; puede usar espacios, guiones y apóstrofes.")
    return nombre


def validar_direccion(direccion, revisar_formato=False):
    if not direccion.strip() or len(direccion) > 200:
        raise ValueError("La dirección debe tener entre 1 y 200 caracteres.")
    direccion = direccion.strip()
    if revisar_formato:
        for caracter in direccion:
            if not caracter.isalpha() and caracter not in "0123456789 ":
                raise ValueError("La dirección solo puede contener letras, números y espacios.")
    return direccion


def validar_telefono(telefono, revisar_formato=False):
    telefono = telefono.strip()
    if revisar_formato:
        if not telefono.startswith("+") or len(telefono) != 12:
            raise ValueError("El teléfono debe tener 12 caracteres en total: + al comienzo y 11 números después.")
        numeros = telefono[1:]
        if not numeros.isascii() or not numeros.isdecimal():
            raise ValueError("Después del + solo se permiten números del 0 al 9, sin espacios ni otros símbolos.")
    elif not telefono or len(telefono) > 20:
        raise ValueError("El teléfono debe tener entre 1 y 20 caracteres.")
    # Se devuelve texto: conserva el + y los ceros iniciales.
    return telefono


def validar_correo(correo, revisar_formato=False):
    correo = correo.strip()
    if "@" not in correo or len(correo) > 150:
        raise ValueError("Ingrese un correo válido, por ejemplo usuario@gmail.com, de hasta 150 caracteres.")
    if revisar_formato:
        if correo.count("@") != 1:
            raise ValueError("El correo debe tener una sola @, por ejemplo usuario@gmail.com.")
        usuario, dominio = correo.split("@")
        if not usuario:
            raise ValueError("Debe escribir un nombre antes de @gmail.com.")
        for caracter in correo:
            if caracter.isspace():
                raise ValueError("El correo no puede contener espacios, por ejemplo usuario@gmail.com.")
        if dominio != "gmail.com":
            raise ValueError("El correo debe terminar exactamente en @gmail.com, por ejemplo usuario@gmail.com.")
    return correo


def validar_fecha(fecha):
    try:
        texto = str(fecha)
        if len(texto) != 10 or texto[4] != "-" or texto[7] != "-":
            raise ValueError
        fecha = datetime.strptime(texto, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Ingrese una fecha válida con formato AAAA-MM-DD.")
    if fecha.year < 1000:
        raise ValueError("El proyecto admite fechas desde el año 1000.")
    return fecha


def validar_dinero(valor, nombre_campo):
    try:
        valor = Decimal(str(valor))
    except InvalidOperation:
        raise ValueError(nombre_campo + " debe ser un número.")
    if not valor.is_finite() or valor < 0 or valor > Decimal("9999999999.99"):
        raise ValueError(nombre_campo + " debe estar entre 0 y 9999999999.99.")
    if valor != valor.quantize(Decimal("0.01")):
        raise ValueError(nombre_campo + " puede tener hasta dos decimales.")
    return valor


def validar_salario(salario):
    return validar_dinero(salario, "El salario")


def validar_presupuesto(presupuesto):
    return validar_dinero(presupuesto, "El presupuesto")


def validar_rol(rol):
    rol = rol.strip().capitalize()
    if rol not in ("Empleado", "Gerente"):
        raise ValueError("El rol debe ser Empleado o Gerente.")
    return rol


def validar_texto(texto, limite, nombre_campo):
    texto = texto.strip()
    if not texto or len(texto) > limite:
        raise ValueError(nombre_campo + f" debe tener entre 1 y {limite} caracteres.")
    for caracter in texto:
        if not caracter.isprintable():
            raise ValueError(nombre_campo + " no admite saltos de línea ni caracteres de control.")
    return texto


def validar_nombre_entidad(nombre):
    return validar_texto(nombre, 100, "El nombre")


def validar_descripcion(descripcion):
    return validar_texto(descripcion, 255, "La descripción o tarea")


def validar_miembro(miembro):
    return validar_texto(miembro, 100, "El miembro")


def validar_departamento(departamento):
    return validar_texto(departamento, 100, "El departamento")


def validar_id(numero):
    try:
        numero = int(str(numero))
    except ValueError:
        raise ValueError("El ID debe ser un número entero.")
    if numero <= 0 or numero > 2147483647:
        raise ValueError("El ID debe estar entre 1 y 2147483647.")
    return numero


def validar_horas(horas):
    try:
        horas = int(str(horas))
    except ValueError:
        raise ValueError("Las horas deben ser un número entero.")
    if horas < 0 or horas > 2147483647:
        raise ValueError("Las horas deben estar entre 0 y 2147483647.")
    return horas


def validar_horas_adicionales(horas):
    horas = validar_horas(horas)
    if horas == 0:
        raise ValueError("Debe agregar al menos una hora.")
    return horas


def validar_nombre_usuario(nombre, revisar_formato=False):
    if not nombre.strip() or len(nombre) > 50:
        raise ValueError("El usuario debe tener entre 1 y 50 caracteres.")
    nombre = nombre.strip()
    if revisar_formato:
        for caracter in nombre:
            if not caracter.isalpha() and caracter not in "0123456789_":
                raise ValueError("El usuario solo puede contener letras, números y guion bajo (_).")
    return nombre


def validar_contrasena(contrasena):
    # Conserva el texto y rechaza los símbolos que no permite el proyecto.
    if len(contrasena) < 8 or len(contrasena) > 128:
        raise ValueError("La contraseña debe tener entre 8 y 128 caracteres.")
    prohibidos = "\"'()/\\[]{}“”‘’«»"
    for caracter in contrasena:
        if caracter in prohibidos:
            raise ValueError("La contraseña no admite comillas, paréntesis, barras (/ o \\), corchetes ni llaves.")
    return contrasena


class Persona(ABC):
    def __init__(self, nombre, direccion, telefono, correo):
        self.actualizar_datos(nombre, direccion, telefono, correo)

    def actualizar_datos(self, nombre, direccion, telefono, correo):
        nombre = validar_nombre(nombre)
        direccion = validar_direccion(direccion)
        telefono = validar_telefono(telefono)
        correo = validar_correo(correo)
        self._nombre = nombre
        self._direccion = direccion
        self._telefono = telefono
        self._correo = correo

    def get_nombre(self):
        return self._nombre

    def get_direccion(self):
        return self._direccion

    def get_telefono(self):
        return self._telefono

    def get_correo(self):
        return self._correo

    @abstractmethod
    def mostrar_datos(self):
        pass

    def __str__(self):
        return self.mostrar_datos()


class Empleado(Persona):
    def __init__(self, id_empleado, nombre, direccion, telefono,
                 correo, fecha_inicio, salario, rol="Empleado"):
        super().__init__(nombre, direccion, telefono, correo)
        self._id_empleado = id_empleado
        self._fecha_inicio = validar_fecha(fecha_inicio)
        self.set_salario(salario)
        self._rol = validar_rol(rol)
        self.__cuenta_usuario = None

    def get_id(self):
        return self._id_empleado

    def get_fecha_inicio(self):
        return self._fecha_inicio

    def get_rol(self):
        return self._rol

    def get_salario(self):
        return self.__salario

    def set_salario(self, salario):
        self.__salario = validar_salario(salario)

    def asignar_cuenta(self, cuenta):
        if not isinstance(cuenta, CuentaUsuario):
            raise ValueError("Debe asignarse una CuentaUsuario.")
        if cuenta.get_correo() != self.get_correo():
            raise ValueError("La cuenta debe usar el correo del empleado.")
        self.__cuenta_usuario = cuenta

    def get_cuenta_usuario(self):
        return self.__cuenta_usuario

    def mostrar_datos(self):
        return (
            f"ID: {self._id_empleado} | Nombre: {self._nombre} | "
            f"Dirección: {self._direccion} | Teléfono: {self._telefono} | "
            f"Correo: {self._correo} | Inicio: {self._fecha_inicio} | "
            f"Salario: {self.__salario:.2f} | Rol: {self._rol}"
        )


class CuentaUsuario:
    def __init__(self, nombre, correo, servicio, contrasena=None):
        self._nombre = validar_nombre_usuario(nombre)
        self._correo = validar_correo(correo)
        self.__servicio = servicio
        self.__contrasena_cifrada = None
        if contrasena is not None:
            self.set_contrasena(contrasena)

    def get_nombre(self):
        return self._nombre

    def get_correo(self):
        return self._correo

    def set_contrasena(self, contrasena):
        contrasena = validar_contrasena(contrasena)
        self.__contrasena_cifrada = self.__servicio.cifrar(contrasena)

    def get_contrasena_cifrada(self):
        if self.__contrasena_cifrada is None:
            raise ValueError("La cuenta todavía no tiene contraseña.")
        return self.__contrasena_cifrada

    def cargar_contrasena_cifrada(self, token):
        # Recupera el contenido que ya estaba cifrado en Supabase.
        self.__contrasena_cifrada = bytes(token)

    def acceso_cuenta(self, nombre, contrasena):
        if nombre != self._nombre:
            return False
        return self.__servicio.validacion_cifrado(
            contrasena, self.get_contrasena_cifrada()
        )

    def __str__(self):
        return f"Usuario: {self._nombre} | Correo: {self._correo}"


class ServicioCifrado:
    def __init__(self, archivo_clave):
        archivo = Path(archivo_clave)
        if archivo.exists():
            clave = archivo.read_bytes()
        else:
            clave = Fernet.generate_key()
            # xb crea el archivo sin sobrescribir una clave existente.
            with archivo.open("xb") as salida:
                salida.write(clave)
        self.__cifrador = Fernet(clave)

    def cifrar(self, texto):
        return self.__cifrador.encrypt(texto.encode())

    def descifrar(self, token):
        return self.__cifrador.decrypt(token).decode()

    def validacion_cifrado(self, ingresada, token):
        try:
            return ingresada == self.descifrar(token)
        except InvalidToken:
            return False

    def __str__(self):
        return "Servicio de cifrado Fernet"


class Proyecto:
    def __init__(self, id_proyecto, nombre, descripcion_proyecto,
                 fecha_de_inicio, miembro, presupuesto):
        self._id_proyecto = id_proyecto
        self._nombre = validar_nombre_entidad(nombre)
        self._descripcion_proyecto = validar_descripcion(descripcion_proyecto)
        self._fecha_de_inicio = validar_fecha(fecha_de_inicio)
        self._miembro = validar_miembro(miembro)
        self.__presupuesto = validar_presupuesto(presupuesto)

    def get_id(self):
        return self._id_proyecto

    def get_nombre(self):
        return self._nombre

    def get_descripcion_proyecto(self):
        return self._descripcion_proyecto

    def get_fecha_de_inicio(self):
        return self._fecha_de_inicio

    def get_miembro(self):
        return self._miembro

    def get_presupuesto(self):
        return self.__presupuesto

    def get_datos(self):
        return {"nombre": self._nombre, "descripcion_proyecto": self._descripcion_proyecto,
                "fecha_de_inicio": self._fecha_de_inicio, "miembro": self._miembro,
                "presupuesto": self.__presupuesto}

    def mostrar_datos(self):
        return (f"Proyecto {self._id_proyecto} | {self._nombre} | "
                f"Descripción: {self._descripcion_proyecto} | Inicio: {self._fecha_de_inicio} | "
                f"Miembro: {self._miembro} | Presupuesto: {self.__presupuesto:.2f}")

    def __str__(self):
        return self.mostrar_datos()


class Departamento:
    def __init__(self, id_departamento, nombre, gerente_id, departamento):
        self._id_departamento = id_departamento
        self._nombre = validar_nombre_entidad(nombre)
        self._gerente_id = validar_id(gerente_id)
        self._departamento = validar_departamento(departamento)

    def get_id(self):
        return self._id_departamento

    def get_nombre(self):
        return self._nombre

    def get_gerente_id(self):
        return self._gerente_id

    def get_departamento(self):
        return self._departamento

    def get_datos(self):
        return {"nombre": self._nombre, "departamento": self._departamento,
                "gerente_id": self._gerente_id}

    def mostrar_datos(self):
        return (f"Departamento {self._id_departamento} | {self._nombre} | "
                f"Descripción: {self._departamento} | ID del gerente: {self._gerente_id}")

    def __str__(self):
        return self.mostrar_datos()


class Asignacion:
    def __init__(self, id_asignacion, fecha, horas_trabajadas, tareas_realizadas,
                 id_empleado=None, id_proyecto=None):
        self._id_asignacion = id_asignacion
        self._fecha = validar_fecha(fecha)
        self.__horas_trabajadas = validar_horas(horas_trabajadas)
        self._tareas_realizadas = validar_descripcion(tareas_realizadas)
        # None permite consultar filas antiguas que aún no se han vinculado.
        self._id_empleado = validar_id(id_empleado) if id_empleado is not None else None
        self._id_proyecto = validar_id(id_proyecto) if id_proyecto is not None else None

    def get_id(self):
        return self._id_asignacion

    def get_fecha(self):
        return self._fecha

    def get_horas_trabajadas(self):
        return self.__horas_trabajadas

    def get_tareas_realizadas(self):
        return self._tareas_realizadas

    def get_id_empleado(self):
        return self._id_empleado

    def get_id_proyecto(self):
        return self._id_proyecto

    def sumar_horas(self, horas):
        horas = validar_horas_adicionales(horas)
        self.__horas_trabajadas = validar_horas(self.__horas_trabajadas + horas)

    def get_datos(self):
        return {"fecha": self._fecha, "horas_trabajadas": self.__horas_trabajadas,
                "tareas_realizadas": self._tareas_realizadas,
                "id_empleado": self._id_empleado, "id_proyecto": self._id_proyecto}

    def mostrar_datos(self):
        empleado = self._id_empleado if self._id_empleado is not None else "sin vincular"
        proyecto = self._id_proyecto if self._id_proyecto is not None else "sin vincular"
        return (f"Asignación {self._id_asignacion} | Fecha: {self._fecha} | "
                f"Empleado: {empleado} | Proyecto: {proyecto} | "
                f"Horas: {self.__horas_trabajadas} | Tareas: {self._tareas_realizadas}")

    def __str__(self):
        return self.mostrar_datos()


# CAMBIO INTEGRACIÓN: se incorporan las clases de tu parte al diseño del equipo.
# Tiempo e Informes siguen separados. Las horas se guardan en asignacion una sola vez.
class Tiempo:
    def __init__(self, fecha, horas_trabajadas, descripcion_de_tareas, empleado, proyecto,
                 mostrar_mensaje=True):
        self.fecha = fecha
        self._horas_trabajadas = 0
        self._descripcion_de_tareas = descripcion_de_tareas
        self.empleado = empleado
        self.proyecto = proyecto
        self.registro_horas(horas_trabajadas, mostrar_mensaje)

    def registro_horas(self, horas, mostrar_mensaje=True):
        if horas > 0:
            self._horas_trabajadas = horas
            if mostrar_mensaje:
                print("horas registradas correctamente")
        elif mostrar_mensaje:
            print("las horas deben ser mayores que cero")

    def mostrar_registro(self):
        print("registro de fecha", self.fecha)
        print("horas trabajadas", self._horas_trabajadas)
        print("descripcion de la tarea", self._descripcion_de_tareas)
        print("empleado", self.empleado)
        print("proyecto", self.proyecto)

    # Estos métodos permiten guardar los datos sin acceder directamente a atributos internos.
    def get_horas_trabajadas(self):
        return self._horas_trabajadas

    def get_descripcion_de_tareas(self):
        return self._descripcion_de_tareas


class Informes:
    def __init__(self, empleados, proyecto, departamento, registro_de_tiempo):
        self.empleados = empleados
        self.proyecto = proyecto
        self.departamento = departamento
        self.registro_de_tiempo = registro_de_tiempo

    def generar_informes(self):
        if isinstance(self.registro_de_tiempo, list):
            for nombre, encabezados, filas in self.obtener_secciones():
                print("\n" + nombre)
                if not filas:
                    print("Sin registros")
                for fila in filas:
                    for encabezado, valor in zip(encabezados, fila):
                        print(encabezado + ":", valor)
                    print()
                if nombre == "Tiempo":
                    columna_horas = encabezados.index("Horas")
                    print("Total de horas:", sum(fila[columna_horas] for fila in filas))
            return
        print("informe de tiempo")
        print("departamento", self.departamento)
        self.registro_de_tiempo.mostrar_registro()

    # CAMBIO EXPORTACIÓN: estos métodos pertenecen a Informes.
    # No necesitamos crear clases PDF ni Excel.
    def obtener_secciones(self):
        """Prepara los mismos datos para los dos formatos de archivo."""
        if not isinstance(self.registro_de_tiempo, list):
            # Conservamos el ejemplo sencillo con un solo objeto Tiempo.
            tiempo = self.registro_de_tiempo
            return [("Tiempo", ["Fecha", "Empleado", "Proyecto", "Horas", "Tareas", "Departamento"], [
                [validar_fecha(str(tiempo.fecha)), tiempo.empleado, tiempo.proyecto,
                 tiempo.get_horas_trabajadas(), tiempo.get_descripcion_de_tareas(), self.departamento]
            ])]

        # El informe general recibe las listas consultadas en Supabase.
        empleados = []
        nombres_empleados = {}
        for empleado in self.empleados:
            nombres_empleados[empleado.get_id()] = empleado.get_nombre()
            empleados.append([
                empleado.get_id(), empleado.get_nombre(), empleado.get_direccion(),
                empleado.get_telefono(), empleado.get_correo(), empleado.get_fecha_inicio(),
                empleado.get_salario(), empleado.get_rol()
            ])

        proyectos = []
        nombres_proyectos = {}
        for proyecto in self.proyecto:
            nombres_proyectos[proyecto.get_id()] = proyecto.get_nombre()
            proyectos.append([
                proyecto.get_id(), proyecto.get_nombre(), proyecto.get_descripcion_proyecto(),
                proyecto.get_fecha_de_inicio(), proyecto.get_miembro(), proyecto.get_presupuesto()
            ])

        departamentos = []
        for departamento in self.departamento:
            departamentos.append([
                departamento.get_id(), departamento.get_nombre(), departamento.get_departamento(),
                departamento.get_gerente_id(),
                nombres_empleados.get(departamento.get_gerente_id(), "Sin vincular")
            ])

        tiempos = []
        for registro in self.registro_de_tiempo:
            tiempos.append([
                registro.get_id(), registro.get_fecha(), registro.get_id_empleado(),
                nombres_empleados.get(registro.get_id_empleado(), "Sin vincular"),
                registro.get_id_proyecto(),
                nombres_proyectos.get(registro.get_id_proyecto(), "Sin vincular"),
                registro.get_horas_trabajadas(), registro.get_tareas_realizadas()
            ])

        # Cada elemento contiene: nombre de sección, encabezados y filas.
        return [
            ("Empleados", ["ID", "Nombre", "Dirección", "Teléfono", "Correo", "Inicio de contrato", "Salario", "Rol"], empleados),
            ("Proyectos", ["ID", "Nombre", "Descripción", "Fecha de inicio", "Miembro", "Presupuesto"], proyectos),
            ("Departamentos", ["ID", "Nombre", "Descripción", "ID del gerente", "Gerente"], departamentos),
            ("Tiempo", ["ID", "Fecha", "ID empleado", "Empleado", "ID proyecto", "Proyecto", "Horas", "Tareas"], tiempos)
        ]

    def preparar_ruta(self, extension, carpeta=None):
        # Por defecto, los archivos quedan junto al programa, dentro de reportes.
        if carpeta is None:
            carpeta = Path(__file__).resolve().parent / "reportes"
        carpeta = Path(carpeta).resolve()
        carpeta.mkdir(parents=True, exist_ok=True)
        # La fecha y los microsegundos evitan reemplazar un informe anterior.
        momento = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
        return carpeta / f"informe_ecotech_{momento}.{extension}"

    def exportar_excel(self, carpeta=None):
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font, PatternFill
        from openpyxl.utils import get_column_letter
        from math import ceil

        ruta = self.preparar_ruta("xlsx", carpeta)
        libro = Workbook()
        libro.remove(libro.active)

        for nombre, encabezados, filas in self.obtener_secciones():
            hoja = libro.create_sheet(nombre)
            hoja.append(encabezados)
            for fila in filas:
                hoja.append(fila)

            # Un dato escrito por el usuario siempre se guarda como texto,
            # aunque empiece con =. Así Excel no lo ejecuta como una fórmula.
            for fila in hoja:
                for celda in fila:
                    if isinstance(celda.value, str):
                        celda.data_type = "s"
                    if celda.is_date:
                        celda.number_format = "yyyy-mm-dd"
                    celda.alignment = Alignment(vertical="top", wrap_text=True)

            for celda in hoja[1]:
                celda.font = Font(bold=True, color="FFFFFF")
                celda.fill = PatternFill("solid", fgColor="22624B")
            hoja.freeze_panes = "A2"
            hoja.auto_filter.ref = hoja.dimensions

            # Ajustamos las columnas y las filas para leer los textos completos.
            for numero, encabezado in enumerate(encabezados, start=1):
                ancho = max([len(encabezado)] + [len(str(f[numero - 1] or "")) for f in filas])
                hoja.column_dimensions[get_column_letter(numero)].width = min(max(ancho + 3, 16), 48)
                if encabezado in ("Salario", "Presupuesto"):
                    for fila in hoja.iter_rows(min_row=2, min_col=numero, max_col=numero):
                        fila[0].number_format = '#,##0.00'
            for fila in hoja:
                lineas = 1
                for celda in fila:
                    ancho = hoja.column_dimensions[celda.column_letter].width - 3
                    partes = str(celda.value or "").splitlines() or [""]
                    lineas = max(lineas, sum(max(1, ceil(len(parte) / ancho)) for parte in partes))
                hoja.row_dimensions[fila[0].row].height = 16 * lineas + 6

            if not filas:
                hoja.append(["Sin registros"])
            if nombre == "Tiempo":
                columna_horas = encabezados.index("Horas")
                total = sum(fila[columna_horas] for fila in filas)
                hoja.append([])
                hoja.append(["Total de horas", total])
                hoja.cell(hoja.max_row, 1).font = Font(bold=True)

        libro.save(ruta)
        return ruta

    def exportar_pdf(self, carpeta=None):
        from html import escape
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

        ruta = self.preparar_ruta("pdf", carpeta)
        estilos = getSampleStyleSheet()
        estilos["BodyText"].spaceAfter = 4
        contenido = [Paragraph("EcoTech - Informe", estilos["Title"])]
        contenido.append(Paragraph("Generado: " + datetime.now().strftime("%Y-%m-%d %H:%M"), estilos["Normal"]))
        contenido.append(Spacer(1, 16))

        # Paragraph ajusta el texto; SimpleDocTemplate añade las páginas necesarias.
        for numero_seccion, (nombre, encabezados, filas) in enumerate(self.obtener_secciones()):
            if numero_seccion > 0:
                contenido.append(PageBreak())
            contenido.append(Paragraph(nombre, estilos["Heading1"]))
            if not filas:
                contenido.append(Paragraph("Sin registros", estilos["BodyText"]))
            for numero_fila, fila in enumerate(filas, start=1):
                contenido.append(Paragraph(f"Registro {numero_fila}", estilos["Heading2"]))
                for encabezado, valor in zip(encabezados, fila):
                    if valor is None:
                        valor = "Sin vincular"
                    # escape permite imprimir &, < y > sin interpretarlos como etiquetas.
                    texto = escape(str(valor)).replace("\n", "<br/>")
                    contenido.append(Paragraph(f"<b>{escape(encabezado)}:</b> {texto}", estilos["BodyText"]))
                contenido.append(Spacer(1, 10))
            if nombre == "Tiempo":
                columna_horas = encabezados.index("Horas")
                total = sum(fila[columna_horas] for fila in filas)
                contenido.append(Paragraph(f"Total de horas: {total}", estilos["Heading2"]))

        documento = SimpleDocTemplate(str(ruta), pagesize=A4, title="Informe EcoTech",
                                      leftMargin=42, rightMargin=42, topMargin=42, bottomMargin=42)
        def poner_numero_pagina(lienzo, documento):
            # ReportLab llama esta función al terminar cada página.
            lienzo.saveState()
            lienzo.setFont("Helvetica", 9)
            lienzo.drawRightString(A4[0] - 42, 24, f"Página {documento.page}")
            lienzo.restoreState()

        documento.build(contenido, onFirstPage=poner_numero_pagina, onLaterPages=poner_numero_pagina)
        return ruta


# Solo estos nombres internos pueden convertirse en nombres de tabla o columna.
# Los valores ingresados por el usuario siempre se envían mediante %s.
CONFIGURACION_ENTIDADES = {
    "PROYECTO": ("proyecto", "id_proyecto", (
        "nombre", "descripcion_proyecto", "fecha_de_inicio", "miembro", "presupuesto")),
    "DEPARTAMENTO": ("departamento", "id_departamento", (
        "nombre", "departamento", "gerente_id")),
    "ASIGNACION": ("asignacion", "id_asignacion", (
        "fecha", "horas_trabajadas", "tareas_realizadas", "id_empleado", "id_proyecto"))
}


def conectar_supabase(usuario, contrasena, host, puerto=SUPABASE_PUERTO, base=SUPABASE_BASE):
    if not host or not usuario or not contrasena:
        raise ValueError("Complete el servidor, usuario y contraseña de la base de Supabase.")
    # Usamos el Session pooler de Supabase, que admite conexiones IPv4.
    # ecotech es el esquema de nuestras tablas; no usamos las tablas de Auth.
    return psycopg.connect(
        host=host, port=puerto, user=usuario, password=contrasena, dbname=base,
        sslmode="require", autocommit=True, connect_timeout=10,
        options="-c search_path=ecotech,pg_catalog", prepare_threshold=None
    )


def verificar_tablas(conexion):
    cursor = conexion.cursor()
    try:
        # LIMIT 0 comprueba las columnas sin leer registros.
        cursor.execute("""
            SELECT id_empleado, nombre, direccion, telefono,
                   correo, fecha_inicio, salario, rol
            FROM empleado LIMIT 0
        """)
        cursor.fetchall()
        cursor.execute("""
            SELECT id_cuenta, id_empleado, nombre_usuario,
                   correo, contrasena_cifrada
            FROM cuenta_usuario LIMIT 0
        """)
        cursor.fetchall()
        cursor.execute("""
            SELECT id_historial, fecha, operacion, entidad, id_registro, id_empleado,
                   usuario_mysql, detalle, datos_anteriores, datos_nuevos
            FROM historial_cambios LIMIT 0
        """)
        cursor.fetchall()
        for entidad in CONFIGURACION_ENTIDADES:
            tabla, campo_id, campos = CONFIGURACION_ENTIDADES[entidad]
            columnas = ", ".join((campo_id,) + campos)
            cursor.execute(f"SELECT {columnas} FROM {tabla} LIMIT 0")
            cursor.fetchall()
    finally:
        cursor.close()


def leer_empleado(cursor, id_empleado):
    cursor.execute("""
        SELECT id_empleado, nombre, direccion, telefono,
               correo, fecha_inicio, salario, rol
        FROM empleado WHERE id_empleado = %s FOR UPDATE
    """, (id_empleado,))
    return cursor.fetchone()


def leer_cuenta(cursor, id_empleado):
    # La contraseña queda fuera de las consultas para el historial.
    cursor.execute("""
        SELECT id_cuenta, id_empleado, nombre_usuario, correo
        FROM cuenta_usuario WHERE id_empleado = %s FOR UPDATE
    """, (id_empleado,))
    return cursor.fetchone()


def registrar_historial(cursor, operacion, entidad, id_empleado,
                        detalle, anteriores=None, nuevos=None, id_registro=None):
    # JSON convierte los datos a texto para conservar el antes y el después.
    antes = None
    despues = None
    if anteriores is not None:
        antes = json.dumps(anteriores, ensure_ascii=False, default=str)
    if nuevos is not None:
        despues = json.dumps(nuevos, ensure_ascii=False, default=str)
    if id_registro is None:
        if entidad == "EMPLEADO":
            id_registro = id_empleado
        elif entidad == "CUENTA_USUARIO":
            datos_cuenta = nuevos if nuevos is not None else anteriores
            id_registro = datos_cuenta["id_cuenta"]
    if id_registro is None:
        raise ValueError("Falta el ID del registro para guardar su historial.")
    cursor.execute("""
        INSERT INTO historial_cambios
        (operacion, entidad, id_registro, id_empleado, usuario_mysql,
         detalle, datos_anteriores, datos_nuevos)
        VALUES (%s, %s, %s, %s, CURRENT_USER, %s, %s, %s)
    """, (operacion, entidad, id_registro, id_empleado, detalle, antes, despues))
    # No hay commit aquí: lo realiza la función CRUD al terminar todo.


def agregar_empleado(conexion, empleado):
    cuenta = empleado.get_cuenta_usuario()
    if cuenta is None:
        raise ValueError("Debe asignar una cuenta antes de guardar el empleado.")
    token = cuenta.get_contrasena_cifrada()
    cursor = conexion.cursor(row_factory=dict_row)
    try:
        # CAMBIO SUPABASE: BEGIN inicia la misma operación con commit/rollback.
        cursor.execute("BEGIN")
        cursor.execute("""
            INSERT INTO empleado
            (nombre, direccion, telefono, correo, fecha_inicio, salario, rol)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id_empleado
        """, (
            empleado.get_nombre(), empleado.get_direccion(),
            empleado.get_telefono(), empleado.get_correo(),
            empleado.get_fecha_inicio(), empleado.get_salario(), empleado.get_rol()
        ))
        # CAMBIO SUPABASE: RETURNING entrega el ID que generó PostgreSQL.
        id_nuevo = cursor.fetchone()["id_empleado"]
        cursor.execute("""
            INSERT INTO cuenta_usuario
            (id_empleado, nombre_usuario, correo, contrasena_cifrada)
            VALUES (%s, %s, %s, %s)
        """, (id_nuevo, cuenta.get_nombre(), cuenta.get_correo(), token))
        datos_empleado = leer_empleado(cursor, id_nuevo)
        datos_cuenta = leer_cuenta(cursor, id_nuevo)
        registrar_historial(
            cursor, "AGREGAR", "EMPLEADO", id_nuevo,
            "Empleado creado.", nuevos=datos_empleado
        )
        registrar_historial(
            cursor, "AGREGAR", "CUENTA_USUARIO", id_nuevo,
            "Cuenta creada con contraseña cifrada.", nuevos=datos_cuenta
        )
        conexion.commit()
        return id_nuevo
    except (Error, ValueError):
        conexion.rollback()
        raise
    finally:
        cursor.close()


def consultar_empleados(conexion):
    cursor = conexion.cursor(row_factory=dict_row)
    try:
        cursor.execute("""
            SELECT id_empleado, nombre, direccion, telefono,
                   correo, fecha_inicio, salario, rol
            FROM empleado ORDER BY id_empleado
        """)
        empleados = []
        for fila in cursor.fetchall():
            empleados.append(Empleado(
                fila["id_empleado"], fila["nombre"], fila["direccion"],
                fila["telefono"], fila["correo"], fila["fecha_inicio"],
                fila["salario"], fila["rol"]
            ))
        return empleados
    finally:
        cursor.close()


def buscar_empleado(conexion, id_empleado):
    cursor = conexion.cursor(row_factory=dict_row)
    try:
        cursor.execute("""
            SELECT id_empleado, nombre, correo, rol
            FROM empleado WHERE id_empleado = %s
        """, (id_empleado,))
        return cursor.fetchone()
    finally:
        cursor.close()


def actualizar_empleado(conexion, empleado):
    cursor = conexion.cursor(row_factory=dict_row)
    try:
        # CAMBIO SUPABASE: BEGIN inicia la misma operación con commit/rollback.
        cursor.execute("BEGIN")
        anteriores = leer_empleado(cursor, empleado.get_id())
        if anteriores is None:
            conexion.rollback()
            return False
        cuenta_anterior = leer_cuenta(cursor, empleado.get_id())
        if empleado.get_rol() != "Gerente":
            cursor.execute("SELECT id_departamento FROM departamento WHERE gerente_id = %s LIMIT 1", (empleado.get_id(),))
            if cursor.fetchone() is not None:
                raise ValueError("Ese empleado dirige un departamento. Cambie primero el gerente del departamento.")
        cursor.execute("""
            UPDATE empleado
            SET nombre = %s, direccion = %s, telefono = %s,
                correo = %s, fecha_inicio = %s, salario = %s, rol = %s
            WHERE id_empleado = %s
        """, (
            empleado.get_nombre(), empleado.get_direccion(),
            empleado.get_telefono(), empleado.get_correo(),
            empleado.get_fecha_inicio(), empleado.get_salario(), empleado.get_rol(),
            empleado.get_id()
        ))
        cursor.execute("""
            UPDATE cuenta_usuario SET correo = %s WHERE id_empleado = %s
        """, (empleado.get_correo(), empleado.get_id()))
        nuevos = leer_empleado(cursor, empleado.get_id())
        cuenta_nueva = leer_cuenta(cursor, empleado.get_id())
        if anteriores != nuevos:
            registrar_historial(
                cursor, "ACTUALIZAR", "EMPLEADO", empleado.get_id(),
                "Datos del empleado actualizados.", anteriores, nuevos
            )
        if cuenta_anterior != cuenta_nueva:
            registrar_historial(
                cursor, "ACTUALIZAR", "CUENTA_USUARIO", empleado.get_id(),
                "Correo sincronizado con el empleado.",
                cuenta_anterior, cuenta_nueva
            )
        conexion.commit()
        return True
    except (Error, ValueError):
        conexion.rollback()
        raise
    finally:
        cursor.close()


def eliminar_empleado(conexion, id_empleado):
    cursor = conexion.cursor(row_factory=dict_row)
    try:
        # CAMBIO SUPABASE: BEGIN inicia la misma operación con commit/rollback.
        cursor.execute("BEGIN")
        anteriores = leer_empleado(cursor, id_empleado)
        if anteriores is None:
            conexion.rollback()
            return False
        cuenta = leer_cuenta(cursor, id_empleado)
        sql = "DELETE FROM empleado WHERE id_empleado = %s"
        cursor.execute(sql, (id_empleado,))
        registrar_historial(
            cursor, "ELIMINAR", "EMPLEADO", id_empleado,
            "Empleado eliminado.", anteriores=anteriores
        )
        if cuenta is not None:
            registrar_historial(
                cursor, "ELIMINAR", "CUENTA_USUARIO", id_empleado,
                "Cuenta eliminada junto con su empleado.", anteriores=cuenta
            )
        conexion.commit()
        return True
    except (Error, ValueError):
        conexion.rollback()
        raise
    finally:
        cursor.close()


def consultar_cuentas(conexion):
    cursor = conexion.cursor(row_factory=dict_row)
    try:
        cursor.execute("""
            SELECT c.id_cuenta, c.id_empleado, c.nombre_usuario, c.correo,
                   e.nombre AS empleado
            FROM cuenta_usuario c
            INNER JOIN empleado e ON e.id_empleado = c.id_empleado
            ORDER BY c.id_cuenta
        """)
        return cursor.fetchall()
    finally:
        cursor.close()


def agregar_cuenta(conexion, id_empleado, cuenta):
    token = cuenta.get_contrasena_cifrada()
    cursor = conexion.cursor(row_factory=dict_row)
    try:
        # CAMBIO SUPABASE: BEGIN inicia la misma operación con commit/rollback.
        cursor.execute("BEGIN")
        empleado = leer_empleado(cursor, id_empleado)
        if empleado is None:
            conexion.rollback()
            return None
        if cuenta.get_correo() != empleado["correo"]:
            raise ValueError("La cuenta debe usar el correo del empleado.")
        cursor.execute("""
            INSERT INTO cuenta_usuario
            (id_empleado, nombre_usuario, correo, contrasena_cifrada)
            VALUES (%s, %s, %s, %s)
            RETURNING id_cuenta
        """, (id_empleado, cuenta.get_nombre(), cuenta.get_correo(), token))
        id_cuenta = cursor.fetchone()["id_cuenta"]
        datos = leer_cuenta(cursor, id_empleado)
        registrar_historial(
            cursor, "AGREGAR", "CUENTA_USUARIO", id_empleado,
            "Cuenta creada para un empleado existente.", nuevos=datos
        )
        conexion.commit()
        return id_cuenta
    except (Error, ValueError):
        conexion.rollback()
        raise
    finally:
        cursor.close()


def actualizar_cuenta(conexion, id_empleado, cuenta):
    token = cuenta.get_contrasena_cifrada()
    cursor = conexion.cursor(row_factory=dict_row)
    try:
        # CAMBIO SUPABASE: BEGIN inicia la misma operación con commit/rollback.
        cursor.execute("BEGIN")
        empleado = leer_empleado(cursor, id_empleado)
        if empleado is None:
            conexion.rollback()
            return False
        if cuenta.get_correo() != empleado["correo"]:
            raise ValueError("La cuenta debe usar el correo del empleado.")
        anteriores = leer_cuenta(cursor, id_empleado)
        if anteriores is None:
            conexion.rollback()
            return False
        cursor.execute("""
            UPDATE cuenta_usuario
            SET nombre_usuario = %s, contrasena_cifrada = %s
            WHERE id_empleado = %s
        """, (cuenta.get_nombre(), token, id_empleado))
        nuevos = leer_cuenta(cursor, id_empleado)
        registrar_historial(
            cursor, "ACTUALIZAR", "CUENTA_USUARIO", id_empleado,
            "Usuario y contraseña actualizados; contraseña oculta.",
            anteriores, nuevos
        )
        conexion.commit()
        return True
    except (Error, ValueError):
        conexion.rollback()
        raise
    finally:
        cursor.close()


def eliminar_cuenta(conexion, id_cuenta):
    cursor = conexion.cursor(row_factory=dict_row)
    try:
        # CAMBIO SUPABASE: BEGIN inicia la misma operación con commit/rollback.
        cursor.execute("BEGIN")
        cursor.execute("""
            SELECT id_cuenta, id_empleado, nombre_usuario, correo
            FROM cuenta_usuario WHERE id_cuenta = %s FOR UPDATE
        """, (id_cuenta,))
        anteriores = cursor.fetchone()
        if anteriores is None:
            conexion.rollback()
            return False
        sql = "DELETE FROM cuenta_usuario WHERE id_cuenta = %s"
        cursor.execute(sql, (id_cuenta,))
        registrar_historial(
            cursor, "ELIMINAR", "CUENTA_USUARIO", anteriores["id_empleado"],
            "Cuenta eliminada; el empleado se conserva.",
            anteriores=anteriores
        )
        conexion.commit()
        return True
    except (Error, ValueError):
        conexion.rollback()
        raise
    finally:
        cursor.close()


def comprobar_acceso(conexion, nombre, contrasena, servicio):
    cursor = conexion.cursor()
    try:
        cursor.execute("""
            SELECT nombre_usuario, correo, contrasena_cifrada
            FROM cuenta_usuario WHERE nombre_usuario = %s
        """, (nombre,))
        fila = cursor.fetchone()
        if fila is None:
            return False
        cuenta = CuentaUsuario(fila[0], fila[1], servicio)
        cuenta.cargar_contrasena_cifrada(fila[2])
        return cuenta.acceso_cuenta(nombre, contrasena)
    finally:
        cursor.close()


def configuracion_entidad(entidad):
    if entidad not in CONFIGURACION_ENTIDADES:
        raise ValueError("La entidad solicitada no está permitida.")
    return CONFIGURACION_ENTIDADES[entidad]


def leer_registro(cursor, entidad, id_registro, bloquear=False):
    tabla, campo_id, campos = configuracion_entidad(entidad)
    columnas = ", ".join((campo_id,) + campos)
    sql = f"SELECT {columnas} FROM {tabla} WHERE {campo_id} = %s"
    if bloquear:
        sql += " FOR UPDATE"
    cursor.execute(sql, (validar_id(id_registro),))
    return cursor.fetchone()


def buscar_registro(conexion, entidad, id_registro):
    cursor = conexion.cursor(row_factory=dict_row)
    try:
        return leer_registro(cursor, entidad, id_registro)
    finally:
        cursor.close()


def objeto_desde_fila(entidad, fila):
    if entidad == "PROYECTO":
        return Proyecto(fila["id_proyecto"], fila["nombre"], fila["descripcion_proyecto"],
                        fila["fecha_de_inicio"], fila["miembro"], fila["presupuesto"])
    if entidad == "DEPARTAMENTO":
        return Departamento(fila["id_departamento"], fila["nombre"], fila["gerente_id"], fila["departamento"])
    if entidad == "ASIGNACION":
        return Asignacion(fila["id_asignacion"], fila["fecha"], fila["horas_trabajadas"],
                          fila["tareas_realizadas"], fila["id_empleado"], fila["id_proyecto"])
    raise ValueError("La entidad solicitada no está permitida.")


def consultar_registros(conexion, entidad):
    tabla, campo_id, campos = configuracion_entidad(entidad)
    columnas = ", ".join((campo_id,) + campos)
    cursor = conexion.cursor(row_factory=dict_row)
    try:
        cursor.execute(f"SELECT {columnas} FROM {tabla} ORDER BY {campo_id}")
        registros = []
        for fila in cursor.fetchall():
            registros.append(objeto_desde_fila(entidad, fila))
        return registros
    finally:
        cursor.close()


def verificar_relaciones(cursor, entidad, datos):
    if entidad == "DEPARTAMENTO":
        gerente = leer_empleado(cursor, datos["gerente_id"])
        if gerente is None:
            raise ValueError("No existe el empleado elegido como gerente.")
        if validar_rol(gerente["rol"]) != "Gerente":
            raise ValueError("El responsable del departamento debe tener el rol Gerente.")
    elif entidad == "ASIGNACION":
        if datos["id_empleado"] is None or datos["id_proyecto"] is None:
            raise ValueError("Debe vincular la asignación con un empleado y un proyecto.")
        if leer_empleado(cursor, datos["id_empleado"]) is None:
            raise ValueError("No existe el empleado de la asignación.")
        if leer_registro(cursor, "PROYECTO", datos["id_proyecto"], bloquear=True) is None:
            raise ValueError("No existe el proyecto de la asignación.")


def empleado_relacionado(entidad, datos):
    if entidad == "DEPARTAMENTO":
        return datos["gerente_id"]
    if entidad == "ASIGNACION":
        return datos["id_empleado"]
    return None


def guardar_registro(conexion, entidad, registro, actualizar=False):
    # Estas tres entidades comparten el mismo control de transacción e historial.
    tabla, campo_id, campos = configuracion_entidad(entidad)
    datos = registro.get_datos()
    valores = tuple(datos[campo] for campo in campos)
    cursor = conexion.cursor(row_factory=dict_row)
    try:
        # CAMBIO SUPABASE: BEGIN inicia la misma operación con commit/rollback.
        cursor.execute("BEGIN")
        anteriores = None
        if actualizar:
            id_registro = validar_id(registro.get_id())
            anteriores = leer_registro(cursor, entidad, id_registro, bloquear=True)
            if anteriores is None:
                conexion.rollback()
                return False
        verificar_relaciones(cursor, entidad, datos)
        if actualizar:
            cambios = ", ".join(campo + " = %s" for campo in campos)
            sql = f"UPDATE {tabla} SET {cambios} WHERE {campo_id} = %s"
            cursor.execute(sql, valores + (id_registro,))
            operacion = "ACTUALIZAR"
        else:
            columnas = ", ".join(campos)
            parametros = ", ".join(["%s"] * len(campos))
            sql = f"INSERT INTO {tabla} ({columnas}) VALUES ({parametros}) RETURNING {campo_id}"
            cursor.execute(sql, valores)
            id_registro = cursor.fetchone()[campo_id]
            operacion = "AGREGAR"
        nuevos = leer_registro(cursor, entidad, id_registro)
        if anteriores != nuevos:
            registrar_historial(cursor, operacion, entidad, empleado_relacionado(entidad, nuevos),
                                f"{entidad}: registro guardado.", anteriores, nuevos, id_registro)
        conexion.commit()
        return True if actualizar else id_registro
    except (Error, ValueError):
        conexion.rollback()
        raise
    finally:
        cursor.close()


def eliminar_registro(conexion, entidad, id_registro):
    tabla, campo_id, campos = configuracion_entidad(entidad)
    id_registro = validar_id(id_registro)
    cursor = conexion.cursor(row_factory=dict_row)
    try:
        # CAMBIO SUPABASE: BEGIN inicia la misma operación con commit/rollback.
        cursor.execute("BEGIN")
        anteriores = leer_registro(cursor, entidad, id_registro, bloquear=True)
        if anteriores is None:
            conexion.rollback()
            return False
        sql = f"DELETE FROM {tabla} WHERE {campo_id} = %s"
        cursor.execute(sql, (id_registro,))
        registrar_historial(cursor, "ELIMINAR", entidad, empleado_relacionado(entidad, anteriores),
                            f"{entidad}: registro eliminado.", anteriores=anteriores, id_registro=id_registro)
        conexion.commit()
        return True
    except (Error, ValueError):
        conexion.rollback()
        raise
    finally:
        cursor.close()


def agregar_proyecto(conexion, proyecto):
    return guardar_registro(conexion, "PROYECTO", proyecto)


def actualizar_proyecto(conexion, proyecto):
    return guardar_registro(conexion, "PROYECTO", proyecto, actualizar=True)


def consultar_proyectos(conexion):
    return consultar_registros(conexion, "PROYECTO")


def buscar_proyecto(conexion, id_proyecto):
    return buscar_registro(conexion, "PROYECTO", id_proyecto)


def eliminar_proyecto(conexion, id_proyecto):
    return eliminar_registro(conexion, "PROYECTO", id_proyecto)


def agregar_departamento(conexion, departamento):
    return guardar_registro(conexion, "DEPARTAMENTO", departamento)


def actualizar_departamento(conexion, departamento):
    return guardar_registro(conexion, "DEPARTAMENTO", departamento, actualizar=True)


def consultar_departamentos(conexion):
    return consultar_registros(conexion, "DEPARTAMENTO")


def buscar_departamento(conexion, id_departamento):
    return buscar_registro(conexion, "DEPARTAMENTO", id_departamento)


def eliminar_departamento(conexion, id_departamento):
    return eliminar_registro(conexion, "DEPARTAMENTO", id_departamento)


def agregar_asignacion(conexion, asignacion):
    return guardar_registro(conexion, "ASIGNACION", asignacion)


def actualizar_asignacion(conexion, asignacion):
    return guardar_registro(conexion, "ASIGNACION", asignacion, actualizar=True)


def consultar_asignaciones(conexion):
    return consultar_registros(conexion, "ASIGNACION")


def buscar_asignacion(conexion, id_asignacion):
    return buscar_registro(conexion, "ASIGNACION", id_asignacion)


def eliminar_asignacion(conexion, id_asignacion):
    return eliminar_registro(conexion, "ASIGNACION", id_asignacion)


def registrar_horas_asignacion(conexion, id_asignacion, horas):
    horas = validar_horas_adicionales(horas)
    cursor = conexion.cursor(row_factory=dict_row)
    try:
        # CAMBIO SUPABASE: BEGIN inicia la misma operación con commit/rollback.
        cursor.execute("BEGIN")
        anteriores = leer_registro(cursor, "ASIGNACION", id_asignacion, bloquear=True)
        if anteriores is None:
            conexion.rollback()
            return None
        asignacion = objeto_desde_fila("ASIGNACION", anteriores)
        asignacion.sumar_horas(horas)
        cursor.execute("UPDATE asignacion SET horas_trabajadas = horas_trabajadas + %s WHERE id_asignacion = %s",
                       (horas, id_asignacion))
        nuevos = leer_registro(cursor, "ASIGNACION", id_asignacion)
        registrar_historial(cursor, "ACTUALIZAR", "ASIGNACION", nuevos["id_empleado"],
                            f"Se agregaron {horas} horas.", anteriores, nuevos, id_asignacion)
        conexion.commit()
        return nuevos["horas_trabajadas"]
    except (Error, ValueError):
        conexion.rollback()
        raise
    finally:
        cursor.close()


def consultar_historial(conexion, id_empleado=None, operacion=None,
                        texto="", limite=20, entidad=None, id_registro=None):
    if id_empleado is not None and id_empleado <= 0:
        raise ValueError("El ID debe ser mayor que cero.")
    if operacion is not None and operacion not in (
        "AGREGAR", "ACTUALIZAR", "ELIMINAR"
    ):
        raise ValueError("Operación de historial inválida.")
    if not 1 <= limite <= 200:
        raise ValueError("El límite debe estar entre 1 y 200.")
    if entidad is not None and entidad not in ("EMPLEADO", "CUENTA_USUARIO", "PROYECTO", "DEPARTAMENTO", "ASIGNACION"):
        raise ValueError("Entidad de historial inválida.")
    if id_registro is not None:
        validar_id(id_registro)
        if entidad is None:
            raise ValueError("Seleccione una entidad para filtrar por el ID de un registro.")
    sql = """
        SELECT id_historial, fecha, operacion, entidad, id_registro, id_empleado,
               usuario_mysql, detalle
        FROM historial_cambios WHERE 1 = 1
    """
    datos = []
    if entidad is not None:
        sql += " AND entidad = %s"
        datos.append(entidad)
    if id_registro is not None:
        sql += " AND id_registro = %s"
        datos.append(id_registro)
    if id_empleado is not None:
        sql += " AND id_empleado = %s"
        datos.append(id_empleado)
    if operacion is not None:
        sql += " AND operacion = %s"
        datos.append(operacion)
    if texto:
        # CAMBIO SUPABASE: strpos busca texto literal, incluso si contiene % o _.
        sql += """
            AND (
                strpos(detalle, %s) > 0
                OR strpos(COALESCE(datos_anteriores, ''), %s) > 0
                OR strpos(COALESCE(datos_nuevos, ''), %s) > 0
            )
        """
        datos.extend([texto, texto, texto])
    sql += " ORDER BY fecha DESC, id_historial DESC LIMIT %s"
    datos.append(limite)
    cursor = conexion.cursor(row_factory=dict_row)
    try:
        cursor.execute(sql, tuple(datos))
        return cursor.fetchall()
    finally:
        cursor.close()


def consultar_detalle_historial(conexion, id_historial):
    cursor = conexion.cursor(row_factory=dict_row)
    try:
        cursor.execute("""
            SELECT id_historial, fecha, operacion, entidad, id_registro, id_empleado,
                   usuario_mysql, detalle, datos_anteriores, datos_nuevos
            FROM historial_cambios WHERE id_historial = %s
        """, (id_historial,))
        return cursor.fetchone()
    finally:
        cursor.close()


def pedir_id(mensaje):
    return pedir_dato(mensaje, validar_id)


def pedir_dato(mensaje, validacion, ocultar=False, revisar_formato=False):
    while True:
        try:
            if ocultar:
                entrada = getpass(mensaje)
            else:
                entrada = input(mensaje).strip()
            if revisar_formato:
                return validacion(entrada, revisar_formato=True)
            return validacion(entrada)
        except ValueError as error:
            print("Dato inválido:", error)
            if ocultar:
                print("Intente con otra contraseña para continuar.")
            else:
                print("Corrija este dato para continuar.")


def pedir_rol(conexion=None, id_empleado=None):
    while True:
        rol = pedir_dato("Rol (Empleado/Gerente): ", validar_rol)
        if conexion is not None and id_empleado is not None and rol != "Gerente":
            cursor = conexion.cursor()
            try:
                cursor.execute("SELECT id_departamento FROM departamento WHERE gerente_id = %s LIMIT 1", (id_empleado,))
                es_gerente = cursor.fetchone() is not None
            finally:
                cursor.close()
            if es_gerente:
                print("Dato inválido: dirige un departamento. Debe mantener el rol Gerente o cambiar primero el responsable del departamento.")
                print("Corrija solo el rol para continuar.")
                continue
        return rol


def pedir_empleado(id_empleado, conexion=None):
    nombre = pedir_dato("Nombre: ", validar_nombre, revisar_formato=True)
    direccion = pedir_dato("Dirección: ", validar_direccion, revisar_formato=True)
    telefono = pedir_dato("Teléfono (12 en total: + y 11 números): ", validar_telefono, revisar_formato=True)
    correo = pedir_dato("Correo (debe terminar en @gmail.com): ", validar_correo, revisar_formato=True)
    fecha = pedir_dato("Inicio del contrato (AAAA-MM-DD): ", validar_fecha)
    salario = pedir_dato("Salario, usando punto para los decimales: ", validar_salario)
    rol = pedir_rol(conexion, id_empleado)
    return Empleado(
        id_empleado, nombre, direccion, telefono, correo, fecha, salario, rol
    )


def pedir_cuenta(correo, servicio):
    nombre = pedir_dato("Nombre de usuario: ", validar_nombre_usuario, revisar_formato=True)
    print("La contraseña admite mayúsculas, minúsculas, números y símbolos permitidos (8 a 128 caracteres).")
    print("No se permiten comillas, paréntesis, barras (/ o \\), corchetes ni llaves.")
    contrasena = pedir_dato("Contraseña de la cuenta: ", validar_contrasena, ocultar=True)
    return CuentaUsuario(nombre, correo, servicio, contrasena)


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
            f'Historial {fila["id_historial"]} | {fila["fecha"]} | '
            f'{fila["operacion"]} | {fila["entidad"]} {fila["id_registro"]} | '
            f'Empleado {fila["id_empleado"]} | Base de datos: {fila["usuario_mysql"]}'
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
    print(f'\nHistorial {fila["id_historial"]}: {fila["detalle"]}')
    for campo, titulo in (
        ("datos_anteriores", "ANTES"), ("datos_nuevos", "DESPUÉS")
    ):
        print(titulo + ":")
        if fila[campo] is None:
            print("No corresponde.")
        else:
            print(json.dumps(json.loads(fila[campo]), ensure_ascii=False, indent=2))


def mostrar_error_supabase(error):
    # CAMBIO SUPABASE: PostgreSQL identifica sus errores mediante sqlstate.
    estado = error.sqlstate
    if estado == "23505":
        print("Ese usuario ya existe o el empleado ya tiene una cuenta.")
    elif estado == "23503":
        print("Revise los registros relacionados: el ID no existe o el registro todavía está en uso.")
    elif estado in ("23514", "23502", "22001", "22003", "22007"):
        print("Un dato no cumple las restricciones de la base. Revise los valores ingresados.")
    elif estado in ("40P01", "40001", "55P03"):
        print("Otro cambio está utilizando esos registros. Intente nuevamente.")
    elif estado in ("42P01", "42703", "3F000"):
        print("Falta el esquema de EcoTech. Ejecute ecotech_supabase.sql en el proyecto correcto.")
    elif estado == "42501":
        print("El usuario de la base no tiene permiso para realizar esta operación.")
    elif estado and estado.startswith("28"):
        print("El usuario o la contraseña de la base son incorrectos.")
    elif estado and estado.startswith("08"):
        print("No se pudo mantener la conexión. Revise el servidor y la red.")
    else:
        # No mostramos cadenas de conexión ni detalles que puedan contener datos personales.
        print("No se completó la operación en Supabase. Código:", estado or "conexión/configuración")


def pedir_id_vinculado(conexion, entidad, solo_gerentes=False):
    if entidad == "EMPLEADO":
        registros = consultar_empleados(conexion)
        disponibles = []
        for empleado in registros:
            if not solo_gerentes or empleado.get_rol() == "Gerente":
                disponibles.append(empleado)
        mensaje = "ID del gerente: " if solo_gerentes else "ID del empleado: "
    else:
        disponibles = consultar_proyectos(conexion)
        mensaje = "ID del proyecto: "
    if not disponibles:
        if solo_gerentes:
            raise ValueError("Primero debe agregar un empleado con rol Gerente o actualizar su rol.")
        raise ValueError("Primero debe agregar al menos un " + entidad.lower() + ".")
    print("Registros disponibles:")
    for registro in disponibles:
        print(f"ID {registro.get_id()}: {registro.get_nombre()}")
    while True:
        numero = pedir_id(mensaje)
        if entidad == "EMPLEADO":
            fila = buscar_empleado(conexion, numero)
        else:
            fila = buscar_proyecto(conexion, numero)
        if fila is None:
            print("Dato inválido: no existe ese ID. Corrija solo este dato.")
        elif solo_gerentes and validar_rol(fila["rol"]) != "Gerente":
            print("Dato inválido: el empleado debe tener rol Gerente. Elija otro ID.")
        else:
            return numero


def pedir_registro(conexion, entidad, id_registro=None):
    if entidad == "PROYECTO":
        nombre = pedir_dato("Nombre del proyecto: ", validar_nombre_entidad)
        descripcion = pedir_dato("Descripción del proyecto: ", validar_descripcion)
        fecha = pedir_dato("Fecha de inicio (AAAA-MM-DD): ", validar_fecha)
        miembro = pedir_dato("Miembro o referencia del equipo: ", validar_miembro)
        presupuesto = pedir_dato("Presupuesto, usando punto para los decimales: ", validar_presupuesto)
        return Proyecto(id_registro, nombre, descripcion, fecha, miembro, presupuesto)
    if entidad == "DEPARTAMENTO":
        gerente_id = pedir_id_vinculado(conexion, "EMPLEADO", solo_gerentes=True)
        nombre = pedir_dato("Nombre del departamento: ", validar_nombre_entidad)
        departamento = pedir_dato("Descripción o área del departamento: ", validar_departamento)
        return Departamento(id_registro, nombre, gerente_id, departamento)
    if entidad == "ASIGNACION":
        id_empleado = pedir_id_vinculado(conexion, "EMPLEADO")
        id_proyecto = pedir_id_vinculado(conexion, "PROYECTO")
        fecha = pedir_dato("Fecha de la asignación (AAAA-MM-DD): ", validar_fecha)
        horas = pedir_dato("Horas trabajadas (número entero): ", validar_horas)
        tareas = pedir_dato("Tareas realizadas: ", validar_descripcion)
        return Asignacion(id_registro, fecha, horas, tareas, id_empleado, id_proyecto)
    raise ValueError("La entidad solicitada no está permitida.")


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
                    print(f"Horas guardadas en Base de datos: {total}. Cambio registrado.")
            else:
                print("Opción inválida. Elija una de las opciones mostradas.")
        except ValueError as error:
            print("Dato inválido:", error)
        except Error as error:
            mostrar_error_supabase(error)


# CAMBIO INTEGRACIÓN: usamos la tabla que ya tenía el equipo, sin duplicar las horas.
def guardar_tiempo(conexion, tiempo):
    horas = validar_horas_adicionales(tiempo.get_horas_trabajadas())
    asignacion = Asignacion(
        None, tiempo.fecha, horas, tiempo.get_descripcion_de_tareas(),
        tiempo.empleado, tiempo.proyecto
    )
    return agregar_asignacion(conexion, asignacion)


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
    empleados = consultar_empleados(conexion)
    proyectos = consultar_proyectos(conexion)
    departamentos = consultar_departamentos(conexion)
    asignaciones = consultar_asignaciones(conexion)
    print("\nINFORME GENERAL DE ECOTECH")
    print("\nEMPLEADOS")
    for empleado in empleados:
        print(empleado)
    print("\nPROYECTOS")
    for proyecto in proyectos:
        print(proyecto)
    print("\nDEPARTAMENTOS")
    for departamento in departamentos:
        print(departamento)

    # Buscamos los nombres por ID para que el informe sea más fácil de leer.
    nombres_empleados = {empleado.get_id(): empleado.get_nombre() for empleado in empleados}
    nombres_proyectos = {proyecto.get_id(): proyecto.get_nombre() for proyecto in proyectos}
    print("\nREGISTROS DE TIEMPO")
    if not asignaciones:
        print("Todavía no hay registros de tiempo.")
    total = 0
    for asignacion in asignaciones:
        tiempo = Tiempo(
            asignacion.get_fecha(), asignacion.get_horas_trabajadas(),
            asignacion.get_tareas_realizadas(),
            nombres_empleados.get(asignacion.get_id_empleado(), "Sin vincular"),
            nombres_proyectos.get(asignacion.get_id_proyecto(), "Sin vincular"),
            mostrar_mensaje=False
        )
        # El modelo original no relaciona empleado con departamento: no inventamos esa relación.
        informe = Informes(tiempo.empleado, tiempo.proyecto, "No disponible para este registro", tiempo)
        print("\nRegistro:", asignacion.get_id())
        informe.generar_informes()
        total += tiempo.get_horas_trabajadas()
    print("\nTotal de horas:", total)


# CAMBIO EXPORTACIÓN: cada opción consulta todos los registros y crea UN archivo.
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
                        f'Cuenta {cuenta["id_cuenta"]} | '
                        f'Empleado {cuenta["id_empleado"]}: {cuenta["empleado"]} | '
                        f'Usuario: {cuenta["nombre_usuario"]} | {cuenta["correo"]}'
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
        except OSError:
            print("No se pudo guardar el archivo. Revise los permisos de la carpeta reportes.")
        except ImportError:
            print("Falta una biblioteca. Instale las dependencias de requirements.txt.")
        except Error as error:
            mostrar_error_supabase(error)


def main():
    conexion = None
    try:
        print("ECOTECH - SUPABASE (POSTGRESQL)")
        # CAMBIO SUPABASE: estos datos están en Connect > Session pooler.
        host = os.getenv("SUPABASE_DB_HOST", "").strip()
        usuario = os.getenv("SUPABASE_DB_USER", "").strip()
        if not host:
            host = input("Servidor de Supabase (host del Session pooler): ").strip()
        if not usuario:
            usuario = input("Usuario de la base (postgres.ID_DEL_PROYECTO): ").strip()
        puerto = int(os.getenv("SUPABASE_DB_PORT", str(SUPABASE_PUERTO)))
        base = os.getenv("SUPABASE_DB_NAME", SUPABASE_BASE)
        contrasena = os.getenv("SUPABASE_DB_PASSWORD")
        if not contrasena:
            contrasena = getpass("Contraseña de la base de Supabase: ")
        conexion = conectar_supabase(usuario, contrasena, host, puerto, base)
        verificar_tablas(conexion)
        # Conservamos el cifrado del avance original. Al migrar cuentas, use la misma clave.
        archivo_clave = Path(os.getenv("ECOTECH_FERNET_KEY_FILE") or Path(__file__).with_name("clave_fernet.key"))
        cursor = conexion.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM cuenta_usuario")
            cuentas_guardadas = cursor.fetchone()[0]
        finally:
            cursor.close()
        if cuentas_guardadas > 0 and not archivo_clave.exists():
            raise ValueError("Falta clave_fernet.key. Restaure la clave original.")
        servicio = ServicioCifrado(archivo_clave)
        print("Conexión a Supabase lista.")
        menu(conexion, servicio)
    except Error as error:
        mostrar_error_supabase(error)
    except (OSError, ValueError) as error:
        print("No se pudo iniciar el programa:", error)
    except (KeyboardInterrupt, EOFError):
        print("\nPrograma finalizado.")
    finally:
        if conexion is not None:
            conexion.close()


if __name__ == "__main__":
    main()
