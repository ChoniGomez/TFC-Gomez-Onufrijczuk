import tkinter as tk
from pantallas import PantallaInicio
# IMPORTANTE: Importamos tu nueva clase desde tu archivo gestor_datos.py
from gestor_datos import GestorDatos 

class AppPrincipal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TFC Gomez - Onufrijczuk")
        self.geometry("1100x750") 

        # ¡AQUÍ ESTÁ LA MAGIA! 
        # Instanciamos la clase y la guardamos en self.gestor
        self.gestor = GestorDatos() 

        self.contenedor = tk.Frame(self)
        self.contenedor.pack(side="top", fill="both", expand=True)

        self.mostrar_pantalla(PantallaInicio)

    def mostrar_pantalla(self, clase_pantalla):
        for widget in self.contenedor.winfo_children():
            widget.destroy()
        
        nueva_pantalla = clase_pantalla(parent=self.contenedor, controlador=self)
        nueva_pantalla.pack(fill="both", expand=True)

if __name__ == "__main__":
    app = AppPrincipal()
    app.mainloop()