from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import openai
import os
import json
from dotenv import load_dotenv

# Carica variabili ambiente da .env
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# Percorso ai file KB
DATA_PATH = "./data"

# Modello richiesto
MODEL = "gpt-4o"

# Input API
class InputData(BaseModel):
    chat: str
    commento_operatore: str = ""
    modalita: str  # "whatsapp" oppure "email"

# Utility: carica file testo o json
def load_file(file_path: str):
    if file_path.endswith(".json"):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

@app.post("/donatif/process")
async def processa_richiesta(data: InputData):
    # Validazione modalità
    if data.modalita not in ["whatsapp", "email"]:
        return JSONResponse(status_code=400, content={"errore": "modalita deve essere 'whatsapp' o 'email'"})

    # Carica file comuni
    intent_catalog = load_file(f"{DATA_PATH}/intent_catalog.json")
    handling_guidelines = load_file(f"{DATA_PATH}/handling_guidelines.md")
    response_patterns = load_file(f"{DATA_PATH}/response_patterns_.md")
    style_guide = load_file(f"{DATA_PATH}/style_guide_donatif.md")

    # Carica output template specifico
    output_template_file = "output_template_whatsapp.json" if data.modalita == "whatsapp" else "output_template_email.json"
    output_template = load_file(f"{DATA_PATH}/{output_template_file}")

    # Costruzione prompt
    prompt = f\"\"\"
Sei DonatifAssistantAI, un assistente interno che genera risposte coerenti, strutturate e professionali per operatori Donatif.

ISTRUZIONI:
- Analizza la conversazione cliente riportata sotto.
- Usa come riferimento prioritario il contesto dell’operatore fornito sotto.
- Applica tutte le regole contenute nei seguenti file:

Catalogo Intent:
{json.dumps(intent_catalog)}

Linee guida operative:
{handling_guidelines}

Pattern linguistici e risposte:
{response_patterns}

Guida di stile:
{style_guide}

Template di output da rispettare (in formato JSON):
{json.dumps(output_template)}

📥 Conversazione cliente:
{data.chat}

📌 Contesto manuale dell’operatore (da seguire alla lettera se presente):
{data.commento_operatore}

📤 FORMATO OUTPUT:
Rispondi restituendo solo un oggetto JSON con i seguenti campi:

{{
  "analisi": "...",
  "azioni": "...",
  "risposta": "...",
  "meta": {{
    "confidence": "alta/media/bassa",
    "iteration": numero,
    "verifica_trm": "ok" oppure "warning"
  }}
}}

📛 IMPORTANTE:
- Nessun markdown o emoji.
- Nessuna ripetizione del messaggio cliente.
- Nessuna CTA non prevista o inventata.
- Segui rigorosamente il tono e il formato del template.
\"\"\"

    # Chiamata OpenAI
    try:
        response = openai.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        risposta = response.choices[0].message.content.strip()
        return JSONResponse(content=json.loads(risposta))
    except Exception as e:
        return JSONResponse(status_code=500, content={"errore": str(e)})