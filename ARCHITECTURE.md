# Architecture - Agent Web Generator

## Project Structure

```
backend/
├── app/
│   ├── agents/
│   │   ├── web_builder_agent.py       # Orquestador: analiza prompt → WebPlanDTO
│   │   └── agent_principal.py         # CLI interactivo (referencia, no usado en API)
│   ├── api/routes/
│   │   ├── generate.py                # POST /generate, POST /generate/upload (principal endpoint)
│   │   └── chat.py                    # GET /chat (UI web), POST /api/chat/message
│   ├── services/
│   │   ├── page_generator.py          # Selector: ADK vs MCP
│   │   ├── stitch_adk_client.py       # Generación ADK no-interactiva (para /generate)
│   │   ├── adk_agent_service.py       # Chat interactivo ADK (para /chat)
│   │   ├── stitch_client.py           # Generación MCP HTTP (alternativa)
│   │   └── adk_agent_service.py       # Sesiones interactivas con Runner
│   ├── dto/
│   │   ├── prompt_dto.py              # {prompt, images, docs}
│   │   ├── web_plan_dto.py            # {site_type, sections, style, images, docs}
│   │   └── result_dto.py              # {html, framework}
│   └── main.py                        # FastAPI app, monta rutas + /uploads
├── uploads/                           # Archivos subidos (imágenes, docs)
└── requirements.txt                   # Dependencias
```

## Flow Diagrams

### 1. **POST /generate** (generación de página)
```
Cliente
  ↓
POST /generate (PromptDTO)
  ↓
WebBuilderAgent.run()
  ↓ analyze_prompt()
WebPlanDTO (site_type, sections, style, images, docs)
  ↓
PageGenerator.generate(plan)
  ├─→ Si USE_ADK=true
  │    ↓
  │    stitch_adk_client.generate_with_adk()
  │    ↓
  │    Agente ADK (generación una sola vez)
  │
  └─→ Si USE_ADK=false
       ↓
       stitch_client.generate_with_stitch()
       ↓
       MCP HTTP POST localhost:3001/generate

↓
HTML generado
↓
GeneratedPageDTO {html, framework}
↓
Response JSON
```

### 2. **POST /generate/upload** (con archivos)
```
Cliente (form multipart)
  ├─ prompt (text)
  ├─ images[] (files)
  └─ docs[] (files)
  ↓
Upload endpoint salva archivos → /backend/uploads/uuid_*
  ↓
Crea PromptDTO con rutas locales
  ↓
WebBuilderAgent.run() (igual que /generate)
  ↓
HTML generado
```

### 3. **GET /chat + POST /api/chat/message** (conversación interactiva)
```
Cliente (navegador)
  ↓
GET /chat
  ↓
Página HTML (chat UI)
  ↓
JavaScript envía POST /api/chat/message {message}
  ↓
ADKAgentService.chat(user_message)
  ├─ Inicializa sesión (una sola vez)
  ├─ McpToolset + Agent + InMemorySessionService
  ├─ Runner.run_async() con mensaje del usuario
  └─ Retorna respuesta final del agente
  ↓
Response JSON {response}
  ↓
UI renderiza respuesta
```

## Key Services

| Servicio | Responsabilidad | Endpoint/Uso |
|----------|---|---|
| `web_builder_agent.py` | Mapeo prompt → plan (lógica simple) | `/generate` |
| `page_generator.py` | Selector USE_ADK (verdadero orquestador) | Interno |
| `stitch_adk_client.py` | Generación ADK puntual | `/generate` si USE_ADK=true |
| `adk_agent_service.py` | Chat ADK multi-turno + sesiones | `/api/chat/message` |
| `stitch_client.py` | Generación MCP HTTP | `/generate` si USE_ADK=false |

## Environment Variables

```
GOOGLE_API_KEY=...         # Para ADK
STITCH_API_KEY=...         # Para Google Stitch MCP
USE_ADK=true               # true=ADK, false=MCP HTTP
```

## Starting the Server

```bash
cd backend
source ../.venv/bin/activate
python3 -m uvicorn app.main:app --reload --port 8000
```

**Endpoints Available:**
- `http://localhost:8000/docs` — Swagger UI
- `POST /generate` — Generar página con prompt
- `POST /generate/upload` — Generar con archivos
- `GET /chat` — UI interactivo
- `POST /api/chat/message` — Mensajes de chat
- `GET /uploads/{filename}` — Acceder archivos subidos

## Notes

- **Agent Principal** (`agent_principal.py`): Script CLI interactivo. No se usa en los endpoints; es una referencia/test.
- **ADK Sessions**: `adk_agent_service.py` mantiene sesiones en memoria (`InMemorySessionService`). Cada instancia = nueva sesión.
- **MCP Alternative**: Si no quieres ADK en tiempo de ejecución, usa `USE_ADK=false` y asegura que `localhost:3001/generate` está corriendo.
