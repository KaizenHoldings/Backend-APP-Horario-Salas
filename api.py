"""API REST: expone la agenda de las salas como JSON."""

import os
from datetime import date

from functools import lru_cache
from typing import List, Optional

import requests
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, Security
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel

from catalogo import Catalogo
from config import FECHA_POR_DEFECTO, GraphConfig
from exporter import normalizar_eventos
from graph_client import GraphAuthError, GraphClient

from fastapi.middleware.cors import CORSMiddleware

# ----------------------------------------------------------------- API Key
load_dotenv()
API_KEY = os.getenv("API_KEY", "")
if not API_KEY:
    raise RuntimeError("Falta la variable de entorno API_KEY en el .env")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verificar_api_key(key: Optional[str] = Security(api_key_header)) -> None:
    """Dependencia que valida el header X-API-Key en cada request."""
    
    if not key or key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="API key invalida o ausente.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

app = FastAPI(
    title="Agenda de salas",
    description="Consulta la ocupacion de las salas en Microsoft Graph.",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------- dependencias
@lru_cache(maxsize=1)
def get_cliente() -> GraphClient:
    """Un solo cliente para todo el proceso, asi el token se reutiliza."""
    return GraphClient(GraphConfig.from_env())


@lru_cache(maxsize=1)
def get_catalogo() -> Catalogo:
    cliente = get_cliente()
    return Catalogo(cliente)


# -------------------------------------------------------------------- modelos
class Sala(BaseModel):
    nombre: Optional[str] = None
    email: str
    timezone: str


class Evento(BaseModel):
    id: Optional[str] = None
    titulo: Optional[str] = None
    organizador: Optional[str] = None
    correo_organizador: Optional[str] = None
    fecha: Optional[str] = None
    desde: Optional[str] = None
    hasta: Optional[str] = None
    zona_horaria: Optional[str] = None

class Agenda(BaseModel):
    sala: Sala
    fecha: str
    total: int
    eventos: List[Evento]


class Catalogue(BaseModel):
    salas: List[Sala]


# ------------------------------------------------------------------ endpoints
@app.get("/salas", response_model=Catalogue, summary="Salas configuradas")
def listar_salas(
    catalogo: Catalogo = Depends(get_catalogo),
    _: None = Depends(verificar_api_key),
) -> Catalogue:
    """Devuelve el catalogo de salas obtenidas desde Microsoft Graph."""
    return Catalogue(salas=catalogo.listar())


@app.get("/salas/agenda", response_model=Agenda, summary="Agenda de una sala")
def agenda_de_sala(
    email: str = Query(
        ...,
        description="Correo del buzon de la sala. Es el unico dato obligatorio.",
        examples=["sala.kh@kaizenholdings.net"],
    ),
    timezone: Optional[str] = Query(
        None,
        description=(
            "Zona horaria IANA en que se devuelven las horas. "
            "Si se omite se usa la del catalogo."
        ),
        examples=["America/Caracas"],
    ),
    fecha: str = Query(
        FECHA_POR_DEFECTO,
        description="Dia a consultar en formato YYYY-MM-DD.",
        examples=[FECHA_POR_DEFECTO],
    ),
    cliente: GraphClient = Depends(get_cliente),
    catalogo: Catalogo = Depends(get_catalogo),
    _: None = Depends(verificar_api_key),
) -> Agenda:
    """Eventos de la sala en el dia indicado.

    El nombre de la sala no se pide: sale del catalogo si el correo esta ahi,
    y si no, viene vacio.
    """
    try:
        date.fromisoformat(fecha)
    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"Fecha invalida: '{fecha}'. Se espera YYYY-MM-DD."
        )

    sala = catalogo.resolver(email, timezone)

    try:
        eventos = cliente.get_eventos(
            sala["email"],
            inicio=f"{fecha}T00:00:00",
            fin=f"{fecha}T23:59:59",
            zona_horaria=sala["timezone"],
        )
    except GraphAuthError as error:
        raise HTTPException(status_code=502, detail=f"Fallo la autenticacion: {error}")
    except requests.HTTPError as error:
        estado = error.response.status_code if error.response is not None else 502
        if estado == 404:
            raise HTTPException(
                status_code=404, detail=f"No se encontro el buzon '{email}'."
            )
        if estado in (401, 403):
            raise HTTPException(
                status_code=403,
                detail=f"Sin permisos para leer el calendario de '{email}'.",
            )
        raise HTTPException(status_code=502, detail=f"Error de Graph: {error}")
    except requests.RequestException as error:
        raise HTTPException(status_code=504, detail=f"No se pudo contactar Graph: {error}")

    agenda = normalizar_eventos(eventos)

    return Agenda(
        sala=Sala(**sala),
        fecha=fecha,
        total=len(agenda),
        eventos=[Evento(**evento) for evento in agenda],
    )
