#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Crea el logger para la app
Elige el directorio de almacenamiento en función del SO
TODO: Externalizarlo como un submódulo
"""

import logging
import os, sys
from pathlib import Path

def get_log_file(log_filename: str):
  app_name = "maya_signer"

  # Obtengo el directorio donde lo voy a guardar en función del SO
  # Linux
  if sys.platform.startswith("linux"):
    log_dir = Path("/var/log") / app_name
    if not os.access("/var/log", os.W_OK):
      # Si falla (no es root) lo hacemos en local
      log_dir = Path.home() / ".local" / "state" / app_name

  # Windows
  elif sys.platform.startswith("win"):  
    appdata = os.environ.get("APPDATA", Path.home())
    log_dir = Path(appdata) / "MayaSigner"

  # macOS
  elif sys.platform == "darwin":
    log_dir = Path.home() / "Library" / "Logs" / "MayaSigner"

  else:
    # solución genérica
    log_dir = Path.home() / f".{app_name}"

  log_dir.mkdir(parents=True, exist_ok=True)

  return log_dir / log_filename

def setup_logger(log_filename: str, context: str):
    """
    Configura el logger
    """
    log_file = get_log_file(log_filename)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(context)
    logger.setLevel(logging.INFO)
    logger.propagate = False 

    # Evita duplicados si se importa varias veces
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )

    # Archivo
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # Consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
