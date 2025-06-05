# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from app.api.message import router as message_router

# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"], # Accepte toutes les origines (remplacer par l'ip si besoin)
#     allow_credentials=True,
#     allow_methods=["*"], # Autorise toutes les méthodes (GET, POST, etc)
#     allow_headers=["*"], # Autorise tous les headers
# )

# # 📌 Inclure les routes de message.py
# app.include_router(message_router)

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.settings import router as settings_router
from app.api.edition import router as edition_router
from app.api.presets import router as presets_router
from app.api.users import router as users_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # sécurise ça en prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(settings_router, prefix="/api/settings")
app.include_router(edition_router, prefix="/api/edition")
app.include_router(presets_router, prefix="/api/presets")
app.include_router(users_router, prefix="/api/users")

app.mount("/static", StaticFiles(directory="app/uploads"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
