import tkinter as tk
from pantallas import PantallaInicio
from gestor_datos import GestorDatos 

class AppPrincipal(tk.Tk):
    """
    Clase principal de la aplicación. Gestiona la ventana y el cambio entre pantallas.
    """
    def __init__(self):
        super().__init__()
        self.title("TFC Gomez - Onufrijczuk")
        
        # --- Centra la ventana en la pantalla ---
        anchoVentana = 1100
        altoVentana = 790

        # Obtiene la resolución de la pantalla.
        anchoPantalla = self.winfo_screenwidth()
        altoPantalla = self.winfo_screenheight()

        # Calcula las coordenadas para centrar la ventana.
        posicionX = int((anchoPantalla / 2) - (anchoVentana / 2))
        
        # Ajuste vertical para la barra de tareas.
        posicionY = int((altoPantalla / 2) - (altoVentana / 2)) - 40

        # Define el tamaño y posición de la ventana.
        self.geometry(f"{anchoVentana}x{altoVentana}+{posicionX}+{posicionY}")

        # Crea el gestor de datos que compartirá la información.
        self.gestor = GestorDatos() 

        # Contenedor para las diferentes pantallas.
        self.contenedor = tk.Frame(self)
        self.contenedor.pack(side="top", fill="both", expand=True)

        self.mostrarPantalla(PantallaInicio)

    def mostrarPantalla(self, clasePantalla):
        """
        Limpia la pantalla actual y muestra la nueva.
        """
        for widget in self.contenedor.winfo_children():
            widget.destroy()
        
        nuevaPantalla = clasePantalla(parent=self.contenedor, controlador=self)
        nuevaPantalla.pack(fill="both", expand=True)


if __name__ == "__main__":
    app = AppPrincipal()
    app.mainloop()