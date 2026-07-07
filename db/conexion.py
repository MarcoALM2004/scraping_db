import mysql.connector

#  NO SE OLVIDEN DE CAMBIAR LA CONTRASEÑA DE SU BASE DE DATOS
def conectar():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="MarcoAntonio",
        database="scramping_Extractor"
    )