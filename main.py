import tkinter as tk
from pantallas import PantallaInicio

class AppPrincipal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TFC Gomez - Onufrijczuk")
        # Hacemos la ventana principal más grande para que quepa el gráfico y los controles
        self.geometry("1100x650") 

        self.datos = {
            "facilitadores": None,
            "horas": None,
            "trayectos": None,
            "fac_trayectos": None,
            "disponibilidad": None
        }

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