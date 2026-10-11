"""Pruebas locales sin conectarse a Supabase ni modificar datos reales."""
import io
import unittest
from contextlib import redirect_stdout
from datetime import date
from unittest.mock import Mock, patch

import main as app


class PruebasAdaptacion(unittest.TestCase):
    def setUp(self):
        self.conexion = Mock()
        self.cursor = self.conexion.cursor.return_value

    def empleado_con_cuenta(self):
        empleado = app.Empleado(None, 'Persona Prueba', 'Calle Prueba 100',
                                '912345678', 'prueba@example.com', '2026-01-01', 1000)
        servicio = Mock()
        servicio.cifrar.return_value = b'token-simulado'
        cuenta = app.CuentaUsuario('usuario_prueba', 'prueba@example.com', servicio, 'Prueba123!')
        empleado.asignar_cuenta(cuenta)
        return empleado

    def test_fallo_cuenta_revierte_toda_la_operacion(self):
        self.cursor.fetchone.return_value = {'id_empleado': 7}
        self.cursor.execute.side_effect = [None, None, app.Error('fallo simulado')]
        with self.assertRaises(app.Error):
            app.agregar_empleado(self.conexion, self.empleado_con_cuenta())
        self.conexion.commit.assert_not_called()
        self.conexion.rollback.assert_called_once()
        self.cursor.close.assert_called_once()

    def test_id_postgresql_y_cifrado_fuera_del_historial(self):
        self.cursor.fetchone.side_effect = [
            {'id_empleado': 7},
            {'id_empleado': 7, 'nombre': 'Persona Prueba'},
            {'id_cuenta': 12, 'id_empleado': 7, 'nombre_usuario': 'usuario_prueba'}
        ]
        resultado = app.agregar_empleado(self.conexion, self.empleado_con_cuenta())
        self.assertEqual(resultado, 7)
        self.conexion.commit.assert_called_once()
        self.conexion.rollback.assert_not_called()
        consultas = self.cursor.execute.call_args_list
        self.assertIn('RETURNING id_empleado', consultas[1].args[0])
        historiales = [c for c in consultas if 'INSERT INTO historial_cambios' in c.args[0]]
        self.assertEqual(len(historiales), 2)
        self.assertNotIn('token-simulado', repr(historiales))
        self.assertNotIn('Prueba123!', repr(historiales))

    def test_tiempo_guarda_una_asignacion_con_sus_ids(self):
        tiempo = app.Tiempo('2026-01-10', 8, 'Tarea de prueba', 7, 3, False)
        with patch.object(app, 'agregar_asignacion', return_value=15) as guardar:
            self.assertEqual(app.guardar_tiempo(self.conexion, tiempo), 15)
        guardar.assert_called_once()
        datos = guardar.call_args.args[1].get_datos()
        self.assertEqual(datos['id_empleado'], 7)
        self.assertEqual(datos['id_proyecto'], 3)
        self.assertEqual(datos['horas_trabajadas'], 8)
        self.assertEqual(datos['fecha'], date(2026, 1, 10))

    def test_tiempo_invalido_no_llega_a_base(self):
        with patch.object(app, 'agregar_asignacion') as guardar:
            for horas in (0, -2, 1.5):
                with self.subTest(horas=horas), self.assertRaises(ValueError):
                    app.guardar_tiempo(self.conexion, app.Tiempo('2026-01-10', horas, 'Tarea', 7, 3, False))
            guardar.assert_not_called()

    def test_informe_no_duplica_horas_ni_inventa_departamento(self):
        empleado = self.empleado_con_cuenta()
        empleado._id_empleado = 7
        proyecto = app.Proyecto(3, 'Proyecto prueba', 'Descripcion', '2026-01-01', 'Equipo', 100)
        asignaciones = [app.Asignacion(1, '2026-01-10', 8, 'Tarea uno', 7, 3),
                        app.Asignacion(2, '2026-01-11', 3, 'Tarea dos', 7, 3)]
        salida = io.StringIO()
        with patch.object(app, 'consultar_empleados', return_value=[empleado]), \
             patch.object(app, 'consultar_proyectos', return_value=[proyecto]), \
             patch.object(app, 'consultar_departamentos', return_value=[]), \
             patch.object(app, 'consultar_asignaciones', return_value=asignaciones), \
             redirect_stdout(salida):
            app.mostrar_informes_desde_supabase(self.conexion)
        texto = salida.getvalue()
        self.assertIn('Total de horas: 11', texto)
        self.assertEqual(texto.count('informe de tiempo'), 2)
        self.assertIn('No disponible para este registro', texto)
        self.assertNotIn('horas registradas correctamente', texto)

    def test_busqueda_literal_y_parametrizada(self):
        texto = "50%_'; DROP TABLE empleado; --"
        self.cursor.fetchall.return_value = []
        app.consultar_historial(self.conexion, texto=texto)
        sql, parametros = self.cursor.execute.call_args.args
        self.assertNotIn(texto, sql)
        self.assertIn('strpos', sql)
        self.assertEqual(parametros[:3], (texto, texto, texto))

    def test_conexion_requiere_ssl(self):
        with patch.object(app.psycopg, 'connect') as conectar:
            app.conectar_supabase('usuario_prueba', 'contrasena-ficticia', 'host.invalid')
        self.assertEqual(conectar.call_args.kwargs['sslmode'], 'require')
        self.assertTrue(conectar.call_args.kwargs['autocommit'])
        self.assertIn('ecotech', conectar.call_args.kwargs['options'])


if __name__ == '__main__':
    unittest.main()
