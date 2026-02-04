# Arquitectura

Diseño del sistema y cómo encajan los componentes.

## Diagrama general

```mermaid
graph TB
    subgraph "Servidor Maya"
        Odoo[Maya / Odoo]
        DB[(Base de Datos)]
        Odoo <--> DB
    end

    subgraph "Navegador del Usuario"
        Web[Interfaz Web Maya]
        Web -->|Click Firmar| Proto["enlace maya://"]
    end

    subgraph "Escritorio del Usuario"
        Proto -->|SO ejecuta| Main["main.py (Cliente)"]
        Main -->|HTTP POST| Service["maya_signer_service.py (Servicio)"]
        Service -->|Qt GUI| Dialog["credentials_dialog.py"]
        Service -->|XML-RPC| Odoo
        Service -->|Lanza| Manager["subprocess_signature_manager.py"]
        Manager -->|Subproceso| Worker["signer_worker.py"]
        Worker -->|Usa| Hanko["hanko_signer.py"]
        Hanko -->|Accede| Cert["Certificado / DNIe"]
        Service -->|Muestra| Tray["Bandeja del Sistema"]
    end
```

## Comunicación entre componentes

### Cliente → Servicio (HTTP)

El cliente (`main.py`) y el servicio (`maya_signer_service.py`) se comunican vía HTTP local:

```
POST http://127.0.0.1:50304/
Content-Type: application/json

{
  "batch": 42,
  "url": "https://maya.example.com",
  "database": "production",
  "token": "tok_abc123"
}
```

### Servicio → Odoo (XML-RPC)

El servicio se comunica con Odoo mediante XML-RPC sobre HTTPS:

```
Servicio                          Odoo (XML-RPC)
   |                                   |
   |--- authenticate() ------------->  |
   |<-- uid -------------------------  |
   |                                   |
   |--- validate_session_token() --->  |
   |<-- {valid: true} ---------------  |
   |                                   |
   |--- download_unsigned_pdfs() --->  |
   |<-- [PDF1, PDF2, ...] -----------  |
   |                                   |
   |--- upload_signed_pdfs() --------> |
   |<-- true ------------------------  |
```

### Servicio → Worker (Archivos JSON)

El servicio y el worker no comparten memoria ni sockets. Se comunican exclusivamente por archivos en un directorio temporal:

```
Directorio temporal: /tmp/maya_signer_XXXXX/

Servicio escribe:                    Worker lee:
  input.json ─────────────────────>  input.json
  unsigned_1.pdf ─────────────────>  unsigned_1.pdf
  unsigned_2.pdf ─────────────────>  unsigned_2.pdf

Worker escribe:                      Servicio lee:
  status.json ────────────────────>  status.json  (polling cada 0.5s)
  signed_1.pdf ───────────────────>  signed_1.pdf
  signed_2.pdf ───────────────────>  signed_2.pdf
  output.json ────────────────────>  output.json
```

## Decisiones de diseño

### ¿Por qué el worker es un subproceso separado?

Las librerías de firma (pyHanko, PKCS#11) pueden ser inestables, especialmente con DNIe. Si el worker crashea:

- El servicio principal sigue corriendo
- El usuario puede reintentar
- No se pierde el estado de la aplicación

### ¿Por qué comunicación por archivos y no por sockets?

- Máxima aislamiento entre procesos
- Fácil de debuggear (puedes leer los archivos manualmente)
- No hay problemas de sincronización ni deadlocks
- El worker no necesita conocer nada del servicio

### ¿Por qué las credenciales solo en memoria?

- Se eliminan automáticamente cuando se cierra el servicio
- No hay riesgo de lectura desde disco
- El usuario puede limpiarlas manualmente en cualquier momento

### ¿Por qué un solo .spec para 3 plataformas?

- Un solo lugar donde añadir hidden imports
- Menos archivos que mantener
- El .spec detecta el SO automáticamente y se adapta

## Flujo completo de una firma

```mermaid
sequenceDiagram
    participant U as Usuario
    participant B as Navegador
    participant C as main.py
    participant S as Servicio
    participant D as Diálogo
    participant O as Odoo
    participant M as Manager
    participant W as Worker
    participant F as Certificado

    U->>B: Click "Firmar" en Maya
    B->>C: Abre maya://sign?batch=42&...
    C->>S: POST {batch, url, token}

    alt Sin credenciales almacenadas
        S->>D: Muestra diálogo
        D->>U: Solicita usuario/pass/cert
        U->>D: Introduce credenciales
        D->>S: Guarda en memoria
    end

    S->>O: authenticate()
    O-->>S: uid
    S->>O: validate_session_token()
    O-->>S: {valid: true}
    S->>O: download_unsigned_pdfs(42)
    O-->>S: [PDF1, PDF2]

    S->>M: sign_documents([PDF1, PDF2])
    M->>M: Prepara directorio temporal
    M->>M: Escribe input.json + PDFs
    M->>W: Lanza subproceso

    W->>W: Lee input.json
    W->>F: Carga certificado
    W->>W: Firma PDF1
    W->>W: Firma PDF2
    W->>W: Escribe output.json + PDFs firmados

    M->>M: Lee output.json
    M-->>S: [PDF1_firmado, PDF2_firmado]

    S->>O: upload_signed_pdfs(42, [...])
    O-->>S: true
    S->>U: Notificación "2 documentos firmados"
```
