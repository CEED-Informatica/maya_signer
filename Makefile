# Leer versión desde version.py
VERSION := $(shell python3 -c "from manifest import __version__; print(__version__)")
PACKAGE := maya-signer_$(VERSION)_amd64.deb

.PHONY: help clean build-deb install-deb test uninstall

help:
	@echo "Maya Signer v$(VERSION) - Build System (Linux)"
	@echo ""
	@echo "Comandos disponibles:"
	@echo "  make build-deb    - Crea el paquete .deb"
	@echo "  make install-deb  - Instala el paquete .deb"
	@echo "  make test         - Prueba el paquete"
	@echo "  make clean        - Limpia archivos generados"
	@echo "  make uninstall    - Desinstala el paquete"

clean:
	@echo "Limpiando archivos generados..."
	rm -rf build/dist build/build
	rm -rf maya-signer_*
	rm -f *.deb
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo ">> Limpieza completada <<"

build-deb: clean
	@echo "Construyendo paquete .deb..."
	cd build && python3 build_deb.py
	@echo ">> Paquete construido <<"

install-deb: build-deb
	@echo "Instalando paquete..."
	sudo dpkg -i $(PACKAGE)
	sudo apt-get install -f -y
	@echo ">> Paquete instalado <<"

test:
	@echo "Probando instalación..."
	@maya-signer --help || echo "Error: comando no encontrado"
	@echo ""
	@echo "Probando protocolo..."
	@xdg-mime query default x-scheme-handler/maya
	@echo ""
	@echo "Archivos instalados:"
	@dpkg -L maya-signer | head -20

uninstall:
	@echo "Desinstalando Maya Signer..."
	sudo apt remove maya-signer
	@echo ">> Desinstalado <<"
