# Detección de sistema operativo
ifeq ($(OS),Windows_NT)
    PLATFORM := windows
    PACKAGE_EXT := msi
else
    UNAME_S := $(shell uname -s)
    ifeq ($(UNAME_S),Linux)
        PLATFORM := linux
        PACKAGE_EXT := deb
    endif
    ifeq ($(UNAME_S),Darwin)
        PLATFORM := macos
        PACKAGE_EXT := dmg
    endif
endif

# Leer versión desde version.py
VERSION := $(shell python3 -c "from manifest import __version__; print(__version__)")
PACKAGE := maya-signer_$(VERSION)_amd64.deb
PACKAGE_WINDOWS := maya-signer_$(VERSION)_x64.msi

.PHONY: help clean build-deb install-deb test-deb build-msi install-msi test-msi uninstall

help:
	@echo "Maya Signer v$(VERSION) - Build System (Linux)"
	@echo ""
	@echo "Comandos disponibles:"
ifeq ($(PLATFORM),linux)
	@echo "  make build-deb      - Crea el paquete .deb"
	@echo "  make install-deb    - Instala el paquete .deb"
	@echo "  make test-deb       - Prueba el paquete"
	@echo "  make uninstall-deb  - Desinstala el paquete"
endif
ifeq ($(PLATFORM),windows)
	@echo "  make build-msi      - Crea el instalador .msi (Windows)"
	@echo "  make install-msi    - Instala el .msi"
	@echo "  make test-msi       - Prueba el instalador .msi"
endif
	@echo "  make clean          - Limpia archivos generados"
	

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

test-deb:
	@echo "Probando instalación..."
	@maya-signer --help || echo "Error: comando no encontrado"
	@echo ""
	@echo "Probando protocolo..."
	@xdg-mime query default x-scheme-handler/maya
	@echo ""
	@echo "Archivos instalados:"
	@dpkg -L maya-signer | head -20

uninstall-deb:
	@echo "Desinstalando Maya Signer..."
	sudo apt remove maya-signer
	@echo ">> Desinstalado <<"

build-msi:
	@echo "Construyendo instalador MSI para Windows..."
	cd build && python build_msi.py
	@echo "✓ MSI construido"

install-msi: build-msi
	@echo "Instalando MSI..."
	msiexec /i $(PACKAGE_WINDOWS) /qb
	@echo "✓ Instalado"

test-windows:
	@echo "Probando instalación..."
	@where maya-signer.exe
	@echo ""
	@echo "Probando protocolo..."
	@reg query "HKCR\maya"