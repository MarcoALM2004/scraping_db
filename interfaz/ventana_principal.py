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
from interfaz.ventana_historial import HistorialApp
from scraper.comparador import comparar_dos_tiendas
import pandas as pd
import os
import tkinter as tk
import threading
import sys
import os
import re



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
# CATEGORÍAS DE PROCESADOR (para el filtro)
# ──────────────────────────────────────────────────────────────
PATRONES_PROCESADOR = {
    "Core i3": r"\bi3\b",
    "Core i5": r"\bi5\b",
    "Core i7": r"\bi7\b",
    "Core i9": r"\bi9\b",
    "Core Ultra 5": r"ultra\s*5\b",
    "Core Ultra 7": r"ultra\s*7\b",
    "Core Ultra 9": r"ultra\s*9\b",
    "Ryzen 3": r"ryzen\s*3\b",
    "Ryzen 5": r"ryzen\s*5\b",
    "Ryzen 7": r"ryzen\s*7\b",
    "Ryzen 9": r"ryzen\s*9\b",
    "Ryzen AI 7": r"ryzen\s*ai\s*7\b",
    "Ryzen AI 9": r"ryzen\s*ai\s*9\b",
    "Celeron": r"celeron",
    "N150": r"\bn150\b",
}

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

        # Variables de estado internas para almacenar la búsqueda actual en bruto
        self.productos_mk_actuales = []
        self.productos_imp_actuales = []

        self.productos_mk_filtrados = []
        self.productos_imp_filtrados = []

        # Relaciona cada fila de la tabla con su enlace real
        self.enlaces_por_item = {}

        # Estado del filtro por procesador
        self.categorias_seleccionadas = {}
        self.filtro_visible = False

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

        # BOTÓN FILTRAR

        self.btn_filtro = tk.Button(
            barra,
            text="🎚️ Filtrar ▾",
            font=("Segoe UI", 11, "bold"),
            bg="#0ea5e9",
            fg="white",
            relief="flat",
            command=self._toggle_panel_filtro
        )

        self.btn_filtro.pack(
            side="left",
            padx=10
        )

        # STATUS

        self.var_status = tk.StringVar(
            value="Listo para buscar."
        )

        self.lbl_status = tk.Label(
            self,
            textvariable=self.var_status,
            bg=BG,
            fg=MUTED,
            anchor="w",
            padx=14
        )

        self.lbl_status.pack(fill="x")

        # PANEL DE FILTRO POR PROCESADOR

        self.panel_filtro = tk.Frame(
            self,
            bg=PANEL,
            pady=6
        )

        fila_checks = tk.Frame(
            self.panel_filtro,
            bg=PANEL
        )

        fila_checks.pack(
            padx=16,
            pady=(6, 2),
            anchor="w"
        )

        for i, categoria in enumerate(PATRONES_PROCESADOR.keys()):
            variable = tk.IntVar(value=0)

            self.categorias_seleccionadas[categoria] = variable

            tk.Checkbutton(
                fila_checks,
                text=categoria,
                variable=variable,
                bg=PANEL,
                fg=TEXT,
                selectcolor="#334155",
                activebackground=PANEL,
                activeforeground=TEXT,
                font=("Segoe UI", 9)
            ).grid(
                row=i // 5,
                column=i % 5,
                sticky="w",
                padx=10,
                pady=4
            )

        fila_botones_filtro = tk.Frame(
            self.panel_filtro,
            bg=PANEL
        )

        fila_botones_filtro.pack(
            padx=16,
            pady=(2, 8),
            anchor="w"
        )

        tk.Button(
            fila_botones_filtro,
            text="✔️ Aplicar filtro",
            bg=ACCENT,
            fg="white",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            command=self._aplicar_filtro_procesador
        ).pack(
            side="left",
            padx=(0, 8)
        )

        tk.Button(
            fila_botones_filtro,
            text="✖️ Limpiar filtro",
            bg="#6b7280",
            fg="white",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            command=self._limpiar_filtro_procesador
        ).pack(side="left")
        

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
            "precio",
            "enlace"
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

        self.tabla.heading(
            "enlace",
            text="Enlace"
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

        self.tabla.column(
            "enlace",
            width=140,
            anchor="center",
            stretch=False
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

        self.tabla.bind(
            "<ButtonRelease-1>",
            self._copiar_enlace_desde_tabla
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
        # COLORES PARA COMPARACIÓN
        self.tabla.tag_configure(
            "mk_gana",
            background="#1e3a8a",
            foreground="white"
        )

        self.tabla.tag_configure(
            "imp_gana",
            background="#065f46",
            foreground="white"
        )

        self.tabla.tag_configure(
            "iguales",
            background="#334155",
            foreground="white"
        )

        # PANEL DE BOTONES HORIZONTAL
        panel_botones = tk.Frame(
            self,
            bg=BG
        )

        panel_botones.pack(
            pady=10
        )

        #Botton para vcomparar precios

        btn_comparar = tk.Button(
        panel_botones,
        text="🔍 Comparar precios",
        bg="#f97316",
        fg="white",
        font=("Segoe UI",11,"bold"),
        command=self.comparar_productos
    )

        btn_comparar.pack(
            side="left",
            padx=5
    )

        # BOTON EXPORTAR
        btn_exportar = tk.Button(
        panel_botones,
        text="📊 Exportar a Excel",
        bg="#10b981",
        fg="white",
        font=("Segoe UI", 11, "bold"),
        command=self._exportar_excel
        )

        btn_exportar.pack(
            side="left",
            padx=5
        )

        # BOTON GUARDAR
        tk.Button(
        panel_botones,
        text="💾 Guardar la tabla",
        bg="#3b82f6",
        fg="white",
        font=("Segoe UI", 11, "bold"),
        command=self.guardar_en_bd
    ).pack(
        side="left",
        padx=5
    )

        #Botton para ver historial

        btn_historial = tk.Button(
        panel_botones,
        text="📂 Historial",
        bg="#EFBF04",
        fg="white",
        font=("Segoe UI",11,"bold"),
        command=self.abrir_historial
    )

        btn_historial.pack(
            side="left",
            padx=5
    )

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

    def _toggle_panel_filtro(self):
        if self.filtro_visible:
            self.panel_filtro.pack_forget()
            self.filtro_visible = False
            self.btn_filtro.config(text="🎚️ Filtrar ▾")

        else:
            self.panel_filtro.pack(
                fill="x",
                after=self.lbl_status
            )

            self.filtro_visible = True
            self.btn_filtro.config(text="🎚️ Filtrar ▲")

    # ──────────────────────────────────────────────────────────

    def _producto_coincide(self, nombre, categorias_activas):
        nombre = nombre.lower()

        for categoria in categorias_activas:
            patron = PATRONES_PROCESADOR[categoria]

            if re.search(patron, nombre):
                return True

        return False
    
    # ──────────────────────────────────────────────────────────
    def _aplicar_filtro_procesador(self):
        if not self.productos_mk_actuales and not self.productos_imp_actuales:
            messagebox.showwarning(
                "Aviso",
                "Primero realiza una búsqueda para poder filtrar."
            )
            return

        categorias_activas = [
            categoria
            for categoria, variable in self.categorias_seleccionadas.items()
            if variable.get() == 1
        ]

        if not categorias_activas:

            self.productos_mk_filtrados = self.productos_mk_actuales
            self.productos_imp_filtrados = self.productos_imp_actuales

            self._mostrar_productos(
                self.productos_mk_actuales,
                self.productos_imp_actuales
            )

            self.var_status.set(
                "Sin filtro. Mostrando todos los productos."
            )

            return

        mk_filtrados = [
            producto
            for producto in self.productos_mk_actuales
            if self._producto_coincide(
                producto.get("nombre", ""),
                categorias_activas
            )
        ]

        impacto_filtrados = [
            producto
            for producto in self.productos_imp_actuales
            if self._producto_coincide(
                producto.get("nombre", ""),
                categorias_activas
            )
        ]

        self.productos_mk_filtrados = mk_filtrados
        self.productos_imp_filtrados = impacto_filtrados

        self._mostrar_productos(
            mk_filtrados,
            impacto_filtrados
        )

        self.var_status.set(
            f"Filtro aplicado: {', '.join(categorias_activas)} | "
            f"Memory Kings: {len(mk_filtrados)} | "
            f"Impacto: {len(impacto_filtrados)}"
        )
    # ──────────────────────────────────────────────────────────

    def _limpiar_filtro_procesador(self):
        for variable in self.categorias_seleccionadas.values():
            variable.set(0)

        if not self.productos_mk_actuales and not self.productos_imp_actuales:
            self.var_status.set(
                "No hay productos para restaurar."
            )
            return
        self.productos_mk_filtrados = self.productos_mk_actuales
        self.productos_imp_filtrados = self.productos_imp_actuales

        self._mostrar_productos(
            self.productos_mk_actuales,
            self.productos_imp_actuales
        )

        self.var_status.set(
            "Filtro eliminado. Mostrando todos los productos."
        )
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

            self.productos_mk_actuales = mk
            self.productos_imp_actuales = imp

            self.productos_mk_filtrados = mk
            self.productos_imp_filtrados = imp

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

    def _copiar_enlace_desde_tabla(self, event):

        region = self.tabla.identify_region(
            event.x,
            event.y
        )

        if region != "cell":
            return

        columna = self.tabla.identify_column(event.x)

        # Solo funciona al hacer clic en la cuarta columna
        if columna != "#4":
            return

        item_id = self.tabla.identify_row(event.y)

        if not item_id:
            return

        enlace = self.enlaces_por_item.get(item_id, "")

        if not enlace:
            messagebox.showwarning(
                "Enlace no disponible",
                "Este producto no tiene un enlace registrado."
            )
            return

        # Copiar al portapapeles
        self.clipboard_clear()
        self.clipboard_append(enlace)
        self.update()

        # Obtener los valores actuales de la fila
        valores = list(
            self.tabla.item(item_id, "values")
        )

        # Cambiar temporalmente la cuarta columna
        valores[3] = "✅ Copiado"

        self.tabla.item(
            item_id,
            values=valores
        )

        # Mostrar confirmación en la parte inferior
        self.var_status.set(
            "✅ Enlace copiado. Ya puedes pegarlo con Ctrl + V."
        )

        # Después de 2 segundos vuelve a mostrar el icono
        self.after(
            2000,
            lambda: self._restaurar_texto_enlace(item_id)
        )

    # ────────────────────────────────────────────────────────── 
    def _restaurar_texto_enlace(self, item_id):

        # Verifica que la fila todavía exista
        if not self.tabla.exists(item_id):
            return

        valores = list(
            self.tabla.item(item_id, "values")
        )

        enlace = self.enlaces_por_item.get(item_id, "")

        if enlace:
            valores[3] = "📋 Copiar"
        else:
            valores[3] = "No disponible"

        self.tabla.item(
            item_id,
            values=valores
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

        # Limpiamos los enlaces asociados a filas anteriores
        self.enlaces_por_item.clear()

        # MEMORY KINGS
        for producto in mk:

            precio = producto.get("precio")

            enlace = (
                producto.get("url")
                or producto.get("link")
                or producto.get("enlace")
                or ""
            )

            item_id = self.tabla.insert(
                "",
                "end",
                values=(
                    "Memory Kings",
                    producto.get("nombre", "")[:150],
                    f"S/ {precio:.2f}" if precio else "S/D",
                    "📝 Copiar" 
                        if enlace 
                            else "No disponible"
                )
            )

            self.enlaces_por_item[item_id] = enlace

        # IMPACTO
        for producto in imp:

            precio = producto.get("precio")

            enlace = (
                producto.get("url")
                or producto.get("link")
                or producto.get("enlace")
                or ""
            )

            item_id = self.tabla.insert(
                "",
                "end",
                values=(
                    "Impacto",
                    producto.get("nombre", "")[:150],
                    f"S/ {precio:.2f}" if precio else "S/D",
                    "📋 Copiar" if enlace else "No disponible"
                )
            )

            self.enlaces_por_item[item_id] = enlace

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

            valores = self.tabla.item(item)["values"]

            enlace = self.enlaces_por_item.get(item, "")

            datos.append([
                valores[0],
                valores[1],
                valores[2],
                enlace
            ])

        self._guardar_excel(datos)

# ──────────────────────────────────────────────────────────────

    def _guardar_excel(self, datos):

        carpeta = "data"
        os.makedirs(
            carpeta, exist_ok=True
            )

        ruta = os.path.join(
            carpeta, "productos.xlsx"
            )

        df = pd.DataFrame(
            datos,columns=["Tienda", "Producto", "Precio", "Enlace"]
        )
        try:

            df.to_excel(
                ruta,
                index=False
            )

            messagebox.showinfo(
                "OK", f"Excel guardado en:\n{ruta}"
                )

        except PermissionError:

            messagebox.showwarning(
                "Archivo abierto",

                "Cierre el Excel y vuelva a intentar exportar."
            )


        except Exception as e:

            messagebox.showerror(
                "Error",
                str(e)
            )


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
        
        # Verificar si el nombre ya existe
        conn = conectar()
        cursor = conn.cursor()

        sql_verificar = """
        SELECT COUNT(*) 
        FROM historial
        WHERE nombre = %s
        """

        cursor.execute(
            sql_verificar,
            (nombre,)
        )

        existe = cursor.fetchone()[0]

        if existe > 0:
            conn.close()

            messagebox.showwarning(
                "Nombre existente",
                "Ya existe un historial con ese nombre.\nIngrese otro nombre."
            )

            return

        conn.close()

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

        try:

            cursor.execute(
                sql_historial,
                (codigo, nombre)
            )

        except Exception as e:

            conn.rollback()
            conn.close()

            messagebox.showerror(
                "Error",
                f"No se pudo guardar el historial:\n{e}"
            )

            return

        # ─────────────────────────────
        # 4. guardar productos
        # ─────────────────────────────
        datos = []

        for item in self.tabla.get_children():
            valores = self.tabla.item(item)["values"]

            tienda = valores[0]
            producto = valores[1]
            precio = valores[2]
            enlace = self.enlaces_por_item.get(item, "")
            precio_comparacion = None

            # Si es una comparación guarda el precio completo como texto
            if "Match" in producto:

                precio_comparacion = precio
                precio = None

            else:

                try:
                    precio = float(
                        precio.replace("S/", "").strip()
                    )

                except:
                    precio = None


            datos.append(
                (
                    codigo,
                    tienda,
                    producto,
                    precio,
                    precio_comparacion,
                    enlace
                )
            )

        sql_productos = """
            INSERT INTO productos (
                codigo,
                tienda,
                producto,
                precio,
                precio_comparacion,
                enlace
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        cursor.executemany(sql_productos, datos)

        conn.commit()
        conn.close()

        messagebox.showinfo("OK",f"Guardado exitoso:\n\nNombre: {nombre}\nCódigo: {codigo}")

# ──────────────────────────────────────────────────────────────

    def comparar_productos(self):

        if not hasattr(self, "productos_mk_actuales"):

            messagebox.showwarning(
                "Aviso",
                "Primero realiza una búsqueda"
            )

            return


        resultados = comparar_dos_tiendas(
            self.productos_mk_filtrados,
            self.productos_imp_filtrados,
            umbral=0.45
        )

        self.tabla.delete(
            *self.tabla.get_children()
        )

        self.enlaces_por_item.clear()

        for item in resultados:

            mas_barato = item["mas_barato"]
            ahorro = item["ahorro"]

            similitud_pct = int(item["similitud"] * 100)

            texto_producto = (
                f"[{similitud_pct}% Match] "
                f"MK: {item['nombre_a'][:55]}... │ "
                f"IMP: {item['nombre_b'][:55]}..."
            )

            texto_precio = (
                f"MK: S/ {item['precio_a']:.2f} │ "
                f"IMP: S/ {item['precio_b']:.2f}"
            )

            if ahorro > 0 and mas_barato != "Iguales":
                texto_precio += (
                    f" (Ahorras S/ {ahorro:.2f})"
                )

            enlace_mk = (
                item.get("url_a")
                or item.get("enlace_a")
                or item.get("link_a")
                or ""
            )

            enlace_imp = (
                item.get("url_b")
                or item.get("enlace_b")
                or item.get("link_b")
                or ""
            )

            if mas_barato == "Memory Kings":

                tienda = "⭐ Memory Kings"
                color = "mk_gana"
                enlace_ganador = enlace_mk

            elif mas_barato == "Impacto":

                tienda = "⭐ Impacto"
                color = "imp_gana"
                enlace_ganador = enlace_imp

            else:

                tienda = "⭐ Empate Técnico"
                color = "iguales"
                enlace_ganador = enlace_mk or enlace_imp

            item_id = self.tabla.insert(
                "",
                "end",
                values=(
                    tienda,
                    texto_producto,
                    texto_precio,
                    "📋 Copiar" if enlace_ganador else "No disponible"
                ),
                tags=(color,)
            )

            self.enlaces_por_item[item_id] = enlace_ganador
# ──────────────────────────────────────────────────────────────

    def abrir_historial(self):

        HistorialApp(self)

# ──────────────────────────────────────────────────────────────

def main():

    app = ComparadorApp()
    app.mainloop()


if __name__ == "__main__":
    main()

