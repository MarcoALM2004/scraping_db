"""
scraper/comparador.py

Compara productos entre:
- Memory Kings
- Impacto

Utiliza similitud de nombres para encontrar coincidencias.
"""

import re
from difflib import SequenceMatcher


def limpiar_nombre(nombre):
    """
    Normaliza nombres para comparación.
    Remueve mayúsculas, caracteres especiales y espacios duplicados.
    """
    if not nombre:
        return ""
    
    nombre = nombre.lower()
    nombre = re.sub(r'[^a-z0-9\s]', ' ', nombre)
    nombre = re.sub(r'\s+', ' ', nombre).strip()
    return nombre


def similitud(a, b):
    """
    Retorna un valor float entre 0.0 y 1.0 indicando qué tan
    parecidos son dos títulos de productos.
    """
    return SequenceMatcher(
        None,
        limpiar_nombre(a),
        limpiar_nombre(b)
    ).ratio()


def comparar_dos_tiendas(productos_a, productos_b, umbral=0.65):
    """
    Algoritmo de Emparejamiento Uno a Uno (One-to-One Product Matching).
    Busca el mejor candidato correlativo y calcula la brecha de precios (ahorro).
    """
    resultados = []
    usados_b = set()  # Control de estado para bloquear productos ya emparejados

    for prod_a in productos_a:
        nombre_a = prod_a.get("nombre", "")
        precio_a = prod_a.get("precio")

        if not precio_a:
            continue

        mejor_match = None
        mejor_score = 0

        for idx_b, prod_b in enumerate(productos_b):
            if idx_b in usados_b:
                continue

            nombre_b = prod_b.get("nombre", "")
            precio_b = prod_b.get("precio")

            if not precio_b:
                continue

            score = similitud(nombre_a, nombre_b)

            if score > mejor_score:
                mejor_score = score
                mejor_match = (idx_b, prod_b)

        if not mejor_match:
            continue

        if mejor_score < umbral:
            continue

        idx_b, prod_b = mejor_match
        usados_b.add(idx_b)  # Bloqueamos el producto de la tienda B para evitar duplicidad

        precio_b = prod_b["precio"]

        # Determinación de márgenes comerciales y ventaja económica
        if precio_a < precio_b:
            mas_barato = "Memory Kings"
            ahorro = precio_b - precio_a
        elif precio_b < precio_a:
            mas_barato = "Impacto"
            ahorro = precio_a - precio_b
        else:
            mas_barato = "Iguales"
            ahorro = 0.0

        resultados.append({
            "nombre_a": nombre_a,
            "nombre_b": prod_b["nombre"],
            "precio_a": precio_a,
            "precio_b": precio_b,
            "url_a": prod_a.get("url", ""),
            "url_b": prod_b.get("url", ""),
            "mas_barato": mas_barato,
            "ahorro": round(ahorro, 2),
            "similitud": round(mejor_score, 3)
        })

    # Ordenamos de mayor a menor ahorro para aportar valor en la UI
    resultados.sort(
        key=lambda x: x["ahorro"],
        reverse=True
    )

    return resultados