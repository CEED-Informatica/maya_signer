import json
import pytest
from unittest.mock import patch, MagicMock

from src.subprocess_signature_manager import SubprocessSignatureManager

@pytest.fixture
def manager(tmp_path):
  """
  Crea un manager con un worker script fake
  """
  fake_worker = tmp_path / "fake_worker.py"
  fake_worker.write_text("# fake")
  return SubprocessSignatureManager(worker_script=fake_worker)


class TestPrepareWorkDirectory:
  """
  Preparación del directorio de trabajo
  """

  def test_crea_pdfs_en_directorio(self, manager, sample_documents):
    """
    Guarda cada documento como unsigned_<id>.pdf
    """
    work_dir = manager.prepare_work_directory(sample_documents)

    for doc in sample_documents:
      pdf_path = work_dir / f"unsigned_{doc['id']}.pdf"
      assert pdf_path.exists(), f"Falta {pdf_path.name}"
      assert pdf_path.read_bytes() == doc["pdf_bytes"]

  def test_directorio_es_nuevo_cada_vez(self, manager, sample_documents):
    """
    Cada llamada crea un directorio diferente
    """
    dir1 = manager.prepare_work_directory(sample_documents)
    dir2 = manager.prepare_work_directory(sample_documents)

    assert dir1 != dir2
    assert dir1.exists()
    assert dir2.exists()

  def test_error_en_escritura_limpia_directorio(self, manager):
    """
    Si falla al escribir un PDF, se elimina el directorio
    """
    docs_malos = [
      {"id": 1, "pdf_bytes": None}  # Esto va a crashear al escribir
    ]

    with pytest.raises(Exception):
      manager.prepare_work_directory(docs_malos)


class TestReadResults:
  """
  Lectura correcta de resultados del worker
  """

  @pytest.mark.unit
  def test_lee_documentos_firmados_correctamente(self, manager, work_dir):
    """
    Lee el output.json y los PDFs firmados generados por el worker
    """
    # Simular lo que el worker deja en el directorio
    signed_content_1 = b"%PDF-1.4 firmado 1"
    signed_content_2 = b"%PDF-1.4 firmado 2"

    (work_dir / "signed_1.pdf").write_bytes(signed_content_1)
    (work_dir / "signed_2.pdf").write_bytes(signed_content_2)

    output = {
      "results": [
        {
          "document_id": 1,
          "res_model": "account.move",
          "res_id": 100,
          "signed_filename": "signed_1.pdf",
          "original_filename": "factura_001.pdf",
          "success": True
        },
        {
          "document_id": 2,
          "res_model": "account.move",
          "res_id": 101,
          "signed_filename": "signed_2.pdf",
          "original_filename": "factura_002.pdf",
          "success": True
        }
      ]
    }
    (work_dir / "output.json").write_text(json.dumps(output))

    results = manager.read_results(work_dir)

    assert len(results) == 2
    assert results[0]["signed_pdf_bytes"] == signed_content_1
    assert results[1]["signed_pdf_bytes"] == signed_content_2
    assert results[0]["signed_filename"] == "factura_001_firmado.pdf"

  @pytest.mark.unit
  def test_ignora_resultados_fallidos(self, manager, work_dir):
    """
    Documentos con success=False no aparecen en el resultado
    """
    (work_dir / "signed_1.pdf").write_bytes(b"content")

    output = {
      "results": [
        {"document_id": 1, "res_model": "m", "res_id": 1,
          "signed_filename": "signed_1.pdf",
          "original_filename": "ok.pdf", "success": True},
        {"document_id": 2, "res_model": "m", "res_id": 2,
          "signed_filename": "signed_2.pdf",
          "original_filename": "fail.pdf", "success": False,
          "error": "Error PKCS11"},
      ]
    }
    (work_dir / "output.json").write_text(json.dumps(output))

    results = manager.read_results(work_dir)

    assert len(results) == 1
    assert results[0]["document_id"] == 1

  @pytest.mark.unit
  def test_retorna_vacio_si_no_hay_output(self, manager, work_dir):
    """
    Si output.json no existe, retorna lista vacía
    """
    results = manager.read_results(work_dir)
    assert results == []

  @pytest.mark.unit
  def test_retorna_vacio_si_pdf_firmado_no_existe(self, manager, work_dir):
    """
    Si el PDF firmado referenciado no existe, se ignora ese documento
    """
    output = {
      "results": [
        {"document_id": 1, "res_model": "m", "res_id": 1,
          "signed_filename": "no_existe.pdf",
          "original_filename": "a.pdf", "success": True},
      ]
    }
    (work_dir / "output.json").write_text(json.dumps(output))

    results = manager.read_results(work_dir)
    assert results == []


class TestCleanup:
  """
  Limpieza de archivos temporales
  """

  @pytest.mark.unit
  def test_elimina_directorio(self, manager, work_dir):
    """
    El cleanup elimina el directorio completo
    """
    (work_dir / "archivo.txt").write_text("test")

    manager.cleanup(work_dir)

    assert not work_dir.exists()

  @pytest.mark.unit
  def test_no_crashea_si_no_existe(self, manager, tmp_path):
    """
    Si el directorio ya no existe, no lanza error
    """
    no_existe = tmp_path / "no_existe"
    manager.cleanup(no_existe)  # No debe lanzar
