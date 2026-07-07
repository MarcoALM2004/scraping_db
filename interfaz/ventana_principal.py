"""
interfaz/ventana_principal.py
Validación de extracción de productos:
Memory Kings vs Impacto
"""
import random
from datetime import datetime
from db.conexion import conectar
from export.export_excel import exportar_a_excel
from tkinter import simpledialog, messagebox,ttk
import tkinter as tk
import threading
import sys
import os

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            ".."
        )
    )
)

from scraper.memory_kings import buscar_productos as mk_buscar
from scraper.impacto import buscar_productos as imp_buscar


# ──────────────────────────────────────────────────────────────
# COLORES
# ──────────────────────────────────────────────────────────────

BG = "#1a1a2e"
PANEL = "#16213e"
ACCENT = "#7c3aed"

TEXT = "#f1f5f9"
MUTED = "#94a3b8"

ROW_A = "#1e293b"
ROW_B = "#0f172a"


# ──────────────────────────────────────────────────────────────
# GENERAR CODIGO
# ──────────────────────────────────────────────────────────────
def generar_codigo():
    fecha = datetime.now().strftime("%Y%m%d")
    rand = random.randint(100, 999)
    return f"EXP-{fecha}-{rand}"


# ──────────────────────────────────────────────────────────────
# APP
# ──────────────────────────────────────────────────────────────

class ComparadorApp(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("Extracción de Productos · Memory Kings vs Impacto")
        self.geometry("1300x750")
        self.minsize(900, 600)

        self.configure(bg=BG)

        self._construir_ui()

    # ──────────────────────────────────────────────────────────

    def _construir_ui(self):

        # HEADER
        header = tk.Frame(
            self,
            bg=ACCENT,
            pady=12
        )
        header.pack(fill="x")

        tk.Label(
            header,
            text="💻 Validación de Extracción de Productos",
            font=("Segoe UI", 20, "bold"),
            bg=ACCENT,
            fg="white"
        ).pack()

        tk.Label(
            header,
            text="Memory Kings · Impacto",
            font=("Segoe UI", 10),
            bg=ACCENT,
            fg="#ddd6fe"
        ).pack()

        # BARRA BUSQUEDA

        barra = tk.Frame(
            self,
            bg=PANEL,
            pady=12
        )
        barra.pack(fill="x")

        tk.Label(
            barra,
            text="Buscar:",
            bg=PANEL,
            fg=TEXT,
            font=("Segoe UI", 11)
        ).pack(
            side="left",
            padx=(16, 6)
        )

        self.entrada = tk.Entry(
            barra,
            font=("Segoe UI", 12),
            width=40,
            bg="#1e293b",
            fg=TEXT,
            insertbackground="white",
            relief="flat",
            bd=8
        )

        self.entrada.insert(
            0,
            "laptop core i5"
        )

        self.entrada.pack(
            side="left"
        )

        self.entrada.bind(
            "<Return>",
            lambda e: self._iniciar_busqueda()
        )

        self.btn = tk.Button(
            barra,
            text="▶ Buscar",
            font=("Segoe UI", 11, "bold"),
            bg=ACCENT,
            fg="white",
            relief="flat",
            command=self._iniciar_busqueda
        )

        self.btn.pack(
            side="left",
            padx=10
        )

        tk.Label(
            barra,
            text="Páginas:",
            bg=PANEL,
            fg=MUTED
        ).pack(
            side="left",
            padx=(15, 5)
        )

        self.var_pags = tk.IntVar(value=2)

        tk.Spinbox(
            barra,
            from_=1,
            to=5,
            width=3,
            textvariable=self.var_pags
        ).pack(side="left")

        # STATUS

        self.var_status = tk.StringVar(
            value="Listo para buscar."
        )

        tk.Label(
            self,
            textvariable=self.var_status,
            bg=BG,
            fg=MUTED,
            anchor="w",
            padx=14
        ).pack(fill="x")

        # PROGRESS

        self.progreso = ttk.Progressbar(
            self,
            mode="indeterminate"
        )

        # TABLA

        frame = tk.Frame(
            self,
            bg=BG
        )

        frame.pack(
            fill="both",
            expand=True,
            padx=14,
            pady=10
        )

        columnas = (
            "tienda",
            "producto",
            "precio"
        )

        self.tabla = ttk.Treeview(
            frame,
            columns=columnas,
            show="headings"
        )

        self.tabla.heading(
            "tienda",
            text="Tienda"
        )

        self.tabla.heading(
            "producto",
            text="Producto"
        )

        self.tabla.heading(
            "precio",
            text="Precio"
        )

        self.tabla.column(
            "tienda",
            width=150,
            anchor="center"
        )

        self.tabla.column(
            "producto",
            width=850,
            anchor="w"
        )

        self.tabla.column(
            "precio",
            width=150,
            anchor="center"
        )

        scrollbar = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=self.tabla.yview
        )

        self.tabla.configure(
            yscrollcommand=scrollbar.set
        )

        self.tabla.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(
            "Treeview",
            background=ROW_B,
            foreground=TEXT,
            fieldbackground=ROW_B,
            rowheight=28
        )

        style.configure(
        "Treeview",
        background=ROW_B,
        foreground=TEXT,
        fieldbackground=ROW_B,
        rowheight=28
        )

        # BOTON EXPORTAR
        btn_exportar = tk.Button(
        self,
        text="📊 Exportar a Excel",
        bg="#10b981",
        fg="white",
        font=("Segoe UI", 11, "bold"),
        command=self._exportar_excel
        )

        btn_exportar.pack(pady=10)

        # BOTON GUARDAR
        tk.Button(
        self,
        text="💾 Guardar en MySQL",
        bg="#3b82f6",
        fg="white",
        font=("Segoe UI", 11, "bold"),
        command=self.guardar_en_bd
    ).pack(pady=5)
    # ──────────────────────────────────────────────────────────

    def _iniciar_busqueda(self):

        termino = self.entrada.get().strip()

        if not termino:

            messagebox.showwarning(
                "Aviso",
                "Escribe algo para buscar."
            )

            return

        self.btn.config(
            state="disabled",
            text="Buscando..."
        )

        self.tabla.delete(
            *self.tabla.get_children()
        )

        self.progreso.pack(
            fill="x",
            padx=14
        )

        self.progreso.start(10)

        threading.Thread(
            target=self._worker,
            args=(
                termino,
                self.var_pags.get()
            ),
            daemon=True
        ).start()

    # ──────────────────────────────────────────────────────────

    def _worker(self, termino, paginas):

        try:

            self._set_status(
                "Buscando en Memory Kings..."
            )

            mk = mk_buscar(
                termino,
                max_paginas=paginas
            )

            self._set_status(
                "Buscando en Impacto..."
            )

            imp = imp_buscar(
                termino,
                max_paginas=paginas
            )

            self.after(
                0,
                self._mostrar_productos,
                mk,
                imp
            )

        except Exception as e:

            self.after(
                0,
                self._error,
                str(e)
            )

    # ──────────────────────────────────────────────────────────

    def _mostrar_productos(self, mk, imp):

        self.progreso.stop()
        self.progreso.pack_forget()

        self.btn.config(
            state="normal",
            text="▶ Buscar"
        )

        self.tabla.delete(
            *self.tabla.get_children()
        )

        # MEMORY KINGS

        for producto in mk:

            precio = producto.get("precio")

            self.tabla.insert(
                "",
                "end",
                values=(
                    "Memory Kings",
                    producto.get("nombre", "")[:150],
                    f"S/ {precio:.2f}" if precio else "S/D"
                )
            )

        # IMPACTO

        for producto in imp:

            precio = producto.get("precio")

            self.tabla.insert(
                "",
                "end",
                values=(
                    "Impacto",
                    producto.get("nombre", "")[:150],
                    f"S/ {precio:.2f}" if precio else "S/D"
                )
            )

        self.var_status.set(
            f"Memory Kings: {len(mk)} productos | "
            f"Impacto: {len(imp)} productos"
        )

    # ──────────────────────────────────────────────────────────

    def _set_status(self, texto):

        self.after(
            0,
            self.var_status.set,
            texto
        )

    # ──────────────────────────────────────────────────────────

    def _error(self, msg):

        self.progreso.stop()
        self.progreso.pack_forget()

        self.btn.config(
            state="normal",
            text="▶ Buscar"
        )

        messagebox.showerror(
            "Error",
            msg
        )

        self.var_status.set(
            f"Error: {msg}"
        )

