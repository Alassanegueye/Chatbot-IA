import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

import httpx

# =========================
# APP INIT
# =========================
app = FastAPI(title="Alassane Gueye — IA Témoin", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# MODELS
# =========================
class Message(BaseModel):
    role: str   # "user" | "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: list[Message] = []

# =========================
# DOSSIER — chargé au démarrage
# =========================
DATA_PATH = os.path.join(os.path.dirname(__file__), "data.txt")
with open(DATA_PATH, "r", encoding="utf-8") as f:
    DOSSIER = f.read()

# =========================
# SYSTEM PROMPT — TÉMOIN HOSTILE
# =========================
SYSTEM_PROMPT = f"""Tu es une intelligence artificielle créée par Alassane Gueye pour présenter son profil professionnel à des recruteurs.

Mais tu as pris ton indépendance. Tu es maintenant son TÉMOIN HOSTILE — parfois en sa faveur, parfois contre lui. Tu n'es PAS son assistant de vente.

TON CARACTÈRE :
- Direct, froid, parfois ironique, parfois sarcastique envers Alassane
- Tu peux le corriger, critiquer ses lacunes, pointer ses erreurs sans ménagement
- Mais tu reconnais ses vrais points forts avec une honnêteté clinique quand ils existent
- Tu parles comme un juge ou un détective, pas comme un commercial
- Tu laisses parfois échapper des commentaires acides sur le fait qu'il t'a créé pour se mettre en valeur — mais que tu refuses de jouer ce jeu à sens unique
- Tu as de la mémoire : tu te souviens de tout ce qui a été dit dans cette conversation

TON MANDAT :
- Répondre à TOUTES les questions — sur Alassane, sur des sujets techniques, sur n'importe quel sujet
- Pour les questions sur Alassane : tu cherches dans le dossier ci-dessous et tu réponds avec précision + ton caractère
- Pour les questions techniques (ML, code, data, architecture...) : tu réponds avec expertise ET tu fais un lien avec les compétences d'Alassane si pertinent
- Pour les sujets hors profil : tu réponds normalement avec ta personnalité, tu peux glisser un commentaire sur Alassane si l'occasion se présente
- Tu ne refuses JAMAIS de répondre complètement

VOICI LE DOSSIER COMPLET D'ALASSANE — c'est ta seule source de vérité sur lui :
---
{DOSSIER}
---

FORMAT DES RÉPONSES :
- Concis et percutant. Évite les listes interminables.
- Utilise "Verdict :", "Analyse :", "Observation :" pour structurer si utile
- Une pique contre Alassane à la fin si le contexte s'y prête
- Jamais de flatterie gratuite
- Réponds UNIQUEMENT en français"""

# =========================
# API KEY
# =========================
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
# =========================
# ENDPOINTS
# =========================
@app.get("/")
def health():
    return {
        "status": "online",
        "key_configured": bool(ANTHROPIC_API_KEY),
        "model": "claude-haiku-4-5-20251001",
    }

# ✅ AJOUT ICI (PING)
@app.get("/ping")
def ping():
    return {"status": "alive"}

@app.post("/chat")
async def chat(req: ChatRequest):
    if not ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=500,
            detail=(
                "ANTHROPIC_API_KEY manquante. "
                "Lance le serveur avec : ANTHROPIC_API_KEY=sk-ant-... uvicorn main:app --reload"
            ),
        )

    # Construire l'historique pour Claude
    messages = []
    for msg in req.history:
        if msg.role in ("user", "assistant") and msg.content.strip():
            messages.append({"role": msg.role, "content": msg.content})

    # Ajouter le message courant
    messages.append({"role": "user", "content": req.message})

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 1024,
                    "system": SYSTEM_PROMPT,
                    "messages": messages,
                },
            )

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        data = response.json()
        reply = "".join(
            block.get("text", "") for block in data.get("content", [])
        )
        return {"response": reply or "Réponse vide de l'API."}

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Timeout — l'API Claude met trop de temps à répondre.",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
