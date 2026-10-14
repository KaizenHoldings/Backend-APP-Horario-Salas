"""Catalogo de salas: nombre y zona horaria asociados a cada correo."""

from typing import Dict, List, Optional
from graph_client import GraphClient
from config import ZONA_HORARIA_POR_DEFECTO

class Catalogo:
    """Consulta las salas desde Microsoft Graph.

    El correo es el unico dato obligatorio: si la sala esta en Graph,
    de ahi salen su nombre y su zona horaria.
    """

    def __init__(self, cliente: GraphClient):
        self.cliente = cliente
        self._salas_cache: Optional[List[Dict[str, str]]] = None

    def listar(self) -> List[Dict[str, str]]:
        if self._salas_cache is None:
            lugares = self.cliente.get_salas()
            salas = []
            for lugar in lugares:
                salas.append({
                    "nombre": lugar.get("displayName", ""),
                    "email": lugar.get("emailAddress", ""),
                    "timezone": ZONA_HORARIA_POR_DEFECTO
                })
            self._salas_cache = salas
        return self._salas_cache

    def buscar(self, email: str) -> Optional[Dict[str, str]]:
        objetivo = email.strip().lower()
        for sala in self.listar():
            if sala.get("email", "").strip().lower() == objetivo:
                return sala
        return None

    def resolver(
        self, email: str, timezone: Optional[str] = None
    ) -> Dict[str, Optional[str]]:
        """Completa nombre y zona horaria a partir del correo.

        La zona horaria recibida manda sobre la del catalogo.
        """
        sala = self.buscar(email) or {}

        return {
            "nombre": sala.get("nombre"),
            "email": email,
            "timezone": timezone
            or sala.get("timezone")
            or ZONA_HORARIA_POR_DEFECTO,
        }
