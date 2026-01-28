# Detección de sistema operativo
ifeq ($(OS),Windows_NT)
    PLATFORM := windows
    PACKAGE_EXT := msi
    PYTHON := python
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
    PYTHON := python3
endif

# Leer versión desde version.py
VERSION := $(shell python3 -c "from manifest import __version__; print(__version__)")

# Nombres de paquetes
PACKAGE := maya-signer_$(VERSION)_amd64.deb
PACKAGE_WINDOWS := maya-signer_$(VERSION)_x64.msi
PACKAGE_MACOS := maya-signer_$(VERSION)_macOS.dmg

.PHONY: help clean build install test

help:
	@echo "============================================================"
	@echo "Maya Signer v$(VERSION) - Build System"
	@echo "============================================================"
	@echo "Plataforma detectada: $(PLATFORM)"
	@echo ""
	@echo "Comandos disponibles:"
	@echo "  make build        - Compila el paquete para esta plataforma"
	@echo "  make install      - Instala el paquete"
	@echo "  make test         - Prueba la instalación"
	@echo "  make clean        - Limpia archivos generados"
	@echo ""
	@echo "Comandos específicos:"
ifeq ($(PLATFORM),linux)
	@echo "  make build-deb    - Crea el paquete .deb"
	@echo "  make install-deb  - Instala el .deb"
endif
ifeq ($(PLATFORM),windows)
	@echo "  make build-msi    - Crea el instalador .msi"
	@echo "  make install-msi  - Instala el .msi"
endif
ifeq ($(PLATFORM),macos)
	@echo "  make build-dmg    - Crea el instalador .dmg"
	@echo "  make install-dmg  - Monta el .dmg"
endif

clean:
	@echo "Limpiando archivos generados..."
	rm -rf build/dist build/build
	rm -rf maya-signer_*
	rm -f *.deb *.msi *.dmg
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo ">> Limpieza completada <<"

# Linux
build-deb:
	@echo "Construyendo paquete .deb para Linux..."
	cd build && $(PYTHON) build_deb.py
	@echo "✓ .deb construido"

install-deb: build-deb
	@echo "Instalando paquete .deb..."
	sudo dpkg -i $(PACKAGE_LINUX)
	sudo apt-get install -f -y
	@echo "✓ Instalado"

# Windows
build-msi:
	@echo "Construyendo instalador .msi para Windows..."
	cd build && $(PYTHON) build_msi.py
	@echo "✓ .msi construido"

install-msi: build-msi
	@echo "Instalando .msi..."
	msiexec /i $(PACKAGE_WINDOWS) /qb
	@echo "✓ Instalado"

# macOS
build-dmg:
	@echo "Construyendo instalador .dmg para macOS..."
	cd build && $(PYTHON) build_dmg.py
	@echo "✓ .dmg construido"

install-dmg: build-dmg
	@echo "Montando DMG..."
	@hdiutil attach $(PACKAGE_MACOS)
	@echo ""
	@echo "✓ DMG montado. Arrastra MayaSigner.app a Applications"
	@echo "Presiona Enter cuando termines para desmontar..."
	@read line
	@hdiutil detach /Volumes/Maya\ Signer\ $(VERSION)

# Comandos genéricos que se adaptan a la plataforma
build:
ifeq ($(PLATFORM),linux)
	@$(MAKE) build-deb
endif
ifeq ($(PLATFORM),windows)
	@$(MAKE) build-msi
endif
ifeq ($(PLATFORM),macos)
	@$(MAKE) build-dmg
endif

install:
ifeq ($(PLATFORM),linux)
	@$(MAKE) install-deb
endif
ifeq ($(PLATFORM),windows)
	@$(MAKE) install-msi
endif
ifeq ($(PLATFORM),macos)
	@$(MAKE) install-dmg
endif

test:
	@echo "Probando instalación en $(PLATFORM)..."
ifeq ($(PLATFORM),linux)
	@maya-signer --help || echo "❌ Error: comando no encontrado"
	@xdg-mime query default x-scheme-handler/maya
endif
ifeq ($(PLATFORM),windows)
	@where maya-signer.exe
	@reg query "HKCR\maya"
endif
ifeq ($(PLATFORM),macos)
	@which maya-signer || echo "Buscar en /Applications/MayaSigner.app"
	@defaults read com.apple.LaunchServices/com.apple.launchservices.secure LSHandlers | grep maya || echo "Protocolo no registrado aún"
endif

uninstall:
	@echo "Desinstalando Maya Signer..."
ifeq ($(PLATFORM),linux)
	sudo apt remove maya-signer
endif
ifeq ($(PLATFORM),windows)
	msiexec /x $(PACKAGE_WINDOWS) /quiet
endif
ifeq ($(PLATFORM),macos)
	rm -rf /Applications/MayaSigner.app
	rm -rf ~/.maya_signer
endif
	@echo "✓ Desinstalado"