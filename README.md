# Ophtao — Cabinet d'Ophtalmologie Dr Mégret & Associés

Static website for an ophthalmology clinic located at 60 rue Hoche, 78800 Houilles.
Includes an AI-powered chatbot widget backed by a fully local RAG pipeline — no cloud dependency, no patient data leaves the premises.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   FRONTEND (static)                  │
│                                                     │
│  HTML pages  ──►  assets/css/  +  assets/js/main.js │
│  Chatbot UI  ──►  chatbox/css/ +  chatbox/js/script.js│
└───────────────────────┬─────────────────────────────┘
                        │ fetch POST /api/v1/workspace/:slug/chat
                        ▼
┌─────────────────────────────────────────────────────┐
│              LOCAL AI BACKEND (Docker)               │
│                                                     │
│  AnythingLLM  ──►  RAG engine + vector store        │
│  Ollama       ──►  phi3:mini  or  llama3:8b (CPU)   │
│  LanceDB      ──►  local vector database            │
└─────────────────────────────────────────────────────┘
```

**Key constraint:** CPU-only inference. No GPU required. All data remains on the clinic's Windows server.

---

## Project Structure

```text
ophtao/
├── index.html
├── medical_team.html
├── consultation.html
├── pathologies.html
├── corrections.html
├── technical-equipment.html
│
├── assets/
│   ├── css/
│   │   ├── base.css          # Reset, design tokens, global animations
│   │   ├── layout.css        # Header, nav, footer, responsive breakpoints
│   │   ├── components.css    # Buttons, contact cards
│   │   ├── editorial.css     # Page hero, editorial blocks, CTA section
│   │   ├── home.css          # Hero, welcome section, info grid
│   │   └── team.css          # Team cards and grids
│   ├── js/
│   │   └── main.js           # Mobile menu toggle, dropdown accordion
│   └── images/
│
├── chatbox/
│   ├── css/
│   │   └── chatbox.css       # Chatbot widget styles
│   └── js/
│       ├── config.example.js # Template for environment variables
│       ├── config.js         # Active API Keys (Ignored by Git)
│       └── script.js         # AnythingLLM API client, widget logic
│
└── Knowledge_Base/           # RAG source documents (PDF, TXT)
    └── *.pdf / *.txt
```

---

## Prerequisites

| Tool | Purpose | Install |
|------|---------|---------|
| **Docker Desktop** | Runs AnythingLLM and Ollama containers | [docker.com](https://www.docker.com/products/docker-desktop/) |
| **VS Code** | Code editor | [code.visualstudio.com](https://code.visualstudio.com/) |
| **Live Server** (VS Code extension) | Local dev server — avoids CORS issues on `file://` | VS Code marketplace: `ritwickdey.LiveServer` |

---

## Local Setup & Deployment

### 1. Start Ollama and pull the model

```bash
# Pull and run Ollama (CPU mode, no GPU flags)
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama

# Pull a quantized model suited for CPU inference
docker exec -it ollama ollama pull phi3:mini
# Alternative: docker exec -it ollama ollama pull llama3:8b
```

### 2. Start AnythingLLM

```bash
docker run -d \
  -p 3001:3001 \
  -v ${PWD}/anythingllm_storage:/app/server/storage \
  --name anythingllm \
  mintplexlabs/anythingllm
```

Open `http://localhost:3001` and complete the setup wizard:

- **LLM Provider** → Ollama → `http://host.docker.internal:11434` → model: `phi3:mini`
- **Embedding model** → Ollama → `nomic-embed-text` (or any local embedding model)
- **Vector database** → LanceDB (no external service required)

### 3. Configure the RAG workspace

1. Create a workspace named **Ophtao** (the URL slug will be `ophtao`).
2. Upload existing documents via the UI (see "Adding Documents to the Knowledge Base" section below).
3. In **Workspace Settings**, set **Chat Mode** to **Query** — the model only responds when context is found in the knowledge base.
4. Paste the system prompt below into **Workspace Settings → System Prompt**.

#### System Prompt

```text
Tu es l'assistant virtuel du cabinet d'ophtalmologie Ophtao, situé au 60 rue Hoche, 78800 Houilles.

RÈGLES ABSOLUES :
1. Tu réponds UNIQUEMENT à partir des informations présentes dans les documents fournis.
   Si l'information n'y figure pas, dis exactement : "Je n'ai pas cette information. Appelez-nous au 01.39.13.91.91."
2. Tu n'inventes JAMAIS de diagnostic, de traitement, de tarif ou de disponibilité.
3. Tes réponses sont courtes : 2 à 4 phrases maximum.
4. Tu parles toujours en français, avec un ton professionnel et bienveillant.
5. Pour toute urgence médicale, oriente immédiatement vers le 15 (SAMU) ou le cabinet.
6. Tu ne parles jamais d'autres cabinets, d'autres médecins, ni de sujets hors du cabinet Ophtao.
```

### 4. Generate an API key

1. In AnythingLLM, go to **Settings → API Keys → Generate New API Key**.
2. Copy the generated key.

### 5. Find the workspace slug

Open your workspace. The slug is the last segment of the URL:
```text
http://localhost:3001/workspace/ophtao
                                ^^^^^^
                                this is your WORKSPACE_SLUG
```

### 6. Configure the chatbot

1. Duplicate `chatbox/js/config.example.js` and rename it to `chatbox/js/config.js`.
2. Update the `CONFIG` block:

```javascript
const CONFIG = {
  ANYTHINGLLM_BASE : 'http://localhost:3001',  // or the server's LAN IP, e.g. '[http://192.168.1.50:3001](http://192.168.1.50:3001)'
  WORKSPACE_SLUG   : 'ophtao',                 // slug from step 5
  API_KEY          : 'YOUR_API_KEY_HERE'       // key from step 4
};
```

> **LAN access:** If the site is served from the clinic's Windows server and accessed from other machines on the same network, replace `localhost` with the server's local IP address (e.g., `192.168.1.50`).

---

## Running the Site Locally

> **Do not open HTML files directly** (`file://` protocol). Browsers block `fetch()` calls to `localhost` from `file://` origins (CORS policy).

1. Open the project root folder in VS Code.
2. Right-click `index.html` → **Open with Live Server**.
3. The site opens at `http://127.0.0.1:5500` (or similar). All API calls to AnythingLLM will succeed from this origin.

---

## Adding Documents to the Knowledge Base

1. Open the AnythingLLM dashboard (`http://localhost:3001`).
2. Go to the "Workspace" section on the left sidebar and select the specific workspace (e.g., `ophtao`).
3. Click on the "Documents" tab or the "Upload" area.
4. Drag and drop or select the `.pdf` or `.txt` files (e.g., clinic tariffs, schedules, pathologies).
5. Click "Save and Embed" to vectorize the documents so the LLM can query them.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Status dot is red | AnythingLLM not reachable | Verify Docker container is running: `docker ps` |
| `Failed to fetch` in console | CORS on `file://` | Use Live Server (see above) |
| Bot answers "Je n'ai pas cette information" for everything | No documents indexed | Upload documents to the workspace in AnythingLLM UI |
| Very slow responses | Large model on CPU | Switch to `phi3:mini` — fastest quantized option for CPU-only inference |