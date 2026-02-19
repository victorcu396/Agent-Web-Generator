# Agent-Web-Generator

[![PyPI - Version](https://img.shields.io/pypi/v/pyproyect-toml.svg)](https://pypi.org/project/pyproyect-toml)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyproyect-toml.svg)](https://pypi.org/project/pyproyect-toml)

🚀 Generación automática de páginas web usando **FastAPI**, **Gemini ADK** y **Stitch MCP Server**.

---

## 🧩 Descripción

Agent-Web-Generator permite:

- Analizar prompts de usuario
- Generar planes de construcción web automáticamente
- Crear HTML/CSS listo para usar
- Integración con herramientas Gemini ADK y Stitch MCP

Es ideal para generar **landing pages**, **e-commerce** o **portfolios** de manera automática a partir de un simple texto.

---


┌─────────────────────────────────────────────────┐
│            AGENT-WEB-GENEARATOR                 │
│                                                 │
│  FastAPI (main.py)                              │
│     ↓                                           │
│  Rutas API (generate.py, chat.py)               │
│     ↓                                           │
│  Servicios (adk_agent_service.py)               │
│     ↓                                           │
│  Base de Datos (database.py)                    │
│     ↓                                           │
└─────┼───────────────────────────────────────────┘
      ↓
┌─────┴──────────────────┐
│   PostgreSQL Server    │
│   (puerto 5432)        │
└────────────────────────┘


# 🧩 Web Builder con ADK + MCP + Stitch

Proyecto para generación automática de páginas web usando **Gemini ADK**, **Stitch MCP Server** y un backend en **FastAPI** que orquesta todo el flujo.

Permite:

- Analizar prompts de usuario
- Generar planes de construcción web
- Crear HTML automáticamente
- Usar **Google ADK + Stitch MCP tools**

---

# 🚀 Arquitectura

## Flujo general

Cliente HTTP
↓
POST /generate (PromptDTO)
↓
WebBuilderAgent.analyze_prompt() → WebPlanDTO
↓
PageGenerator.generate(plan)
↓
Google ADK Agent + Stitch MCP
↓
HTML generado
↓
GeneratedPageDTO (html + framework)
↓
Respuesta JSON al cliente

cliente hace un POST /generate
Manda un JSON con el prompt:
json{ "prompt": "quiero una tienda online moderna" }
```

---

**2. `generate.py` recibe el request**

FastAPI deserializa el JSON a un `PromptDTO` y llama a `agent.run(data)`.

---

**3. `WebBuilderAgent.analyze_prompt()`**

Analiza el texto del prompt con simples condiciones `if`. Si contiene "tienda" devuelve un `WebPlanDTO` de tipo ecommerce, si contiene "portfolio" devuelve portfolio, si no, devuelve landing por defecto. Este plan tiene: `site_type`, `sections`, `style`.

---

**4. `PageGenerator.generate(plan)`**

Es un wrapper delgado, simplemente llama a `generate_with_adk(plan)`.

---

**5. `generate_with_adk()` — aquí ocurre lo importante**

- Si es la primera llamada, `_initialize()` crea la conexión al servidor MCP de Stitch en `https://stitch.googleapis.com/mcp`, construye el agente Gemini con ese toolset, y crea el Runner.
- Construye un prompt de texto con los datos del plan: tipo de página, secciones, estilo.
- Lo manda al Runner de ADK como un mensaje de usuario.

---

**6. ADK + Gemini + Stitch MCP**

Aquí es donde Gemini decide si usar las herramientas de Stitch o no. El flujo interno es:
```
Gemini recibe el prompt
↓
Decide llamar a una tool de Stitch (ej: generate_ui)
↓
ADK ejecuta la tool via MCP → llama al servidor de Stitch
↓
Stitch devuelve el resultado (HTML/CSS generado)
↓
Gemini recibe el resultado y forma la respuesta final

7. Respuesta final
generate_with_adk recorre los eventos del Runner hasta encontrar is_final_response(), extrae el texto y lo devuelve como string HTML.

8. WebBuilderAgent.run() devuelve un GeneratedPageDTO
json{
  "html": "<!DOCTYPE html>...",
  "framework": "html"
}
Y FastAPI lo serializa y lo manda al cliente.


---

# 🧠 Integración MCP + ADK

La comunicación sigue el patrón:

Gemini ADK → MCP Client → Stitch MCP Server


## Pasos del flujo MCP

1. Se levanta el **Stitch MCP Server**
2. El agente **Gemini ADK** se conecta vía **HTTP MCP**
3. Gemini puede:
   - Invocar tools
   - Ejecutar workflows de Stitch
   - Generar código web automáticamente

---


## 🛠️ Instalación (Local)

Clonar el repositorio:

git clone https://github.com/Formasster/Agent-Web-Generator.git
cd Agent-Web-Generator/backend


Crear entorno virtual e instalar dependencias:

python -m venv .venv
source .venv/bin/activate   # Mac/Linux
# .venv\Scripts\activate    # Windows
pip install -r requirements.txt


Crear archivo .env con la configuración de PostgreSQL y APIs:

DATABASE_HOSTNAME=127.0.0.1
DATABASE_PORT=5432
DATABASE_USERNAME=postgres
DATABASE_PASSWORD=postgres
DATABASE_NAME=boilerplate_db
GOOGLE_API_KEY=tu_api_key
OPENAI_API_KEY=tu_api_key


Levantar el backend:

uvicorn app.main:app --reload

## 🐳 Instalación con Docker

Crear .env como arriba

Desde la raíz del proyecto:

docker compose build --no-cache
docker compose up


Acceder a la API:

http://localhost:8000/docs




# 📡 Endpoints FastAPI

Base URL:

## 📚 Documentación API

GET /docs


http://localhost:8000/docs

Swagger UI del backend.

---

## 💬 Chatbot

POST /chat


Permite enviar prompts directamente al sistema de generación.

---

## 📁 Subida de archivos


POST /uploads

Permite subir assets que pueden usarse durante la generación web.

http://localhost:8000/uploads/[tu_imagen_o_documento]

---


# 🏗️ Componentes principales

## WebBuilderAgent

Responsable de:

- Analizar prompt
- Generar plan estructurado de página

**Output:**

WebPlanDTO

---

## PageGenerator

Se encarga de:

- Elegir modo de generación
- Ejecutar ADK o Stitch
- Devolver HTML final

---



