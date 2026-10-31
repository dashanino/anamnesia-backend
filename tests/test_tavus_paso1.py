"""Pruebas locales con SQLite y HTTP simulado; no consumen Tavus."""
import json
import os
import unittest
from unittest.mock import patch

# La aplicación instancia Config y el controlador al importar las rutas.
# Todas las credenciales son ficticias y toda salida HTTP queda bloqueada.
os.environ.update({
    "DATABASE_URL": "sqlite:///:memory:",
    "JWT_SECRET_KEY": "solo-pruebas-locales",
    "TAVUS_API_KEY": "clave-ficticia-de-prueba",
    "TAVUS_PAL_ID": "pal-ficticio",
    "TAVUS_TEST_MODE": "true",
    "TAVUS_FACE_ID": "",
})

import requests
from app import create_app
from app.extensions import db
from app.models.simulacion import Simulacion
from app.routes.tavus_route import controller
from app.services.tavus_service import TavusService


def response(data=None, status=200):
    result = requests.Response()
    result.status_code = status
    result.url = "https://tavusapi.com/v2/conversations"
    result._content = json.dumps(data or {}).encode()
    return result


class TavusPaso1Tests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {
            "TAVUS_TEST_MODE": "true", "TAVUS_FACE_ID": "",
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        guard = patch(
            "requests.sessions.Session.request",
            side_effect=AssertionError("La prueba intentó una petición HTTP real"),
        )
        guard.start()
        self.addCleanup(guard.stop)
        self.app = create_app()
        self.app.config["TESTING"] = True
        context = self.app.app_context()
        context.push()
        self.addCleanup(context.pop)
        db.create_all()
        self.addCleanup(db.session.remove)
        service = patch.object(controller, "service", TavusService())
        service.start()
        self.addCleanup(service.stop)
        self.client = self.app.test_client()
        http = patch("requests.post", return_value=response({
            "conversation_id": "c-local",
            "conversation_url": "https://tavus.daily.co/c-local",
            "status": "ended",
        }))
        self.post = http.start()
        self.addCleanup(http.stop)

    def live(self):
        os.environ["TAVUS_TEST_MODE"] = "false"
        controller.service = TavusService()
        self.post.return_value = response({
            "conversation_id": "c-local",
            "conversation_url": "https://tavus.daily.co/c-local",
            "status": "active",
        })

    def create(self):
        return self.client.post("/api/tavus/conversation", json={})

    def end(self):
        return self.client.post("/api/tavus/conversation/c-local/finalizar")

    def test_default_test_mode_is_ended_and_visible(self):
        result = self.create()
        self.assertEqual(result.status_code, 201)
        self.assertIs(result.json["test_mode"], True)
        self.assertEqual(result.json["status"], "ended")
        self.assertEqual(Simulacion.query.one().estado, "finalizada")
        self.assertIs(self.post.call_args.kwargs["json"]["test_mode"], True)

    def test_live_mode_reaches_tavus_payload(self):
        self.live()
        result = self.create()
        self.assertEqual(result.status_code, 201)
        self.assertIs(self.post.call_args.kwargs["json"]["test_mode"], False)
        self.assertEqual(Simulacion.query.one().estado, "creada")

    def test_live_context_contains_the_persisted_case(self):
        self.live()
        result = self.create()
        record = Simulacion.query.one()
        payload = self.post.call_args.kwargs["json"]
        self.assertIn(record.caso_id, payload["conversational_context"])
        self.assertNotIn("caso_clinico", result.json)
        self.assertNotIn("conversational_context", result.json)
        self.assertNotIn("clave-ficticia-de-prueba", json.dumps(result.json))

    def test_face_is_omitted_when_the_pal_provides_it(self):
        self.create()
        self.assertNotIn("face_id", self.post.call_args.kwargs["json"])

    def test_face_override_reaches_payload(self):
        os.environ["TAVUS_FACE_ID"] = "  face-ficticia  "
        controller.service = TavusService()
        self.create()
        self.assertEqual(self.post.call_args.kwargs["json"]["face_id"], "face-ficticia")

    def test_invalid_boolean_is_rejected(self):
        os.environ["TAVUS_TEST_MODE"] = "tru"
        with self.assertRaisesRegex(ValueError, "true o false"):
            TavusService()
        self.post.assert_not_called()

    def test_end_uses_post_end_and_preserves_the_record(self):
        self.live()
        self.create()
        self.post.reset_mock()
        self.post.return_value = response(status=204)
        with patch("requests.delete") as delete:
            result = self.end()
        self.assertEqual(result.status_code, 200)
        self.post.assert_called_once_with(
            "https://tavusapi.com/v2/conversations/c-local/end",
            headers={"x-api-key": "clave-ficticia-de-prueba"}, timeout=30,
        )
        delete.assert_not_called()
        self.assertEqual(Simulacion.query.one().estado, "finalizada")

    def test_end_failure_keeps_the_session_open(self):
        self.live()
        self.create()
        self.post.return_value = response({"error": "denegado"}, status=403)
        result = self.end()
        self.assertEqual(result.status_code, 502)
        self.assertEqual(result.json["tavus_status"], 403)
        self.assertEqual(Simulacion.query.one().estado, "creada")

    def test_ending_an_ended_test_does_not_call_tavus_again(self):
        self.create()
        self.post.reset_mock()
        self.assertEqual(self.end().status_code, 200)
        self.post.assert_not_called()

    def test_upstream_401_is_reported_without_credentials(self):
        self.post.return_value = response({"error": "Invalid access token"}, status=401)
        result = self.create()
        self.assertEqual(result.status_code, 502)
        self.assertEqual(result.json["tavus_status"], 401)
        self.assertNotIn("clave-ficticia-de-prueba", json.dumps(result.json))
        self.assertEqual(Simulacion.query.count(), 0)

    def test_network_failure_does_not_persist_a_simulation(self):
        self.post.side_effect = requests.ConnectionError("conexión simulada fallida")
        self.assertEqual(self.create().status_code, 502)
        self.assertEqual(Simulacion.query.count(), 0)

    def test_database_failure_attempts_to_end_the_live_room(self):
        self.live()
        with patch.object(db.session, "commit", side_effect=RuntimeError("DB simulada fallida")):
            with self.assertLogs(self.app.logger, level="ERROR"):
                result = self.create()
        self.assertEqual(result.status_code, 500)
        self.assertEqual(self.post.call_count, 2)
        self.assertEqual(
            self.post.call_args.args[0],
            "https://tavusapi.com/v2/conversations/c-local/end",
        )
        self.assertEqual(Simulacion.query.count(), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
