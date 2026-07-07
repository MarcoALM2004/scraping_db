"""
debug_tiendas.py — guarda el HTML de Sercoplus
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import os

TERMINO = "laptop core i7"
URL = f"https://sercoplus.com/buscar?controller=search&s={TERMINO.replace(' ', '+')}"

op = webdriver.ChromeOptions()
op.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=op
)

print(f"Abriendo Sercoplus: {URL}")

driver.get(URL)

time.sleep(7)

driver.execute_script(
    "window.scrollTo(0, document.body.scrollHeight);"
)

time.sleep(2)

ruta = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "debug_sercoplus.html"
)

with open(ruta, "w", encoding="utf-8") as f:
    f.write(driver.page_source)

print(f"Guardado: {ruta}")
print(f"Titulo: {driver.title}")

input("ENTER para cerrar...")

driver.quit()