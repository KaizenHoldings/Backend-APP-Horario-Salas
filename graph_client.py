"""Cliente de Microsoft Graph: autenticacion con el tenant y consultas."""

import time
from typing import Any, Dict, List, Optional

import requests

from config import GRAPH_BASE_URL, ZONA_HORARIA_POR_DEFECTO, GraphConfig


class GraphAuthError(RuntimeError):
    """No se pudo obtener el token del tenant."""


class GraphClient:
    """Encapsula la conexion con el tenant y las llamadas a Graph.

    El token se pide la primera vez que se necesita y se reutiliza hasta
    que esta por expirar.
    """

    MARGEN_EXPIRACION = 60  # segundos antes de expirar en que se renueva

    def __init__(self, config: GraphConfig, timeout: int = 30):
        self.config = config
        self.timeout = timeout
        self._session = requests.Session()
        self._token: Optional[str] = None
        self._expira_en: float = 0.0

    # ------------------------------------------------------------------ auth
    @property
    def token(self) -> str:
        if self._token is None or time.time() >= self._expira_en:
            self._token = self._solicitar_token()
        return self._token

    def _solicitar_token(self) -> str:
        data = {
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "scope": self.config.scope,
            "grant_type": "client_credentials",
        }

        response = self._session.post(
            self.config.token_url, data=data, timeout=self.timeout
        )

        if response.status_code != 200:
            raise GraphAuthError(
                f"Error {response.status_code} al pedir el token: {response.text}"
            )

        payload = response.json()
        self._expira_en = (
            time.time() + payload.get("expires_in", 3600) - self.MARGEN_EXPIRACION
        )
        return payload["access_token"]

    def _headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = {"Authorization": f"Bearer {self.token}"}
        if extra:
            headers.update(extra)
        return headers

    # --------------------------------------------------------------- consultas
    def get(
        self,
        recurso: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """GET a un recurso de Graph (ruta relativa o URL absoluta)."""
       # url = recurso if recurso.startswith("http") else f"{GRAPH_BASE_URL}/{recurso.lstrip('/')}"
        url = f'https://graph.microsoft.com/v1.0/{recurso}'

        response = self._session.get(
            url, headers=self._headers(headers), params=params, timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()

    def get_todos(
        self,
        recurso: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """Igual que get() pero recorre las paginas (@odata.nextLink)."""
        resultados: List[Dict[str, Any]] = []
        payload = self.get(recurso, params=params, headers=headers)

        while True:
            resultados.extend(payload.get("value", []))
            siguiente = payload.get("@odata.nextLink")
            if not siguiente:
                return resultados
            payload = self.get(siguiente, headers=headers)

    # ------------------------------------------------------------------ salas
    def get_usuario(self, upn: str) -> Dict[str, Any]:
        """Datos del usuario / sala identificado por su UPN."""
        return self.get(f"users/{upn}")

    def get_eventos(
        self,
        upn: str,
        inicio: str,
        fin: str,
        zona_horaria: str = ZONA_HORARIA_POR_DEFECTO,
    ) -> List[Dict[str, Any]]:
        """Eventos del calendario del buzon entre dos fechas ISO 8601."""
        return self.get_todos(
            f"users/{upn}/calendarView",
            params={
                "startDateTime": inicio,
                "endDateTime": fin,
                "$orderby": "start/dateTime",
                "$top": 100,
            },
            headers={"Prefer": f'outlook.timezone="{zona_horaria}"'},
        )

    def get_salas(self) -> List[Dict[str, Any]]:
        """Obtiene la lista de salas desde Microsoft Graph."""
        return self.get_todos("places/microsoft.graph.room")
