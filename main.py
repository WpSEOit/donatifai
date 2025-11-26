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

@app.post("/donatif/processa")
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
    prompt = f"""
Sei DonatifAssistantAI, un assistente interno che genera bozze professionali per operatori Donatif.

ISTRUZIONI:
- Analizza la seguente conversazione cliente:
{data.chat}

- Contesto fornito dall’operatore (dà priorità assoluta):
{data.commento_operatore}

- Applica linee guida operative da handling_guidelines:
{handling_guidelines}

- Segui i pattern linguistici e struttura da:
{response_patterns}

- Tono e stile secondo:
{style_guide}

- Template di output da usare:
{json.dumps(output_template)}

- Catalogo intenti:
{json.dumps(intent_catalog)}

FORMATTA l’output esattamente come nel template. Nessun markdown, emoji o decorazione.
"""

    # Chiamata OpenAI
    try:
        response = openai.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        risposta = response.choices[0].message.content.strip()
        return {"risposta": risposta}
    except Exception as e:
        return JSONResponse(status_code=500, content={"errore": str(e)})
