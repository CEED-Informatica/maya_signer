import pytest
from unittest.mock import patch, MagicMock, PropertyMock

from src.odoo_client import OdooClient, OdooTokenError, OdooAuthenticationError
import xmlrpc.client

def make_client(batch_token="tok_valid"):
  """
  Crea un OdooClient con xmlrpc mockeado
  """
  # Reemplaza temporalmente la clase xmlrpc.client.ServerProxy 
  # (usada dentro de OdooClient para conectar a Odoo via XML-RPC) 
  # con un mock.
  with patch("src.odoo_client.xmlrpc.client.ServerProxy"):
    client = OdooClient(
        url="https://maya.example.com",
        db="testdb",
        username="user@test.com",
        password="pass",
        batch_token=batch_token
    )

  # Simular que ya está autenticado
  client.uid = 42

  return client

class TestValidateBatchToken:
  """
  Validación de token: respuestas válidas, inválidas y errores
  """

  def test_token_valido(self):
    """
    Un token válido retorna sin errores
    """
    client = make_client("tok_bueno")
    client.models = MagicMock()
    client.models.execute_kw.return_value = {"valid": True, "batch_name": "Lote 1"}

    result = client.validate_batch_token(42)

    assert result["valid"] is True
    assert result["batch_name"] == "Lote 1"

  def test_token_invalido_lanza_error(self):
    """
    Un token inválido (valid=False) lanza OdooTokenError
    """
    client = make_client("tok_malo")
    client.models = MagicMock()
    client.models.execute_kw.return_value = {
        "valid": False,
        "error": "Token expirado"
    }

    with pytest.raises(OdooTokenError, match="Token expirado"):
        client.validate_batch_token(42)

  def test_sin_token_configurado_lanza_error(self):
    """
    Si no hay token, lanza OdooTokenError inmediatamente
    """
    client = make_client(batch_token=None)

    with pytest.raises(OdooTokenError, match="No hay token"):
      client.validate_batch_token(42)

  def test_error_xmlrpc_se_convierte_en_token_error(self):
    """
    Errores inesperados del servidor se convierten en OdooTokenError
    """
    client = make_client("tok_x")
    client.models = MagicMock()
    client.models.execute_kw.side_effect = xmlrpc.client.Fault(
        1, "Server error"
    )

    with pytest.raises(OdooTokenError, match="Error validando token"):
      client.validate_batch_token(42)

