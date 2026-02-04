import pytest

import sys
from pathlib import Path

# También añadir src/ al path para que funcionen imports como:
# from custom_logging import setup_logger
src_path = Path(__file__).parent.parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

@pytest.fixture
def sample_documents():
  """
  Lista de documentos como los devuelve Odoo
  """
  return [
    {
        "id": 1,
        "filename": "factura_001.pdf",
        "state": "unsigned",
        "res_model": "account.move",
        "res_id": 100,
        "pdf_content": "JVBERi0xLjQK",  # Base64 de un PDF mínimo
        "pdf_bytes": b"%PDF-1.4 fake content 1"
    },
    {
        "id": 2,
        "filename": "factura_002.pdf",
        "state": "unsigned",
        "res_model": "account.move",
        "res_id": 101,
        "pdf_content": "JVBERi0xLjQK",
        "pdf_bytes": b"%PDF-1.4 fake content 2"
    }
  ]

@pytest.fixture
def work_dir(tmp_path):
  """
  Directorio temporal de trabajo para tests
  """
  d = tmp_path / "maya_signer_test"
  d.mkdir()
  return d
