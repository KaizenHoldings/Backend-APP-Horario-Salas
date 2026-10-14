"""Consulta la agenda de una sala en Microsoft Graph y la exporta a JSON."""

from catalogo import Catalogo
from config import FECHA_POR_DEFECTO, GraphConfig
from exporter import exportar_json, normalizar_eventos
from graph_client import GraphClient

SALA = "sala.kh@kaizenholdings.net"
FECHA = FECHA_POR_DEFECTO
# salas.json es el catalogo de entrada, la agenda se escribe aparte
ARCHIVO_SALIDA = "agenda.json"


def main() -> None:
    cliente = GraphClient(GraphConfig.from_env())
    sala = Catalogo(cliente).resolver(SALA)

    eventos = cliente.get_eventos(
        sala["email"],
        inicio=f"{FECHA}T00:00:00",
        fin=f"{FECHA}T23:59:59",
        zona_horaria=sala["timezone"],
    )

    agenda = normalizar_eventos(eventos)

    for evento in agenda:
        print("Asunto:", evento["asunto"])
        print("Organizador:", evento["organizador"])
        print("Inicio:", evento["inicio"])
        print("Fin:", evento["fin"])
        print("-" * 50)

    salida = exportar_json(
        {"sala": sala, "fecha": FECHA, "eventos": agenda},
        ARCHIVO_SALIDA,
    )
    print(f"{len(agenda)} evento(s) exportado(s) a {salida}")


if __name__ == "__main__":
    main()
