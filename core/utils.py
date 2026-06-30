"""Funciones auxiliares reutilizadas por las vistas de usuario y admin."""


def siguiente_sql_id(coleccion):
    """
    MongoDB no autoincrementa un id numérico como lo haría SQL (solo genera
    ObjectId). Esta función busca el sql_id más alto existente en la
    colección y devuelve el siguiente entero libre (o 1 si está vacía).
    """
    ultimo = coleccion.find_one(sort=[('sql_id', -1)])
    if ultimo is None:
        return 1
    return ultimo.get('sql_id', 0) + 1
