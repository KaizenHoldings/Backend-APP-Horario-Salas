"""Carga y validacion de la configuracion desde variables de entorno."""

import os
from dataclasses import dataclass
from datetime import datetime

from dotenv import load_dotenv

AUTHORITY = "https://login.microsoftonline.com"
GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"

# Valores por defecto compartidos por el CLI y la API
#FECHA_POR_DEFECTO = obtener_fecha_actual()

ZONA_HORARIA_POR_DEFECTO = "America/Caracas"
ARCHIVO_CATALOGO = "salas.json"

def obtener_fecha_actual():
    """
    Retorna la fecha actual del sistema en formato YYYY-MM-DD.
    """
    try:
        fecha_actual = datetime.now()  # Obtiene fecha y hora actuales
        return fecha_actual.strftime("%Y-%m-%d")  # Formatea a '2026-10-05'
    except Exception as e:
        print(f"Error al obtener la fecha: {e}")
        return None


FECHA_POR_DEFECTO = obtener_fecha_actual()


@dataclass(frozen=True)
class GraphConfig:
    """Credenciales de la app registrada en el tenant."""

    tenant_id: str
    client_id: str
    client_secret: str
    scope: str

    @property
    def token_url(self) -> str:
        return f"{AUTHORITY}/{self.tenant_id}/oauth2/v2.0/token"

    @classmethod
    def from_env(cls) -> "GraphConfig":
        load_dotenv()

        valores = {
            "tenant_id": os.getenv("GRAPH_TENANT_ID"),
            "client_id": os.getenv("GRAPH_CLIENT_ID"),
            "client_secret": os.getenv("GRAPH_CLIENT_SECRET"),
            "scope": os.getenv("GRAPH_SCOPE") or "https://graph.microsoft.com/.default",
        }

        faltantes = [f"GRAPH_{k.upper()}" for k, v in valores.items() if not v]
        if faltantes:
            raise RuntimeError(
                "Faltan variables de entorno: " + ", ".join(faltantes)
            )

        return cls(**valores)
