from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.message import router as message_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Accepte toutes les origines (remplacer par l'ip si besoin)
    allow_credentials=True,
    allow_methods=["*"], # Autorise toutes les méthodes (GET, POST, etc)
    allow_headers=["*"], # Autorise tous les headers
)

# 📌 Inclure les routes de message.py
app.include_router(message_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
