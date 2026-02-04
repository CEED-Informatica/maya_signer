from unittest.mock import patch, MagicMock

from src.main import parse_protocol_url, handle_protocol_call

class TestParseProtocolUrl:
  """
  Parsing correcto de URLs maya://
  Detección de parámetros que no existen
  """

  def test_parsea_url_completa(self):
    """
    Extrae todos los parámetros de una URL bien formada
    """
    url = "maya://sign?batch=42&url=https://maya.example.com&db=prod&token=tok123"
    result = parse_protocol_url(url)

    assert result["batch"] == "42"
    assert result["url"] == "https://maya.example.com"
    assert result["database"] == "prod"
    assert result["token"] == "tok123"

  def test_parsea_url_sin_database(self):
    """
    El parámetro db es opcional
    """
    url = "maya://sign?batch=1&url=https://test.com&token=abc"
    result = parse_protocol_url(url)

    assert result["batch"] == "1"
    assert result["url"] == "https://test.com"
    assert result["database"] == ""
    assert result["token"] == "abc"

  def test_parsea_url_con_caracteres_especiales(self):
    """
    URLs con caracteres especiales codificados se parsean correctamente
    """
    url = "maya://sign?batch=5&url=https%3A%2F%2Fmaya.test.com%3A8069&db=mi_base&token=x"
    result = parse_protocol_url(url)

    assert result["url"] == "https://maya.test.com:8069"
    assert result["database"] == "mi_base"


class TestHandleProtocolCall:

  @patch("src.main.send_signature_request")
  @patch("src.main.is_service_running", return_value=True)
  def test_envía_petición_si_servicio_corriendo(self, mock_running, mock_send):
      """
      Si el servicio está activo, envía la petición directamente
      """
      mock_send.return_value = True
      url = "maya://sign?batch=1&url=https://test.com&token=tok"

      result = handle_protocol_call(url)

      assert result == 0
      mock_send.assert_called_once()

  @patch("src.main.send_signature_request")
  @patch("src.main.start_service", return_value=True)
  @patch("src.main.is_service_running", return_value=False)
  def test_inicia_servicio_si_no_está_corriendo(self, mock_running, mock_start, mock_send):
      """
      Si el servicio no está activo, lo inicia antes de enviar
      """
      mock_send.return_value = True
      url = "maya://sign?batch=1&url=https://test.com&token=tok"

      result = handle_protocol_call(url)

      assert result == 0
      mock_start.assert_called_once()
      mock_send.assert_called_once()

  @patch("src.main.is_service_running", return_value=True)
  def test_falla_sin_batch(self, mock_running):
      """
      Sin parámetro batch retorna error
      """
      url = "maya://sign?url=https://test.com&token=tok"

      result = handle_protocol_call(url)

      assert result == 1

  @patch("src.main.is_service_running", return_value=True)
  def test_falla_sin_token(self, mock_running):
      """
      Sin parámetro token retorna error
      """
      url = "maya://sign?batch=1&url=https://test.com"

      result = handle_protocol_call(url)

      assert result == 1