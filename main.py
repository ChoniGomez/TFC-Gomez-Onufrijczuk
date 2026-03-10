import tkinter as tk
from pantallas import PantallaInicio, PantallaCarga, PantallaResultados

class AppPrincipal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TFC Gomez - Onufrijczuk")
        self.geometry("650x550")

        # Diccionario central para guardar los DataFrames de cada CSV
        self.datos = {
            "facilitadores": None,
            "horas": None,
            "trayectos": None,
            "fac_trayectos": None,
            "disponibilidad": None
        }

        # Contenedor principal
        self.contenedor = tk.Frame(self)
        self.contenedor.pack(side="top", fill="both", expand=True)

        # Iniciar en la pantalla de bienvenida
        self.mostrar_pantalla(PantallaInicio)

    def mostrar_pantalla(self, clase_pantalla):
        """Borra la pantalla actual y carga una nueva."""
        for widget in self.contenedor.winfo_children():
            widget.destroy()
        
        nueva_pantalla = clase_pantalla(parent=self.contenedor, controlador=self)
        nueva_pantalla.pack(fill="both", expand=True)

if __name__ == "__main__":
    app = AppPrincipal()
    app.mainloop()