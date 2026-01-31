# Visión General del Desarrollo

## Tecnologías Utilizadas

**Core**
| Tecnología | Versión | Uso | 
| ---------- | -------- | --- |
| Python     | 3.8+     | Lenguaje principal | 
| PySide6    | 6.5+     | Interfaz gráfica (Qt6) |
| pyHanko    | 0.20+    | Firma de PDFs |
| cryptography | 41+    | Gestión de certificados |

**Empaquetado**

| Herramienta | Plataforma | Uso |
| ----------  | ---------- | --- | 
| PyInstaller | Todas      | Compilación de ejecutables |
| dpkg-deb    | Linux      | Creación de .deb |
| WiX Toolset | Windows    | Creación de .msi |
| create-dmg  | macOS      | Creación de .dmg |

**CI/CD**

* GitHub Actions: Compilación automática
* GitHub Releases: Distribución de instaladores
* GitHub Pages: Documentación (VitePress)

**Arquitectura del Sistema**

<center>

```mermaid
graph TB
    subgraph "Cliente Web (Maya/Odoo)"
        A[Interfaz Web]
    end
    
    subgraph "Escritorio del Usuario"
        B[Navegador]
        C[Protocolo maya://]
        D[main.py]
        E[maya_signer_service.py]
        F[signer_worker.py]
        G[Bandeja del Sistema]
    end
    
    subgraph "Backend Maya"
        H[API XML-RPC]
        I[Base de Datos]
    end
    
    A -->|Click Firmar| B
    B -->|Lanza| C
    C -->|Ejecuta| D
    D -->|Comunica con| E
    E -->|Muestra diálogo| G
    E -->|Solicita firma| F
    F -->|Firma PDF| F
    E -->|Descarga/Sube| H
    H -->|Almacena| I
  ```

</center>

## Componentes Principales

### 1. Cliente (`main.py`)

**Responsabilidad**: Punto de entrada del protocolo `maya://`

- Parsea URLs del protocolo
- Verifica que el servicio está corriendo
- Inicia el servicio si es necesario
- Envía peticiones al servicio

### 2. Servicio (`maya_signer_service.py`)

**Responsabilidad**: Servidor HTTP local que gestiona firmas

- Corre en background (puerto 50304)
- Gestiona credenciales en memoria
- Muestra diálogos de credenciales
- Coordina el proceso de firma
- Notifica el estado al usuario

### 3. Worker (`signer_worker.py`)

**Responsabilidad**: Proceso aislado que ejecuta la firma

- Se ejecuta como subproceso separado
- Sin acceso a Qt ni threading
- Usa pyHanko para firmar PDFs
- Comunica vía archivos JSON

### 4. Cliente Odoo (`odoo_client.py`)

**Responsabilidad**: Comunicación con Maya/Odoo

- Cliente XML-RPC
- Autenticación
- Descarga de PDFs
- Subida de PDFs firmados
- Validación de tokens

### 5. Gestor de Firmas (`subprocess_signature_manager.py`)

**Responsabilidad**: Coordina workers de firma

- Prepara directorios temporales
- Lanza workers
- Monitorea progreso
- Limpia archivos temporales

### 6. Firmador (`hanko_signer.py`)

**Responsabilidad**: Wrapper de pyHanko

- Carga certificados .p12/.pfx
- Configura DNIe (PKCS#11)
- Ejecuta firma de PDFs
- Gestiona cierre de sesiones

## Flujo de Datos

<center>

```mermaid
sequenceDiagram
    participant Maya as Maya/Odoo
    participant Browser as Navegador
    participant Client as main.py
    participant Service as Service (HTTP)
    participant Worker as Worker (Subprocess)
    participant Cert as Certificado
    
    Maya->>Browser: URL maya://sign?...
    Browser->>Client: Lanza protocolo
    Client->>Service: POST /sign
    
    alt Credenciales no almacenadas
        Service->>Service: Muestra diálogo
        Service->>Service: Espera input usuario
    end
    
    Service->>Maya: GET /download_pdfs
    Maya-->>Service: PDFs sin firmar
    
    Service->>Worker: Lanza subprocess
    Worker->>Cert: Accede certificado
    Worker->>Worker: Firma PDFs
    Worker-->>Service: PDFs firmados
    
    Service->>Maya: POST /upload_pdfs
    Maya-->>Service: Confirmación
    
    Service->>Service: Notifica usuario
```

</center>