# ──────────────────────────────────────────────────────────────
    
    def _exportar_excel(self):

        datos = []

        for item in self.tabla.get_children():
            datos.append(self.tabla.item(item)["values"])

        self._guardar_excel(datos)

# ──────────────────────────────────────────────────────────────

    def _guardar_excel(self, datos):

        import pandas as pd
        import os
        from tkinter import messagebox

        carpeta = "data"
        os.makedirs(carpeta, exist_ok=True)

        ruta = os.path.join(carpeta, "productos.xlsx")

        df = pd.DataFrame(datos, columns=["Tienda", "Producto", "Precio"])

        df.to_excel(ruta, index=False)

        messagebox.showinfo("OK", f"Excel guardado en:\n{ruta}")
# ──────────────────────────────────────────────────────────────
    def guardar_en_bd(self):

        # 1. pedir nombre del historial
        nombre = simpledialog.askstring(
            "Guardar historial",
            "Ingresa el nombre del guardado:"
        )

        if not nombre:
            messagebox.showwarning("Aviso", "Debes ingresar un nombre")
            return

        # 2. generar código único
        codigo = generar_codigo()

        conn = conectar()
        cursor = conn.cursor()

        # ─────────────────────────────
        # 3. guardar en HISTORIAL
        # ─────────────────────────────
        sql_historial = """
            INSERT INTO historial (codigo, nombre)
            VALUES (%s, %s)
        """

        cursor.execute(sql_historial, (codigo, nombre))

        # ─────────────────────────────
        # 4. guardar productos
        # ─────────────────────────────
        datos = []

        for item in self.tabla.get_children():
            valores = self.tabla.item(item)["values"]

            tienda = valores[0]
            producto = valores[1]
            precio = valores[2]

            try:
                precio = float(precio.replace("S/", "").strip())
            except:
                precio = None

            datos.append((codigo, tienda, producto, precio))

        sql_productos = """
            INSERT INTO productos (codigo, tienda, producto, precio)
            VALUES (%s, %s, %s, %s)
        """

        cursor.executemany(sql_productos, datos)

        conn.commit()
        conn.close()

        messagebox.showinfo("OK",f"Guardado exitoso:\n\nNombre: {nombre}\nCódigo: {codigo}")

# ──────────────────────────────────────────────────────────────

def main():

    app = ComparadorApp()
    app.mainloop()


if __name__ == "__main__":
    main()

