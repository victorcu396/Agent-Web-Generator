# pyproyect.toml

[![PyPI - Version](https://img.shields.io/pypi/v/pyproyect-toml.svg)](https://pypi.org/project/pyproyect-toml)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyproyect-toml.svg)](https://pypi.org/project/pyproyect-toml)

-----

## Table of Contents

- [Installation](#installation)
- [License](#license)

## Installation

```console
pip install pyproyect-toml
```

## License

`pyproyect-toml` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.


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



