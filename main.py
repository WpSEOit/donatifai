from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import openai
import os
import json
from dotenv import load_dotenv
import traceback
import logging

logging.basicConfig(level=logging.INFO)

# Carica variabili ambiente da .env
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# Percorso ai file KB
DATA_PATH = "./data"

# Modello GPT da usare
MODEL = "gpt-4o"

# Schema input API
class InputData(BaseModel):
    chat_history: str
    operator_note: str = ""
    channel: str  # "whatsapp" oppure "email"

# Utility per caricare file
def load_file(file_path: str):
    if file_path.endswith(".json"):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

# Endpoint API
@app.post("/process")
async def process(data: InputData):
    if data.channel not in ["whatsapp", "email"]:
        return JSONResponse(status_code=400, content={"errore": "channel deve essere 'whatsapp' o 'email'"})

    # Caricamento knowledge base
    intent_catalog = load_file(f"{DATA_PATH}/intent_catalog.json")
    handling_guidelines = load_file(f"{DATA_PATH}/handling_guidelines.md")
    response_patterns = load_file(f"{DATA_PATH}/response_patterns_.md")
    style_guide = load_file(f"{DATA_PATH}/style_guide_donatif.md")

    template_file = "output_template_whatsapp.json" if data.channel == "whatsapp" else "output_template_email.json"
    output_template = load_file(f"{DATA_PATH}/{template_file}")

    # Composizione prompt completo
    prompt = f"""
Sei DonatifAssistantAI, un assistente interno che genera bozze professionali per operatori Donatif.

ISTRUZIONI:
- Analizza la seguente conversazione cliente:
{data.chat_history}

- Contesto fornito dall’operatore (dà priorità assoluta):
{data.operator_note}

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

    try:
        response = openai.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        risposta = response.choices[0].message.content.strip()
        return {"risposta": risposta}
    except Exception as e:
        logging.error("Errore durante la chiamata OpenAI:")
        logging.error(traceback.format_exc())
        return JSONResponse(status_code=500, content={"errore": str(e)})
