import pandas as pd

def exportar_a_excel(datos):
    df = pd.DataFrame(datos, columns=["Tienda", "Producto", "Precio"])
    df.to_excel("productos.xlsx", index=False)
    print("Excel creado correctamente")