"""Normalizacion de eventos y exportacion a JSON."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List


HORA_INICIO_JORNADA = 8
HORA_FIN_JORNADA = 17


def formatear_fecha(fecha: str | None) -> str:

    if not fecha:
        return ""

    dt = datetime.fromisoformat(
        fecha.split(".")[0]
    )

    return dt.strftime("%d/%m/%Y")


def formatear_hora(fecha: str | None) -> str:

    if not fecha:
        return ""

    dt = datetime.fromisoformat(
        fecha.split(".")[0]
    )

    return dt.strftime("%I:%M %p")


def normalizar_evento(evento: Dict[str, Any]) -> Dict[str, Any]:

    organizador = (
        evento.get("organizer", {})
        .get("emailAddress", {})
    )

    inicio = (
        evento.get("start", {})
        .get("dateTime")
    )

    fin = (
        evento.get("end", {})
        .get("dateTime")
    )

    return {
        "tipo": "ocupado",
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

        "inicio_raw": inicio,
        "fin_raw": fin,
    }


def crear_bloques(eventos_normalizados):

    if not eventos_normalizados:
        return []

    bloques = []

    fecha_base = eventos_normalizados[0][
        "inicio_raw"
    ].split("T")[0]

    inicio_jornada = datetime.fromisoformat(
        f"{fecha_base}T{HORA_INICIO_JORNADA:02d}:00:00"
    )

    fin_jornada = datetime.fromisoformat(
        f"{fecha_base}T{HORA_FIN_JORNADA:02d}:00:00"
    )

    eventos_ordenados = sorted(
        eventos_normalizados,
        key=lambda e: e["inicio_raw"]
    )

    cursor = inicio_jornada

    for evento in eventos_ordenados:

        inicio_evento = datetime.fromisoformat(
            evento["inicio_raw"].split(".")[0]
        )

        fin_evento = datetime.fromisoformat(
            evento["fin_raw"].split(".")[0]
        )

        if inicio_evento > cursor:

            bloques.append({
                "tipo": "libre",
                "id": None,
                "titulo": "Disponible",
                "organizador": None,
                "correo_organizador": None,
                "fecha": formatear_fecha(
                    eventos_ordenados[0]["inicio_raw"]
                ),
                "desde": cursor.strftime("%I:%M %p"),
                "hasta": fin_jornada.strftime("%I:%M %p"),
                "zona_horaria": eventos_ordenados[0]["zona_horaria"],
            })

            bloques.append({
                "tipo": "ocupado",
                "id": evento["id"],
                "titulo": evento["titulo"],
                "organizador": evento["organizador"],
                "correo_organizador": evento["correo_organizador"],
                "fecha": evento["fecha"],
                "desde": evento["desde"],
                "hasta": evento["hasta"],
                "zona_horaria": evento["zona_horaria"],
            })

        cursor = fin_evento

    if cursor < fin_jornada:

        bloques.append({
            "tipo": "libre",
            "id": None,
            "titulo": "Disponible",
            "organizador": None,
            "correo_organizador": None,
            "fecha": formatear_fecha(
                eventos_ordenados[0]["inicio_raw"]
            ),
            "desde": cursor.strftime("%I:%M %p"),
            "hasta": fin_jornada.strftime("%I:%M %p"),
            "zona_horaria": eventos_ordenados[0]["zona_horaria"],
        })
    return bloques


def normalizar_eventos(
    eventos: Iterable[Dict[str, Any]]
) -> List[Dict[str, Any]]:

    eventos_normalizados = [
        normalizar_evento(evento)
        for evento in eventos
    ]

    return crear_bloques(
        eventos_normalizados
    )


def exportar_json(
    datos: Any,
    ruta: str | Path
) -> Path:

    destino = Path(ruta)

    destino.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with destino.open(
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            datos,
            archivo,
            ensure_ascii=False,
            indent=2
        )

    return destino