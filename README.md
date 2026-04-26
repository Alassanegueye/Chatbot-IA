# Backend — IA Témoin d'Alassane Gueye

## Installation

```bash
cd backend
pip install -r requirements.txt
```

## Lancement

```bash
# Option 1 — variable d'environnement directe
ANTHROPIC_API_KEY=sk-ant-... uvicorn main:app --reload

# Option 2 — fichier .env
cp .env.example .env
# Edite .env et ajoute ta clé
uvicorn main:app --reload
```

Le serveur tourne sur http://127.0.0.1:8000

## Endpoints

- `GET /`        → health check
- `POST /chat`   → envoie un message + historique, reçoit la réponse de l'IA

## Structure

```
backend/
├── main.py          
├── data.txt         
├── requirements.txt
└── .env.example
```
