"""Pruebas locales sin conectarse a Supabase ni modificar datos reales."""
import io
import unittest
from contextlib import redirect_stdout
from datetime import date
from unittest.mock import MagicMock, Mock, patch

from psycopg import Error
from dominio import Empleado, CuentaUsuario, Proyecto, Asignacion, Tiempo
from infraestructura import conexion as db
from infraestructura import repositorio as repo
from presentacion import menu as ui


class PruebasAdaptacion(unittest.TestCase):
    def setUp(self):
        self.conexion = MagicMock()
        self.cursor = self.conexion.cursor.return_value

    def empleado_con_cuenta(self):
        empleado = Empleado(None, 'Persona Prueba', 'Calle Prueba 100',
                                '912345678', 'prueba@example.com', '2026-01-01', 1000)
        servicio = Mock()
        servicio.cifrar.return_value = b'token-simulado'
        cuenta = CuentaUsuario('usuario_prueba', 'prueba@example.com', servicio, 'Prueba123!')
        empleado.asignar_cuenta(cuenta)
        return empleado

    def test_fallo_cuenta_revierte_toda_la_operacion(self):
        self.cursor.fetchone.return_value = {'id_empleado': 7}
        self.cursor.execute.side_effect = [None, Error('fallo simulado')]
        with self.assertRaises(Error):
            repo.agregar_empleado(self.conexion, self.empleado_con_cuenta())
        self.conexion.commit.assert_not_called()
        self.conexion.rollback.assert_not_called()
        salida = self.conexion.transaction.return_value.__exit__
        self.assertIs(salida.call_args.args[0], Error)
        self.cursor.close.assert_called_once()

    def test_id_postgresql_y_cifrado_fuera_del_historial(self):
        self.cursor.fetchone.side_effect = [
            {'id_empleado': 7},
            {'id_empleado': 7, 'nombre': 'Persona Prueba'},
            {'id_cuenta': 12, 'id_empleado': 7, 'nombre_usuario': 'usuario_prueba'}
        ]
        resultado = repo.agregar_empleado(self.conexion, self.empleado_con_cuenta())
        self.assertEqual(resultado, 7)
        self.conexion.commit.assert_not_called()
        self.conexion.rollback.assert_not_called()
        self.conexion.transaction.assert_called_once()
        self.conexion.transaction.return_value.__exit__.assert_called_once_with(None, None, None)
        consultas = self.cursor.execute.call_args_list
        self.assertIn('RETURNING id_empleado', consultas[0].args[0])
        historiales = [c for c in consultas if 'INSERT INTO historial_cambios' in c.args[0]]
        self.assertEqual(len(historiales), 2)
        self.assertNotIn('token-simulado', repr(historiales))
        self.assertNotIn('Prueba123!', repr(historiales))

    def test_tiempo_guarda_una_asignacion_con_sus_ids(self):
        tiempo = Tiempo('2026-01-10', 8, 'Tarea de prueba', 7, 3, False)
        with patch.object(repo, 'agregar_asignacion', return_value=15) as guardar:
            self.assertEqual(repo.guardar_tiempo(self.conexion, tiempo), 15)
        guardar.assert_called_once()
        datos = guardar.call_args.args[1].get_datos()
        self.assertEqual(datos['id_empleado'], 7)
        self.assertEqual(datos['id_proyecto'], 3)
        self.assertEqual(datos['horas_trabajadas'], 8)
        self.assertEqual(datos['fecha'], date(2026, 1, 10))

    def test_tiempo_invalido_no_llega_a_base(self):
        with patch.object(repo, 'agregar_asignacion') as guardar:
            for horas in (0, -2, 1.5):
                with self.subTest(horas=horas), self.assertRaises(ValueError):
                    repo.guardar_tiempo(self.conexion, Tiempo('2026-01-10', horas, 'Tarea', 7, 3, False))
            guardar.assert_not_called()

    def test_informe_no_duplica_horas_ni_inventa_departamento(self):
        empleado = self.empleado_con_cuenta()
        empleado._id_empleado = 7
        proyecto = Proyecto(3, 'Proyecto prueba', 'Descripcion', '2026-01-01', 'Equipo', 100)
        asignaciones = [Asignacion(1, '2026-01-10', 8, 'Tarea uno', 7, 3),
                        Asignacion(2, '2026-01-11', 3, 'Tarea dos', 7, 3)]
        salida = io.StringIO()
        with patch.object(ui, 'consultar_empleados', return_value=[empleado]), \
             patch.object(ui, 'consultar_proyectos', return_value=[proyecto]), \
             patch.object(ui, 'consultar_departamentos', return_value=[]), \
             patch.object(ui, 'consultar_asignaciones', return_value=asignaciones), \
             redirect_stdout(salida):
            ui.mostrar_informes_desde_supabase(self.conexion)
        texto = salida.getvalue()
        self.assertIn('Total de horas: 11', texto)
        self.assertEqual(texto.count('Tarea uno'), 1)
        self.assertEqual(texto.count('Tarea dos'), 1)
        seccion_tiempo = ui.Informes([empleado], [proyecto], [], asignaciones).obtener_secciones()[-1]
        self.assertNotIn('Departamento', seccion_tiempo[1])
        self.assertNotIn('horas registradas correctamente', texto)

    def test_busqueda_literal_y_parametrizada(self):
        texto = "50%_'; DROP TABLE empleado; --"
        self.cursor.fetchall.return_value = []
        repo.consultar_historial(self.conexion, texto=texto)
        sql, parametros = self.cursor.execute.call_args.args
        self.assertNotIn(texto, sql)
        self.assertIn('strpos', sql)
        self.assertEqual(parametros[:3], (texto, texto, texto))

    def test_conexion_requiere_ssl(self):
        with patch.object(db.psycopg, 'connect') as conectar:
            db.conectar_supabase('usuario_prueba', 'contrasena-ficticia', 'host.invalid')
        self.assertEqual(conectar.call_args.kwargs['sslmode'], 'require')
        self.assertTrue(conectar.call_args.kwargs['autocommit'])
        self.assertIn('ecotech', conectar.call_args.kwargs['options'])


if __name__ == '__main__':
    unittest.main()
