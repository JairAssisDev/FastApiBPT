from entities.user import User
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from shareds.database.comands.userService import get_user, insert_user
from entities.auth import Auth
from entities.userBase import UserBase
from shareds.jwt.main import encode
from shareds.crypto import check_password

router = APIRouter(prefix="/user")

@router.post("/auth")
def autenticar_usuario(usuario:Auth):

    usuario_encontrado = get_user(usuario.matricula)
    if len(usuario_encontrado) > 0:
        senha_encriptada = usuario_encontrado[0]["password"]
        if not check_password(usuario.password, senha_encriptada):
            return JSONResponse(status_code=401,content={"content": {"User": "not found"}})
        nome_usuario = usuario_encontrado[0]["username"]
        instancia = {"userName": nome_usuario, "matricula": usuario.matricula}    
        token = encode(UserBase.parse_obj(instancia))
        return JSONResponse(status_code=200,content={"content": { "token": token }})
    else:
        return JSONResponse(status_code=401,content={"content": {"User": "not found"}})

@router.post("/create")
def criar_usuario(usuario:User):
    try:
        usuario_encontrado = get_user(usuario.matricula)
        if len(usuario_encontrado) == 0:
            insert_user(usuario)
            return JSONResponse(status_code=201,content={"content": {}})
        else:
            return JSONResponse(status_code=500,content={"content": {}})
    except Exception:
        return JSONResponse(status_code=409,content={"detail": "Erro ao inserir usuário"})
