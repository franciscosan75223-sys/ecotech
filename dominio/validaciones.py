from datetime import datetime
from decimal import Decimal, InvalidOperation


def validar_cadena(valor, nombre_campo):
    if not isinstance(valor, str):
        raise TypeError(nombre_campo + " debe ser un texto.")
    return valor


def validar_nombre(nombre, revisar_formato=False):
    nombre = validar_cadena(nombre, 'El nombre')
    if not nombre.strip() or len(nombre) > 100:
        raise ValueError("El nombre debe tener entre 1 y 100 caracteres.")
    nombre = nombre.strip()
    if revisar_formato:
        letras = nombre.replace(" ", "").replace("-", "").replace("'", "").replace("’", "")
        if not letras.isalpha():
            raise ValueError("El nombre debe contener letras; puede usar espacios, guiones y apostrofes.")
    return nombre


def validar_direccion(direccion, revisar_formato=False):
    direccion = validar_cadena(direccion, 'La direccion')
    if not direccion.strip() or len(direccion) > 200:
        raise ValueError("La direccion debe tener entre 1 y 200 caracteres.")
    direccion = direccion.strip()
    if revisar_formato:
        for caracter in direccion:
            if not caracter.isalpha() and caracter not in "0123456789 ":
                raise ValueError("La direccion solo puede contener letras, numeros y espacios.")
    return direccion


def validar_telefono(telefono, revisar_formato=False):
    telefono = validar_cadena(telefono, 'El telefono')
    telefono = telefono.strip()
    if revisar_formato:
        if not telefono.startswith("+") or len(telefono) != 12:
            raise ValueError("El telefono debe tener 12 caracteres en total: + al comienzo y 11 numeros despues.")
        numeros = telefono[1:]
        if not numeros.isascii() or not numeros.isdecimal():
            raise ValueError("Despues del + solo se permiten numeros del 0 al 9, sin espacios ni otros simbolos.")
    elif not telefono or len(telefono) > 20:
        raise ValueError("El telefono debe tener entre 1 y 20 caracteres.")
    return telefono


def validar_correo(correo, revisar_formato=False):
    correo = validar_cadena(correo, 'El correo')
    correo = correo.strip()
    if "@" not in correo or len(correo) > 150:
        raise ValueError("Ingrese un correo valido, por ejemplo usuario@gmail.com, de hasta 150 caracteres.")
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
    texto = str(fecha)
    if len(texto) != 10 or texto[4] != "-" or texto[7] != "-":
        raise ValueError("Ingrese una fecha valida con formato AAAA-MM-DD.")
    try:
        fecha = datetime.strptime(texto, "%Y-%m-%d").date()
    except ValueError as error:
        raise ValueError("Ingrese una fecha valida con formato AAAA-MM-DD.") from error
    if fecha.year < 1000:
        raise ValueError("El proyecto admite fechas desde el ano 1000.")
    return fecha


def validar_dinero(valor, nombre_campo):
    try:
        valor = Decimal(str(valor))
    except InvalidOperation as error:
        raise ValueError(nombre_campo + " debe ser un numero.") from error
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
    rol = validar_cadena(rol, 'El rol')
    rol = rol.strip().capitalize()
    if rol not in ("Empleado", "Gerente"):
        raise ValueError("El rol debe ser Empleado o Gerente.")
    return rol


def validar_texto(texto, limite, nombre_campo, permitir_saltos=False):
    texto = validar_cadena(texto, nombre_campo)
    texto = texto.strip()
    if not texto or len(texto) > limite:
        raise ValueError("{} debe tener entre 1 y {} caracteres.".format(nombre_campo, limite))
    for caracter in texto:
        if not caracter.isprintable() and not (permitir_saltos and caracter in "\r\n"):
            raise ValueError(nombre_campo + " no admite saltos de linea ni caracteres de control.")
    return texto


def validar_nombre_entidad(nombre):
    return validar_texto(nombre, 100, "El nombre")


def validar_descripcion(descripcion, permitir_saltos=False):
    return validar_texto(descripcion, 255, "La descripcion o tarea", permitir_saltos)


def validar_miembro(miembro):
    return validar_texto(miembro, 100, "El miembro")


def validar_departamento(departamento):
    return validar_texto(departamento, 100, "El departamento")


def validar_id(numero):
    try:
        numero = int(str(numero))
    except ValueError as error:
        raise ValueError("El ID debe ser un numero entero.") from error
    if numero <= 0 or numero > 2147483647:
        raise ValueError("El ID debe estar entre 1 y 2147483647.")
    return numero


def validar_horas(horas):
    try:
        horas = int(str(horas))
    except ValueError as error:
        raise ValueError("Las horas deben ser un numero entero.") from error
    if horas < 0 or horas > 2147483647:
        raise ValueError("Las horas deben estar entre 0 y 2147483647.")
    return horas


def validar_horas_adicionales(horas):
    horas = validar_horas(horas)
    if horas == 0:
        raise ValueError("Debe agregar al menos una hora.")
    return horas


def validar_nombre_usuario(nombre, revisar_formato=False):
    nombre = validar_cadena(nombre, 'El usuario')
    if not nombre.strip() or len(nombre) > 50:
        raise ValueError("El usuario debe tener entre 1 y 50 caracteres.")
    nombre = nombre.strip()
    if revisar_formato:
        for caracter in nombre:
            if not caracter.isalpha() and caracter not in "0123456789_":
                raise ValueError("El usuario solo puede contener letras, numeros y guion bajo (_).")
    return nombre


def validar_contrasena(contrasena):
    contrasena = validar_cadena(contrasena, 'La contrasena')
    if len(contrasena) < 8 or len(contrasena) > 128:
        raise ValueError("La contrasena debe tener entre 8 y 128 caracteres.")
    prohibidos = "\"'()/\\[]{}“”‘’«»"
    for caracter in contrasena:
        if caracter in prohibidos:
            raise ValueError("La contrasena no admite comillas, parentesis, barras (/ o \\), corchetes ni llaves.")
    return contrasena