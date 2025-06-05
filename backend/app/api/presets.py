# # app/api/presets.py
# from fastapi import APIRouter, HTTPException
# from pydantic import BaseModel
# from typing import List, Optional

# router = APIRouter()

# # Modèle pour un preset
# class PresetModel(BaseModel):
#     id: int
#     name: str
#     type: str  # ex: 'ads', 'lyrics', 'visual', etc.
#     config: dict

# # Stockage temporaire en mémoire
# _presets_db: List[PresetModel] = [
#     PresetModel(id=1, name="Default Ad", type="ads", config={"content":"Sale!","speed":3}),
#     PresetModel(id=2, name="Lyric Flow", type="lyrics", config={"textColor":"white","backgroundColor":"black","font":"Arial","animation":"scroll_left"}),
# ]
# _next_id = 3

# @router.get("/", response_model=List[PresetModel])
# async def list_presets():
#     return _presets_db

# @router.post("/", response_model=PresetModel)
# async def create_preset(preset: PresetModel):
#     global _next_id
#     preset.id = _next_id
#     _next_id += 1
#     _presets_db.append(preset)
#     return preset

# @router.get("/{preset_id}", response_model=PresetModel)
# async def get_preset(preset_id: int):
#     for p in _presets_db:
#         if p.id == preset_id:
#             return p
#     raise HTTPException(status_code=404, detail="Preset not found")

# @router.put("/{preset_id}", response_model=PresetModel)
# async def update_preset(preset_id: int, updated: PresetModel):
#     for idx, p in enumerate(_presets_db):
#         if p.id == preset_id:
#             updated.id = preset_id
#             _presets_db[idx] = updated
#             return updated
#     raise HTTPException(status_code=404, detail="Preset not found")

# @router.delete("/{preset_id}")
# async def delete_preset(preset_id: int):
#     for idx, p in enumerate(_presets_db):
#         if p.id == preset_id:
#             _presets_db.pop(idx)
#             return {"status": "deleted"}
#     raise HTTPException(status_code=404, detail="Preset not found")


# ------------------------------------ Asynchrone --------------------------------------
# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select
# from pydantic import BaseModel
# from typing import List

# from app.db import AsyncSessionLocal
# from app.models.presets import Preset

# router = APIRouter()

# # Dependency pour récupérer une session
# async def get_session():
#     async with AsyncSessionLocal() as session:
#         yield session

# # Pydantic schema pour les payloads
# class PresetCreate(BaseModel):
#     name: str
#     type: str
#     data: dict

# class PresetRead(PresetCreate):
#     id: int

# # -----------------------------
# @router.get("/", response_model=List[PresetRead])
# async def list_presets(session: AsyncSession = Depends(get_session)):
#     result = await session.execute(select(Preset))
#     return result.scalars().all()

# @router.post("/", response_model=PresetRead, status_code=status.HTTP_201_CREATED)
# async def create_preset(data: PresetCreate, session: AsyncSession = Depends(get_session)):
#     p = Preset(**data.dict())
#     session.add(p)
#     await session.commit()
#     await session.refresh(p)
#     return p

# @router.get("/{preset_id}", response_model=PresetRead)
# async def get_preset(preset_id: int, session: AsyncSession = Depends(get_session)):
#     p = await session.get(Preset, preset_id)
#     if not p:
#         raise HTTPException(status_code=404, detail="Preset not found")
#     return p

# @router.put("/{preset_id}", response_model=PresetRead)
# async def update_preset(preset_id: int, data: PresetCreate, session: AsyncSession = Depends(get_session)):
#     p = await session.get(Preset, preset_id)
#     if not p:
#         raise HTTPException(status_code=404, detail="Preset not found")
#     for k, v in data.dict().items():
#         setattr(p, k, v)
#     await session.commit()
#     await session.refresh(p)
#     return p

# @router.delete("/{preset_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_preset(preset_id: int, session: AsyncSession = Depends(get_session)):
#     p = await session.get(Preset, preset_id)
#     if not p:
#         raise HTTPException(status_code=404, detail="Preset not found")
#     await session.delete(p)
#     await session.commit()


# -------------------------------------- Synchrone ----------------------------------
# app/api/presets.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel
from typing import List

from app.db import get_db           # Dépendance synchrone
from app.models.presets import Preset

router = APIRouter()

# --- Schémas Pydantic ---
class PresetCreate(BaseModel):
    name: str
    type: str
    data: dict

class PresetRead(PresetCreate):
    id: int


# ─── 1) Lister tous les presets ───────────────────────────────────────────────────
@router.get("/", response_model=List[PresetRead])
def list_presets(db: Session = Depends(get_db)):
    """
    Récupère tous les presets depuis la BDD et les renvoie.
    """
    result = db.execute(select(Preset))
    presets = result.scalars().all()
    return presets


# ─── 2) Créer un nouveau preset ───────────────────────────────────────────────────
@router.post("/", response_model=PresetRead, status_code=status.HTTP_201_CREATED)
def create_preset(data: PresetCreate, db: Session = Depends(get_db)):
    """
    Crée un preset avec les champs {name, type, data} et le sauve en base.
    """
    p = Preset(**data.dict())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


# ─── 3) Récupérer un preset par ID ────────────────────────────────────────────────
@router.get("/{preset_id}", response_model=PresetRead)
def get_preset(preset_id: int, db: Session = Depends(get_db)):
    """
    Retourne le preset dont l'id vaut preset_id, ou 404 si introuvable.
    """
    p = db.get(Preset, preset_id)
    if not p:
        raise HTTPException(status_code=404, detail="Preset not found")
    return p


# ─── 4) Mettre à jour un preset ───────────────────────────────────────────────────
@router.put("/{preset_id}", response_model=PresetRead)
def update_preset(preset_id: int, data: PresetCreate, db: Session = Depends(get_db)):
    """
    Modifie le preset existant (si trouvé). On met à jour tous les champs {name, type, data}.
    """
    p = db.get(Preset, preset_id)
    if not p:
        raise HTTPException(status_code=404, detail="Preset not found")
    for field, value in data.dict().items():
        setattr(p, field, value)
    db.commit()
    db.refresh(p)
    return p


# ─── 5) Supprimer un preset ────────────────────────────────────────────────────────
@router.delete("/{preset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_preset(preset_id: int, db: Session = Depends(get_db)):
    """
    Supprime un preset par son ID. Retourne 404 si le preset n'existe pas.
    """
    p = db.get(Preset, preset_id)
    if not p:
        raise HTTPException(status_code=404, detail="Preset not found")
    db.delete(p)
    db.commit()
    # Pas de contenu renvoyé (204)
    return
