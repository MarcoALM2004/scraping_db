"""
main.py - Punto de entrada del proyecto ProyectoScraping
Lanza la interfaz gráfica comparadora de laptops.
"""

import sys
import os

# Asegura que el directorio raíz esté en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from interfaz.ventana_principal import main

if __name__ == "__main__":
    main()