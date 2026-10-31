"""Diagnóstico de solo lectura con Tavus simulado."""
import unittest
from unittest.mock import patch
import test_tavus_paso1 as base
from test_tavus_paso1 import response, Simulacion, controller


class TavusDiagnosticoTests(unittest.TestCase):
    setUp = base.TavusPaso1Tests.setUp
    create = base.TavusPaso1Tests.create

    def diagnostic(self):
        return self.client.get('/api/tavus/conversation/c-local/diagnostico')

    def test_diagnostic_extracts_shutdown_without_exposing_private_events(self):
        self.create()
        before = Simulacion.query.one().estado
        self.post.reset_mock()
        data = {
            'conversation_id': 'c-local', 'status': 'ended',
            'pal_id': 'pal-ficticio', 'face_id': 'face-ficticia',
            'meeting_token': 'TOKEN_QUE_NO_DEBE_SALIR',
            'events': [
                {'event_type': 'system.pal_joined', 'timestamp': '2026-10-22T10:00:00Z'},
                {'event_type': 'application.transcription_ready',
                 'properties': {'transcript': ['HISTORIA_QUE_NO_DEBE_SALIR']}},
                {'event_type': 'system.shutdown', 'timestamp': '2026-10-22T10:05:00Z',
                 'properties': {'shutdown_reason': 'participant_absent_timeout'}},
            ]
        }
        with patch('requests.get', return_value=response(data)) as get:
            result = self.diagnostic()
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json['shutdown_reason'], 'participant_absent_timeout')
        self.assertEqual(len(result.json['eventos_sistema']), 2)
        self.assertNotIn('TOKEN_QUE_NO_DEBE_SALIR', result.get_data(as_text=True))
        self.assertNotIn('HISTORIA_QUE_NO_DEBE_SALIR', result.get_data(as_text=True))
        self.assertEqual(Simulacion.query.one().estado, before)
        self.post.assert_not_called()
        get.assert_called_once_with(
            'https://tavusapi.com/v2/conversations/c-local',
            params={'verbose': 'true'},
            headers={'x-api-key': 'clave-ficticia-de-prueba'}, timeout=30,
        )

    def test_diagnostic_unknown_local_id_does_not_contact_tavus(self):
        with patch('requests.get') as get:
            self.assertEqual(self.diagnostic().status_code, 404)
        get.assert_not_called()

    def test_diagnostic_preserves_null_when_reason_not_available(self):
        self.create()
        with patch('requests.get', return_value=response({'status': 'active', 'events': None})):
            result = self.diagnostic()
        self.assertEqual(result.status_code, 200)
        self.assertIsNone(result.json['shutdown_reason'])
        self.assertEqual(result.json['eventos_sistema'], [])

    def test_diagnostic_rejection_has_upstream_status(self):
        self.create()
        with patch('requests.get', return_value=response({'error': 'not found'}, status=404)):
            result = self.diagnostic()
        self.assertEqual(result.status_code, 502)
        self.assertEqual(result.json['tavus_status'], 404)
