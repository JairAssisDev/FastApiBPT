from entities.paciente import Paciente
from fastapi import APIRouter, File, UploadFile, HTTPException
from predictions.predict import *
from pydantic import ValidationError
from fastapi.responses import JSONResponse
from shareds.database.comands.pacienteService import *
from io import BytesIO
import pandas as pd
from io import StringIO

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
    

from fastapi import Depends, File, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse, FileResponse
from io import BytesIO
import pandas as pd

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_pacientes(file: UploadFile = File(...)):
    """
    Uploads a CSV or XLS(X) file containing patient data and processes it.

    Raises:
        HTTPException: 400 for bad request errors (e.g., invalid file format)
    """

    try:
        if file.filename == "":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No selected file")

        file_content = await file.read()
        file_extension = file.content_type.lower().split("/")[-1]

        if file_extension in ("csv",):
            data = pd.read_csv(BytesIO(file_content))
        elif file_extension in ("xlsx", "xls"):
            data = pd.read_excel(BytesIO(file_content))
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type")

        filtered_data = data[data["nome"].str.lower() != "nome"] 
        lista_de_pacientes_n_salvos = []

        for index, row in filtered_data.iterrows():
            try:
                data_dict = {
                    "nome": str(row["nome"]).lower(),
                    "cpf": str(row["cpf"]),
                    "sex": int(row["sex"]),
                    "redo": int(row["redo"]),
                    "cpb": int(row["cpb"]),
                    "age": int(row["age"]),
                    "bsa": float(row["bsa"]),
                    "hb": float(row["hb"]),
                }

                paciente = verificar_paciente(data_dict["cpf"])
                if not paciente:
                    dados = predict_and_explain(
                        data_dict["sex"],
                        data_dict["redo"],
                        data_dict["cpb"],
                        data_dict["age"],
                        data_dict["bsa"],
                        data_dict["hb"],
                    )
                    data_dict["probability"] = dados["true_probability"]
                    data_dict["prediction"] = dados["prediction"]
                    insert_paciente(Paciente(**data_dict))
                else:
                    lista_de_pacientes_n_salvos.append(data_dict)
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

        if lista_de_pacientes_n_salvos:
            output = BytesIO()
            df = pd.DataFrame(lista_de_pacientes_n_salvos)
            df.to_excel(output, index=False, engine="openpyxl")
            output.seek(0)

            return FileResponse(
                output,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                filename="pacientes_nao_salvos.xlsx",
            )

        return JSONResponse(
            status_code=status.HTTP_207_MULTI_STATUS,
            content={"message": "Parte dos pacientes foram salvos com sucesso."},
        )

    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"error": str(e.detail)})
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"error": str(e)})
