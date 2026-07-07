"""
scraper/memory_kings.py  — Memory Kings
Estructura real del HTML:
  <div class="price">$ 880.00 ó S/ 3,044.50</div>
  <div class="stock">Stock: <b>1</b></div>
  <div class="code">Código interno: <b>040627</b></div>
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json, csv, time, re, os

BASE_URL    = "https://www.memorykings.pe"
URL_LAPTOPS = f"{BASE_URL}/subcategorias/19/laptops"
TIENDA      = "Memory Kings"


# ── Driver ────────────────────────────────────────────────────────────────────
def obtener_driver(headless=True):
    op = webdriver.ChromeOptions()
    if headless:
        op.add_argument("--headless")
    op.add_argument("--no-sandbox")
    op.add_argument("--disable-dev-shm-usage")
    op.add_argument("--window-size=1920,1080")
    op.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=op
    )


def _get_html(driver, url, css_wait="ul.products", timeout=15):
    driver.get(url)
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css_wait))
        )
    except Exception:
        pass
    time.sleep(2)
    return driver.page_source


# ── Extraer precio en SOLES desde "$ 880.00 ó S/ 3,044.50" ──────────────────
def _extraer_precio_soles(texto_price):
    """
    Entrada: "$ 880.00 ó S/ 3,044.50"
    Salida : 3044.50  (float)
    """
    if not texto_price:
        return None, "S/D"

    # Buscar el valor DESPUÉS de "S/" o "S/."
    match = re.search(r'[Ss]/\.?\s*([\d,\.]+)', texto_price)
    if match:
        valor_str    = match.group(1).replace(",", "")
        precio_texto = f"S/ {match.group(1)}"
        try:
            v = float(valor_str)
            if v > 50:
                return v, precio_texto
        except Exception:
            pass

    return None, texto_price.strip()


# ── Subcategorías ─────────────────────────────────────────────────────────────
def scrapear_subcategorias_laptops():
    print(f"[MK] Subcategorías: {URL_LAPTOPS}")
    driver = obtener_driver()
    try:
        html = _get_html(driver, URL_LAPTOPS, "ul.products li")
    finally:
        driver.quit()

    soup  = BeautifulSoup(html, "html.parser")
    items = soup.select("ul.products li")
    print(f"[MK] Subcategorías encontradas: {len(items)}")

    resultado = []
    for item in items:
        a      = item.select_one("a")
        if not a:
            continue
        href   = a.get("href", "")
        url    = href if href.startswith("http") else BASE_URL + href
        h4     = a.select_one("h4")
        img    = a.select_one("img")
        nombre = h4.get_text(strip=True) if h4 else (img.get("alt","") if img else "")
        resultado.append({
            "nombre": nombre,
            "url"   : url,
            "imagen": img.get("src","") if img else ""
        })
    return resultado


# ── Productos de un listado ───────────────────────────────────────────────────
def scrapear_productos_listado(url_listado, max_paginas=3):
    print(f"[MK] Scrapeando: {url_listado}")
    driver    = obtener_driver()
    productos = []

    try:
        for pagina in range(1, max_paginas + 1):
            url_pag = url_listado if pagina == 1 else f"{url_listado}?pagina={pagina}"

            try:
                html = _get_html(driver, url_pag, "ul.products", timeout=15)
            except Exception:
                print(f"[MK] No cargó página {pagina}.")
                break

            soup  = BeautifulSoup(html, "html.parser")
            cards = soup.select("ul.products > li")

            if not cards:
                print(f"[MK] Sin tarjetas en página {pagina}.")
                break

            antes = len(productos)

            for card in cards:
                # ── Nombre ──────────────────────────────────────────────────
                h4     = card.select_one(".title h4")
                nombre = h4.get_text(strip=True) if h4 else ""
                if not nombre:
                    continue

                # ── Precio: selector exacto div.price ────────────────────────
                price_el     = card.select_one("div.price")
                price_texto  = price_el.get_text(strip=True) if price_el else ""
                precio, precio_txt = _extraer_precio_soles(price_texto)

                # ── Stock ────────────────────────────────────────────────────
                stock_el = card.select_one("div.stock b")
                stock    = stock_el.get_text(strip=True) if stock_el else "?"

                # ── Código interno ───────────────────────────────────────────
                code_el = card.select_one("div.code b")
                codigo  = code_el.get_text(strip=True) if code_el else ""

                # ── URL producto ─────────────────────────────────────────────
                a_tag = card.select_one("a[href]")
                href  = a_tag.get("href","") if a_tag else ""
                url_p = href if href.startswith("http") else BASE_URL + href

                # ── Imagen ───────────────────────────────────────────────────
                img    = card.select_one("img")
                imagen = img.get("src","") if img else ""

                productos.append({
                    "nombre"      : nombre,
                    "precio"      : precio,
                    "precio_texto": precio_txt,
                    "stock"       : stock,
                    "codigo"      : codigo,
                    "url"         : url_p,
                    "imagen"      : imagen,
                    "tienda"      : TIENDA,
                })

            nuevos     = len(productos) - antes
            con_precio = sum(1 for p in productos[-nuevos:] if p["precio"])
            print(f"[MK]   Pág {pagina}: {nuevos} productos  ({con_precio} con precio S/)")

            if nuevos == 0:
                break

    finally:
        driver.quit()

    # ─────────────────────────────────────────────
    # ELIMINAR DUPLICADOS
    # ─────────────────────────────────────────────

    productos_unicos = {}
    duplicados = 0

    for p in productos:

        nombre = (
            p.get("nombre", "")
            .lower()
            .strip()
        )

        nombre = " ".join(nombre.split())

        if nombre not in productos_unicos:
            productos_unicos[nombre] = p
        else:
            duplicados += 1

    productos = list(productos_unicos.values())

    print(
        f"[MK] Productos únicos: {len(productos)} "
        f"(duplicados eliminados: {duplicados})"
    )

    return productos


# ── Búsqueda por término ──────────────────────────────────────────────────────
def buscar_productos(termino, max_paginas=2):
    url = f"{BASE_URL}/resultados/{termino.replace(' ', '+')}"
    return scrapear_productos_listado(url, max_paginas)


# ── Guardar ───────────────────────────────────────────────────────────────────
def guardar_json(datos, archivo="archivos/productos_mk.json"):
    os.makedirs("archivos", exist_ok=True)
    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    print(f"[OK] JSON → {archivo}")

def guardar_csv(datos, archivo="archivos/productos_mk.csv"):
    os.makedirs("archivos", exist_ok=True)
    if not datos:
        return
    with open(archivo, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=datos[0].keys())
        w.writeheader()
        w.writerows(datos)
    print(f"[OK] CSV  → {archivo}")

def mostrar_resultados(datos):
    print(f"\n{'='*70}")
    print(f"  {TIENDA}  ({len(datos)} productos)")
    print(f"{'='*70}")
    for i, p in enumerate(datos, 1):
        precio_str = f"S/ {p['precio']:>10,.2f}" if p.get("precio") else f"{'S/D':>13}"
        stock_str  = f"Stock: {p.get('stock','?'):>3}"
        print(f"[{i:02d}] {p['nombre'][:58]:<58}  {precio_str}  {stock_str}")
    print()


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    datos = buscar_productos("laptop core i7", max_paginas=1)
    mostrar_resultados(datos)
    guardar_json(datos)
    guardar_csv(datos)