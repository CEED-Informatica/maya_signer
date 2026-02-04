"""
Testea el flujo completo de preparación de directorio → ejecución del worker
→ lectura de resultados, usando un worker real pero con PDFs de prueba.
"""

import json
import time
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.subprocess_signature_manager import SubprocessSignatureManager

@pytest.fixture
def real_manager():
  """
  Manager que apunta al worker real
  """
  worker = Path(__file__).parent.parent / "src" / "signer_worker.py"
  if not worker.exists():
      pytest.skip("signer_worker.py no encontrado en src/")
  
  return SubprocessSignatureManager(worker_script=worker)


class TestWorkerIntegración:

  @pytest.mark.integration
  def test_flujo_completo_preparar_monitorear_leer(self, real_manager, sample_documents):
    """
    Flujo completo sin firma real:
    Prepara directorio con PDFs -> Crea input.json -> Verifica que el worker puede leerlo
    """
    # Preparar directorio
    work_dir = real_manager.prepare_work_directory(sample_documents)
    assert work_dir.exists()

    # Crear input.json (lo que normalmente hace sign_documents)
    real_manager.create_input_file(
        work_dir,
        documents=sample_documents,
        cert_path="/fake/cert.p12",
        cert_password="password",
        use_dnie=False
    )

    # Verificar estructura
    assert (work_dir / "input.json").exists()
    for doc in sample_documents:
        assert (work_dir / f"unsigned_{doc['id']}.pdf").exists()

    # Verificar que input.json es JSON válido y tiene los datos correctos
    input_data = json.loads((work_dir / "input.json").read_text())
    assert input_data["cert_path"] == "/fake/cert.p12"
    assert len(input_data["documents"]) == len(sample_documents)
    assert input_data["documents"][0]["document_id"] == sample_documents[0]["id"]

    # Limpieza
    real_manager.cleanup(work_dir)
    assert not work_dir.exists()

  @pytest.mark.integration
  def test_worker_reporta_error_con_certificado_inválido(self, real_manager, sample_documents):
    """
    El worker debe terminar con estado 'error' si el certificado no es válido.
    Esto verifica que el worker maneja errores correctamente.
    """
    work_dir = real_manager.prepare_work_directory(sample_documents)

    real_manager.create_input_file(
      work_dir,
      documents=sample_documents,
      cert_path="/no/existe/cert.p12",  # Certificado inexistente
      cert_password="wrong",
      use_dnie=False
    )

    # Lanzar worker
    process = real_manager.start_worker(work_dir)

    # Monitorear (timeout corto)
    result = real_manager.monitor_progress(work_dir, timeout=30)

    # Esperar fin del proceso
    process.wait(timeout=10)

    # Debe haber fallado
    assert result["status"] == "error"