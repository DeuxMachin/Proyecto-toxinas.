import os


current_dir = os.path.dirname(os.path.abspath(__file__))


caracteres = {'ω': 'w', 'μ': 'u', 'β': 'b', '-': '', '_':''}

# Función para renombrar archivos
def renombrar_archivos(ruta):
    for archivo in os.listdir(ruta):
        nuevo_nombre = archivo
        for especial, reemplazo in caracteres.items():
            nuevo_nombre = nuevo_nombre.replace(especial, reemplazo)
        
        
        if nuevo_nombre != archivo:
            os.rename(
                os.path.join(ruta, archivo),
                os.path.join(ruta, nuevo_nombre)
            )
            print(f'Renombrado: {archivo} --> {nuevo_nombre}')


renombrar_archivos(current_dir)
