"""
scraper/impacto.py  — Importaciones Impacto (impacto.com.pe)
Next.js SPA — requiere Selenium para renderizar el JS.

Estructura real del HTML:
  <a class="block h-full" href="/producto/...">
    <h3 class="font-bold text-[#333]...">NOMBRE</h3>
    <span class="text-2xl sm:text-[26px] font-bold text-[#333]...">S/ 4,549.90</span>
    <span ...>CÓD:  022273</span>
    <span ...>STOCK : 1</span>
  </a>
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time, re

BASE_URL     = "https://www.impacto.com.pe"
TIENDA       = "Impacto"
URL_BUSQUEDA = f"{BASE_URL}/search?q="


def obtener_driver(headless=True):
    op = webdriver.ChromeOptions()
    if headless:
        op.add_argument("--headless")
    op.add_argument("--no-sandbox")
    op.add_argument("--disable-dev-shm-usage")
    op.add_argument("--window-size=1920,1080")
    op.add_argument("--disable-blink-features=AutomationControlled")
    op.add_experimental_option("excludeSwitches", ["enable-automation"])
    op.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=op
    )


def _limpiar_precio(texto):
    """Extrae float de 'S/ 4,549.90' → 4549.90"""
    if not texto:
        return None
    texto = texto.replace(",", "")
    nums  = re.findall(r"\d+\.?\d*", texto)
    for n in nums:
        try:
            v = float(n)
            if v > 50:
                return v
        except Exception:
            pass
    return None


def _parsear_impacto(html):
    """
    Selector exacto basado en el HTML real de Impacto (Next.js).
    Cada producto es un <a class="block h-full" href="/producto/...">
    """
    soup      = BeautifulSoup(html, "html.parser")
    productos = []

    # Todas las tarjetas de producto
    cards = soup.select('a.block[href^="/producto/"]')

    for card in cards:
        # ── Nombre ──────────────────────────────────────────────────────────
        h3 = card.select_one("h3")
        nombre = h3.get_text(strip=True) if h3 else ""
        if not nombre or len(nombre) < 5:
            continue

        # ── Precio principal en soles ────────────────────────────────────────
        # Es el <span> con clase "text-2xl" que contiene "S/"
        precio_el = card.select_one('span.text-2xl, span[class*="text-2xl"]')
        precio_texto = precio_el.get_text(strip=True) if precio_el else ""

        # Fallback: buscar cualquier texto con "S/" en la card
        if not precio_texto or "S/" not in precio_texto:
            for el in card.find_all("span"):
                t = el.get_text(strip=True)
                if t.startswith("S/") and re.search(r"\d{3}", t):
                    precio_texto = t
                    break

        precio = _limpiar_precio(precio_texto)

        # ── Stock ────────────────────────────────────────────────────────────
        stock = ""
        for sp in card.find_all("span"):
            t = sp.get_text(strip=True)
            if "STOCK" in t.upper():
                stock = t.replace("STOCK :", "").replace("STOCK:", "").strip()
                break

        # ── Código ───────────────────────────────────────────────────────────
        codigo = ""
        for sp in card.find_all("span"):
            t = sp.get_text(strip=True)
            if "CÓD" in t.upper() or "COD" in t.upper():
                codigo = re.sub(r"C[ÓO]D[:\s]*", "", t, flags=re.IGNORECASE).strip()
                break

        # ── URL ──────────────────────────────────────────────────────────────
        href = card.get("href", "")
        url  = BASE_URL + href if href.startswith("/") else href

        # ── Imagen ───────────────────────────────────────────────────────────
        img    = card.select_one("img")
        imagen = ""
        if img:
            # Next.js usa srcset con URLs absolutas de Google Storage
            srcset = img.get("srcset","")
            if srcset:
                # Primer src del srcset (256w)
                primera = srcset.split(",")[0].strip().split(" ")[0]
                imagen  = primera
            else:
                imagen = img.get("src","")

        productos.append({
            "nombre"      : nombre,
            "precio"      : precio,
            "precio_texto": precio_texto or "S/D",
            "stock"       : stock,
            "codigo"      : codigo,
            "url"         : url,
            "imagen"      : imagen,
            "tienda"      : TIENDA,
        })

    return productos


def buscar_productos(termino, max_paginas=2):
    """Busca un término en Impacto y retorna lista de productos."""
    
    print(f"[IMP] Buscando: '{termino}'")

    driver = obtener_driver()
    productos = []

    try:
        for pagina in range(1, max_paginas + 1):

            url = f"{URL_BUSQUEDA}{termino.replace(' ', '+')}"

            if pagina > 1:
                url += f"&page={pagina}"

            print(f"[IMP] Página {pagina}: {url}")

            driver.get(url)

            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located(
                        (
                            By.CSS_SELECTOR,
                            'a.block[href^="/producto/"]'
                        )
                    )
                )
            except Exception:
                print(f"[IMP] Timeout esperando productos pág {pagina}")

            time.sleep(2)

            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight/2);"
            )

            time.sleep(1)

            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )

            time.sleep(1)

            cards = _parsear_impacto(driver.page_source)

            if not cards:
                print(f"[IMP] Sin productos en página {pagina}.")
                break

            productos.extend(cards)

            con_precio = sum(
                1 for p in cards
                if p["precio"]
            )

            print(
                f"[IMP] {len(cards)} productos "
                f"({con_precio} con precio)"
            )

            soup = BeautifulSoup(
                driver.page_source,
                "html.parser"
            )

            next_btn = soup.select_one(
                ".ais-Pagination-item--nextPage:not(.ais-Pagination-item--disabled) a"
            )

            if not next_btn:
                print("[IMP] No hay más páginas.")
                break

    except Exception as e:
        print(f"[IMP] Error: {e}")

    finally:
        driver.quit()

    # --------------------------------------------------
    # ELIMINAR DUPLICADOS
    # --------------------------------------------------

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
        f"[IMP] Productos únicos: {len(productos)} "
        f"(duplicados eliminados: {duplicados})"
    )

    return productos


def scrapear_laptops(max_paginas=2):
    return buscar_productos("laptop", max_paginas)


if __name__ == "__main__":
    datos = buscar_productos("laptop core i7", max_paginas=1)
    for i, p in enumerate(datos, 1):
        precio = f"S/ {p['precio']:,.2f}" if p.get("precio") else p.get("precio_texto", "S/D")
        print(f"[{i:02d}] {p['nombre'][:58]:<58}  {precio}  Stock:{p['stock']}")