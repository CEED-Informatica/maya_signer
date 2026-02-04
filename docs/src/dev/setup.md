# Configuración entorno

## Instalación código

```bash
# clonar el repò
git clone git@github.com:Maya-AQSS/maya-signer.git

cd maya-signer
python -m venv .venv
source .venv/bin/activate                                               

# Instalar dependencias de desarrollo
pip install -r requirements.txt
```

## Ejecución debug

El fichero principal de ejecución es `main.py`

Desde _vscode_ hay habilitados dos configuraciones de desarrollo:

```json
  {
    "name": "Python Debugger: sin url",
    
  },
  {
    "name": "Python Debugger: con url",
    "args": ["maya://sign?batch=158&token=p6FTJFJ3X_ovILXl8zIF0JAYf4v9K2c7pj--9dfbI44&url=http://localhost:8069&db=CEED_TEST_2526"],
  }
```

## Instalación protocolo `maya://`

Es posible instalar el protocolo mendiante el uso de parámetros del fichero `main.py`

 ```bash
# instalación
maya-signer.py --install-protocol

# desinstalación
maya-signer.py --uninstall-protocol
```
