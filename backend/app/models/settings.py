from pydantic import BaseModel

class PowerModel(BaseModel):
    power: bool

class SettingsModel(BaseModel):
    screenCount: int
    matrixCount: int
    screenShape: str
