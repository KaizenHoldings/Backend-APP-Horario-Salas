"""Normalizacion de eventos y exportacion a JSON."""

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

# normalizar envento nuevo
from datetime import datetime

def formatear_fecha(fecha: str | None) -> str:

    if not fecha:
        return ""

    dt = datetime.fromisoformat(
        fecha.split(".")[0]
    )

    return dt.strftime("%d/%m/%Y")

def formatear_hora(fecha: str) -> str:

    dt = datetime.fromisoformat(
        fecha.split(".")[0]
    )

    return dt.strftime("%I:%M %p")


def normalizar_evento(evento: Dict[str, Any]) -> Dict[str, Any]:

    organizador = evento.get(
        "organizer",
        {}
    ).get(
        "emailAddress",
        {}
    )

    inicio = evento.get(
        "start",
        {}
    ).get(
        "dateTime"
    )

    fin = evento.get(
        "end",
        {}
    ).get(
        "dateTime"
    )

    return {

        "id": evento.get("id"),

        "titulo": evento.get("subject"),

        "organizador": organizador.get("name"),

        "correo_organizador": organizador.get("address"),

        "fecha": formatear_fecha(inicio),

        "desde": formatear_hora(inicio),

        "hasta": formatear_hora(fin),

        "zona_horaria": evento.get(
            "start",
            {}
        ).get(
            "timeZone"
        ),
    }

#def normalizar_evento(evento: Dict[str, Any]) -> Dict[str, Any]:
#    """Deja un evento de Graph con solo los campos que nos interesan."""
#    organizador = evento.get("organizer", {}).get("emailAddress", {})
#
#    return {
#        "id": evento.get("id"),
#        "asunto": evento.get("subject"),
#        "organizador": organizador.get("name"),
#        "correo_organizador": organizador.get("address"),
#        "inicio": evento.get("start", {}).get("dateTime"),
#        "fin": evento.get("end", {}).get("dateTime"),
#        "zona_horaria": evento.get("start", {}).get("timeZone"),
#    }


def normalizar_eventos(eventos: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [normalizar_evento(evento) for evento in eventos]


def exportar_json(datos: Any, ruta: str | Path) -> Path:
    """Guarda la estructura en un archivo JSON y devuelve la ruta."""
    destino = Path(ruta)
    destino.parent.mkdir(parents=True, exist_ok=True)

    with destino.open("w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2)

    return destino
