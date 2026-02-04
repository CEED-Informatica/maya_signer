import pytest

import base64
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

class TestDownloadUnsignedPdfs:
  """
  Descarga de documentos
  """
  def _setup_client(self, documents_from_odoo):
    """
    Helper: prepara un client con batch info y documents mockeados
    """
    client = make_client()
    client.models = MagicMock()

    # validate_batch_token no falla
    client.models.execute_kw.side_effect = [
        # 1ª llamada: validate_session_token
        {"valid": True},
        # 2ª llamada: read del batch
        [{"name": "Lote 1", "document_ids": [1, 2, 3], "state": "draft"}],
        # 3ª llamada: read de los documentos
        documents_from_odoo
    ]
    return client

  def test_descarga_solo_documentos_no_firmados(self):
    """
    Ignora documentos con state='signed'
    """
    pdf_base64 = base64.b64encode(b"%PDF-1.4 content").decode()

    docs = [
      {"id": 1, "filename": "a.pdf", "state": "unsigned",
        "res_model": "account.move", "res_id": 10, "pdf_content": pdf_base64},
      {"id": 2, "filename": "b.pdf", "state": "signed",       # ← este se ignora
        "res_model": "account.move", "res_id": 11, "pdf_content": pdf_base64},
      {"id": 3, "filename": "c.pdf", "state": "unsigned",
        "res_model": "account.move", "res_id": 12, "pdf_content": pdf_base64},
    ]

    client = self._setup_client(docs)
    result = client.download_unsigned_pdfs(42)

    assert len(result) == 2
    assert all(doc["state"] == "unsigned" for doc in result)

  def test_decodifica_base64_correctamente(self):
    """
    El pdf_bytes del resultado es la decodificación correcta del base64
    """
    contenido_original = b"%PDF-1.4 contenido real del PDF"
    pdf_base64 = base64.b64encode(contenido_original).decode()

    docs = [
      {"id": 1, "filename": "a.pdf", "state": "unsigned",
        "res_model": "m", "res_id": 1, "pdf_content": pdf_base64},
    ]

    client = self._setup_client(docs)
    result = client.download_unsigned_pdfs(42)

    assert result[0]["pdf_bytes"] == contenido_original

  def test_ignora_documentos_sin_contenido_pdf(self):
    """
    Documentos con pdf_content vacío o None se saltan
    """
    pdf_base64 = base64.b64encode(b"content").decode()

    docs = [
      {"id": 1, "filename": "a.pdf", "state": "unsigned",
        "res_model": "m", "res_id": 1, "pdf_content": pdf_base64},
      {"id": 2, "filename": "b.pdf", "state": "unsigned",
        "res_model": "m", "res_id": 2, "pdf_content": None},     # ← se ignora
      {"id": 3, "filename": "c.pdf", "state": "unsigned",
        "res_model": "m", "res_id": 3, "pdf_content": ""},       # ← se ignora
    ]

    client = self._setup_client(docs)
    result = client.download_unsigned_pdfs(42)

    assert len(result) == 1
    assert result[0]["id"] == 1

  def test_base64_invalido_no_crashea(self):
    """
    Un pdf_content con base64 inválido se ignora sin crashear
    """
    docs = [
      {"id": 1, "filename": "bueno.pdf", "state": "unsigned",
        "res_model": "m", "res_id": 1,
        "pdf_content": base64.b64encode(b"ok").decode()},
      {"id": 2, "filename": "malo.pdf", "state": "unsigned",
        "res_model": "m", "res_id": 2,
        "pdf_content": "esto_no_es_base64_válido!!!"},
    ]

    client = self._setup_client(docs)
    result = client.download_unsigned_pdfs(42)

    # Solo el bueno debe pasar
    assert len(result) == 1
    assert result[0]["id"] == 1