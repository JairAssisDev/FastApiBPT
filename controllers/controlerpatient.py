from entities.paciente import Paciente
from fastapi import APIRouter
from predictions.predict import *
from pydantic import ValidationError
from fastapi.responses import JSONResponse
from shareds.database.comands.pacienteService import *


router = APIRouter(prefix="/paciente")

@router.post("")
def create_paciente(instance:Paciente):
    try:
        instance.nome = instance.nome.lower()
        dados = predict_and_explain(instance.sex, instance.redo, instance.cpb, instance.age, instance.bsa, instance.hb)
        instance.probability = dados["true_probability"]
        instance.prediction = dados["prediction"]
        insert_paciente(instance)
        return JSONResponse({'message': 'Paciente criado com sucesso'}), 201
    except ValidationError as e:
        return JSONResponse(status_code=422,content={'message': 'Erro na validação dos dados', 'error': e.errors()})
    except Exception as e:
        return JSONResponse(status_code=400,content={'message': 'Erro ao criar paciente', 'error': str(e)})
    
@router.get("/getallpacientes")
def get_all_pacientes():
    try:
        pacientes = paciente_get_all()
        return JSONResponse(status_code=200,content={"pacientes": pacientes})
    except Exception as e:
        return JSONResponse(status_code=401,content={'menssage':'pacente não existe ou foi encontrado'})
    
@router.get("/getproballpacientes")
def get_prob_all_pacientes():
    try:
        pacientes = paciente_prob_get_all()
        return JSONResponse(status_code=200,content={"pacientes": pacientes})
    except Exception as e:
        return JSONResponse(status_code=401, content={'menssage':'pacente não existe ou foi encontrado'})
    
@router.get("/{cpf}")
def get_paciente(cpf):
    paciente = get_by_name_cpf(cpf)
    if paciente:
        return JSONResponse(status_code=200,content={"message":paciente})
    return JSONResponse(status_code=404,content={'message': 'Paciente não encontrado'}), 404

@router("/img/{cpf}", methods=["GET"])
def get_imagem_paciente(cpf):
    paciente = get_by_name_cpf(cpf)
    if paciente:
        instance = Paciente(**paciente)
        dados = predict_and_explain_image(instance.sex, instance.redo, instance.cpb, instance.age, instance.bsa, instance.hb)
        instance.probability = str(dados["true_probability"])
        instance.prediction = str(dados["prediction"])
        instance.imagem = dados["lime_image"]
        return JSONResponse(status_code=200,content={"nome": instance.nome, "imagem": instance.imagem})
    return JSONResponse(status_code=404,content={'message': 'Paciente não encontrado'})


    
@router.delete("/delete/{cpf}", methods=["DELETE"])
def delete_paciente(cpf):
    paciente = verificar_paciente(cpf)
    if paciente:
        delete_paciente_by_name_and_cpf(cpf)
        return JSONResponse(status_code=200,content={'message': 'Paciente deletado com sucesso'})
    return JSONResponse(status_code=404,content={'message': 'Paciente não encontrado'})


@router.put("/update/{cpf}", methods=["PUT"])
def use_update_paciente(cpf:str,newpacinete: Paciente):
    paciente = verificar_paciente(cpf)
    if not paciente:
        return JSONResponse(status_code=404,content={'message': 'Paciente não encontrado'})

    try:
        newpacinete.nome = newpacinete.nome.lower()
        dados = predict_and_explain(newpacinete.sex, newpacinete.redo, newpacinete.cpb, newpacinete.age, newpacinete.bsa, newpacinete.hb)
        newpacinete.probability = dados["true_probability"]
        newpacinete.prediction = dados["prediction"]
        update_paciente(cpf, newpacinete)
        response_data = {
            "message": "Paciente atualizado com sucesso",
            "data": dados
        }
        return JSONResponse(status_code=200,content=response_data)

    except Exception as e:
        return JSONResponse(status_code=400,content={'error': "Erro ao atualizar paciente:"+str(e)})
