import tkinter as tk
from tkinter import ttk, messagebox
from db.conexion import conectar

import pandas as pd
import os


class HistorialApp(tk.Toplevel):

    def __init__(self, parent):
        super().__init__(parent)

        self.title("Historial de Productos Guardados")
        self.geometry("700x400")

        self.config(bg="#1a1a2e")

        self.crear_interfaz()
        self.cargar_historial()


    def crear_interfaz(self):

        titulo = tk.Label(
            self,
            text="📂 Historial de Productos Guardados",
            font=("Segoe UI", 18, "bold"),
            bg="#1a1a2e",
            fg="white"
        )

        titulo.pack(pady=15)


        columnas = (
            "codigo",
            "nombre",
            "fecha"
        )


        self.tabla = ttk.Treeview(
            self,
            columns=columnas,
            show="headings"
        )


        self.tabla.heading(
            "codigo",
            text="Código"
        )

        self.tabla.heading(
            "nombre",
            text="Nombre de la tabla"
        )

        self.tabla.heading(
            "fecha",
            text="Fecha"
        )


        self.tabla.column(
            "codigo",
            width=150,
            anchor="center"
        )


        self.tabla.column(
            "nombre",
            width=250
        )


        self.tabla.column(
            "fecha",
            width=200,
            anchor="center"
        )

        # PANEL DE BOTONES

        frame_botones = tk.Frame(
            self,
            bg="#1a1a2e"
        )

        frame_botones.pack(
            pady=10
        )


        btn_actualizar = tk.Button(
            frame_botones,
            text="🔄 Actualizar",
            bg="#2563eb",
            fg="white",
            font=("Segoe UI",11,"bold"),
            command=self.cargar_historial
        )

        btn_actualizar.pack(
            side="left",
            padx=10
        )


        btn_excel = tk.Button(
            frame_botones,
            text="📊 Exportar Excel",
            bg="#10b981",
            fg="white",
            font=("Segoe UI",11,"bold"),
            command=self.exportar_excel
        )

        btn_excel.pack(
            side="left",
            padx=10
        )

        btn_ver = tk.Button(
            frame_botones,
            text="🔎 Ver productos",
            bg="#9333ea",
            fg="white",
            font=("Segoe UI",11,"bold"),
            command=self.ver_productos
        )

        btn_ver.pack(
            side="left",
            padx=10
        )

        self.tabla.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )


    def exportar_excel(self):

        seleccion = self.tabla.selection()

        if not seleccion:
            messagebox.showwarning(
                "Aviso",
                "Seleccione un historial para exportar"
            )
            return

        datos_historial = self.tabla.item(
            seleccion[0]
        )["values"]

        codigo = datos_historial[0]
        nombre = datos_historial[1]

        try:
            conn = conectar()
            cursor = conn.cursor()

            sql = """
            SELECT
                tienda,
                producto,
                precio,
                precio_comparacion,
                enlace
            FROM productos
            WHERE codigo = %s
            """

            cursor.execute(
                sql,
                (codigo,)
            )

            productos = cursor.fetchall()

            cursor.close()
            conn.close()

            productos_excel = []

            for producto in productos:

                tienda = producto[0]
                nombre_producto = producto[1]
                precio = producto[2]
                comparacion = producto[3]
                enlace = producto[4] or ""

                if precio is not None:
                    mostrar_precio = f"S/ {float(precio):.2f}"

                elif comparacion is not None:
                    mostrar_precio = comparacion

                else:
                    mostrar_precio = "Sin precio"

                productos_excel.append(
                    (
                        tienda,
                        nombre_producto,
                        mostrar_precio,
                        enlace
                    )
                )

            df = pd.DataFrame(
                productos_excel,
                columns=[
                    "Tienda",
                    "Producto",
                    "Precio",
                    "Enlace"
                ]
            )

            carpeta = "data"

            os.makedirs(
                carpeta,
                exist_ok=True
            )

            # Evita caracteres no permitidos en nombres de archivos
            nombre_seguro = "".join(
                caracter
                for caracter in str(nombre)
                if caracter not in r'\/:*?"<>|'
            )

            ruta = os.path.join(
                carpeta,
                nombre_seguro + ".xlsx"
            )

            try:
                df.to_excel(
                    ruta,
                    index=False
                )

                messagebox.showinfo(
                    "OK",
                    f"Excel guardado en:\n{ruta}"
                )

            except PermissionError:
                messagebox.showwarning(
                    "Archivo abierto",
                    "El archivo Excel está abierto.\n\n"
                    "Cierre el archivo y vuelva a intentar exportar."
                )

        except Exception as e:
            messagebox.showerror(
                "Error",
                str(e)
            )

            carpeta = "data"

    def cargar_historial(self):

        conn = None
        cursor = None

        try:
            conn = conectar()
            cursor = conn.cursor()

            sql = """
            SELECT codigo, nombre, fecha
            FROM historial
            ORDER BY fecha DESC
            """

            cursor.execute(sql)

            datos = cursor.fetchall()

            self.tabla.delete(
                *self.tabla.get_children()
            )

            for fila in datos:
                self.tabla.insert(
                    "",
                    "end",
                    values=fila
                )

        except Exception as e:
            messagebox.showerror(
                "Error",
                str(e)
            )

        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()

    def ver_productos(self):

        seleccionado = self.tabla.selection()

        if not seleccionado:
            messagebox.showwarning(
                "Aviso",
                "Seleccione un historial"
            )
            return

        datos = self.tabla.item(
            seleccionado[0]
        )["values"]

        codigo = datos[0]

        ventana = tk.Toplevel(self)

        ventana.title(
            f"Productos guardados {codigo}"
        )

        ventana.geometry("1200x450")
        ventana.config(bg="#1a1a2e")

        frame_tabla = tk.Frame(
            ventana,
            bg="#1a1a2e"
        )

        frame_tabla.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=15
        )

        tabla = ttk.Treeview(
            frame_tabla,
            columns=(
                "tienda",
                "producto",
                "precio",
                "enlace"
            ),
            show="headings"
        )

        tabla.heading(
            "tienda",
            text="Tienda"
        )

        tabla.heading(
            "producto",
            text="Producto"
        )

        tabla.heading(
            "precio",
            text="Precio"
        )

        tabla.heading(
            "enlace",
            text="Enlace"
        )

        tabla.column(
            "tienda",
            width=140,
            anchor="center"
        )

        tabla.column(
            "producto",
            width=700
        )

        tabla.column(
            "precio",
            width=220,
            anchor="center"
        )

        tabla.column(
            "enlace",
            width=120,
            anchor="center"
        )

        scrollbar = ttk.Scrollbar(
            frame_tabla,
            orient="vertical",
            command=tabla.yview
        )

        tabla.configure(
            yscrollcommand=scrollbar.set
        )

        tabla.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        enlaces_por_item = {}

        try:
            conn = conectar()
            cursor = conn.cursor()

            sql = """
            SELECT
                tienda,
                producto,
                precio,
                precio_comparacion,
                enlace
            FROM productos
            WHERE codigo = %s
            """

            cursor.execute(
                sql,
                (codigo,)
            )

            productos = cursor.fetchall()

            for producto in productos:

                tienda = producto[0]
                nombre_producto = producto[1]
                precio = producto[2]
                comparacion = producto[3]
                enlace = producto[4] or ""

                if precio is not None:
                    mostrar_precio = f"S/ {float(precio):.2f}"

                elif comparacion is not None:
                    mostrar_precio = comparacion

                else:
                    mostrar_precio = "Sin precio"

                item_id = tabla.insert(
                    "",
                    "end",
                    values=(
                        tienda,
                        nombre_producto,
                        mostrar_precio,
                        "📋 Copiar" if enlace else "No disponible"
                    )
                )

                enlaces_por_item[item_id] = enlace

            cursor.close()
            conn.close()

        except Exception as e:
            messagebox.showerror(
                "Error",
                str(e)
            )
            return

        def restaurar_enlace(item_id):

            if not tabla.exists(item_id):
                return

            valores = list(
                tabla.item(item_id, "values")
            )

            enlace = enlaces_por_item.get(
                item_id,
                ""
            )

            valores[3] = (
                "📋 Copiar"
                if enlace
                else "No disponible"
            )

            tabla.item(
                item_id,
                values=valores
            )

        def copiar_enlace(event):

            region = tabla.identify_region(
                event.x,
                event.y
            )

            if region != "cell":
                return

            columna = tabla.identify_column(
                event.x
            )

            if columna != "#4":
                return

            item_id = tabla.identify_row(
                event.y
            )

            if not item_id:
                return

            enlace = enlaces_por_item.get(
                item_id,
                ""
            )

            if not enlace:
                messagebox.showwarning(
                    "Enlace no disponible",
                    "Este producto no tiene enlace guardado."
                )
                return

            ventana.clipboard_clear()
            ventana.clipboard_append(enlace)
            ventana.update()

            valores = list(
                tabla.item(item_id, "values")
            )

            valores[3] = "✅ Copiado"

            tabla.item(
                item_id,
                values=valores
            )

            ventana.after(
                2000,
                lambda: restaurar_enlace(item_id)
            )

        tabla.bind(
            "<ButtonRelease-1>",
            copiar_enlace
        )
        
        conn.close()