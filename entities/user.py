from pydantic import BaseModel

class User(BaseModel):
    password: str
    userName: str
    matricula: str