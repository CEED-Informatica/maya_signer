"""
Levanta el servicio HTTP real en un puerto de test y verifica
que el cliente puede comunicarse con él correctamente.
"""

import json
import time
import threading
import pytest
import requests
from unittest.mock import patch, MagicMock
from http.server import HTTPServer

from src.maya_signer_service import MayaServiceHandler, MayaSignerService


TEST_PORT = 50399  # Puerto diferente al de producción

class FakeMayaSignerService:
  """
  Simula el servicio sin necesidad de Qt
  """
  def __init__(self):
    self.credentials_store = {}
    self.signals = MagicMock()
    self.quit_action = MagicMock()
    self.tray_icon = MagicMock()
    self.status_action = MagicMock()

  def get_credentials(self, url):
    return self.credentials_store.get(url)

  def store_credentials(self, url, **kwargs):
    self.credentials_store[url] = kwargs

  def process_signature(self, data, credentials):
    # En integración no firmamos realmente
    pass

  def update_progress_ui(self, msg):
    pass


@pytest.fixture
def test_service():
  """
  Levanta un servidor HTTP real en un puerto de test
  """
  service = FakeMayaSignerService()

  server = HTTPServer(("127.0.0.1", TEST_PORT), MayaServiceHandler)
  server.maya_signer_service = service

  # Arrancar en thread
  thread = threading.Thread(target=server.serve_forever, daemon=True)
  thread.start()

  # Esperar a que esté listo
  time.sleep(0.2)

  yield service, server

  server.shutdown()


class TestClienteServicioIntegración:

  @pytest.mark.integration
  def test_health_check_retorna_200(self, test_service):
    """
    El endpoint /health responde correctamente
    """
    _, _ = test_service
    response = requests.get(f"http://127.0.0.1:{TEST_PORT}/health", timeout=2)

    assert response.status_code == 200
    assert response.json() == {"status": "running"}

  @patch.object(FakeMayaSignerService, "process_signature")
  @pytest.mark.integration
  def test_petición_con_credenciales_almacenadas(self, mock_process, test_service):
    """
    Si hay credenciales en memoria, retorna 200 y lanza firma
    """
    service, _ = test_service

    # Pre-almacenar credenciales
    service.credentials_store["https://maya.example.com"] = {
      "username": "user@test.com",
      "password": "pass",
      "cert_password": "cert",
      "use_dnie": False,
      "cert_path": "/cert.p12"
    }

    response = requests.post(
      f"http://127.0.0.1:{TEST_PORT}",
      json={
          "batch": 1,
          "url": "https://maya.example.com",
          "database": "testdb",
          "token": "tok123"
      },
      timeout=5
    )

    assert response.status_code == 200
    assert response.json()["status"] == "processing"

    # Esperar un momento para que el thread se lance
    time.sleep(0.3)
    mock_process.assert_called_once()

  @pytest.mark.integration
  def test_petición_sin_credenciales_y_usuario_cancela(self, test_service):
    """
    Si no hay credenciales y el usuario cancela, retorna 499
    """
    service, _ = test_service

    # Simular que el usuario cancela inmediatamente
    def simular_cancelación(url, db):
      service.credentials_store[url] = "CANCELLED"

    service.signals.show_credentials_dialog.connect = MagicMock()
    service.signals.show_credentials_dialog.emit = simular_cancelación

    response = requests.post(
      f"http://127.0.0.1:{TEST_PORT}",
      json={
          "batch": 1,
          "url": "https://maya.example.com",
          "database": "testdb",
          "token": "tok123"
      },
      timeout=5
    )

    assert response.status_code == 499
    assert response.json()["error"] == "user_cancelled"

    # Verificar que se limpia el marcador de cancelación
    assert "https://maya.example.com" not in service.credentials_store

  @pytest.mark.integration
  def test_petición_malformada_retorna_500(self, test_service):
    """
    Un POST con datos inválidos retorna 500
    """
    _, _ = test_service

    response = requests.post(
        f"http://127.0.0.1:{TEST_PORT}",
        json={},  # Falta "url"
        timeout=5
    )

    assert response.status_code == 500
