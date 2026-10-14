from config import GraphConfig
from graph_client import GraphClient

def main():
    cliente = GraphClient(GraphConfig.from_env())
    try:
        salas = cliente.get_todos("places/microsoft.graph.room")
        print(salas)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
