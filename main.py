import tkinter as tk
from pantallas import PantallaInicio
from gestor_datos import GestorDatos 

class AppPrincipal(tk.Tk):
    """
    Clase principal de la aplicación que administra la ventana base, 
    el contexto global de datos y el enrutamiento entre las pantallas.
    """
    def __init__(self):
        super().__init__()
        self.title("TFC Gomez - Onufrijczuk")
        
        # ---------------------------------------------------------
        # Configuración de dimensiones y centrado de ventana
        # ---------------------------------------------------------
        anchoVentana = 1100
        altoVentana = 790

        # Obtención de la resolución total de la pantalla del usuario
        anchoPantalla = self.winfo_screenwidth()
        altoPantalla = self.winfo_screenheight()

        # Cálculo de las coordenadas X e Y para el centrado
        posicionX = int((anchoPantalla / 2) - (anchoVentana / 2))
        
        # Se aplica un offset de -40 píxeles en el eje Y para compensar 
        # visualmente el espacio de la barra de tareas del sistema operativo.
        posicionY = int((altoPantalla / 2) - (altoVentana / 2)) - 40

        # Asignación de la geometría en formato "anchoxalto+X+Y"
        self.geometry(f"{anchoVentana}x{altoVentana}+{posicionX}+{posicionY}")
        # ---------------------------------------------------------

        # Instanciación del gestor de datos que mantendrá el estado global de la aplicación.
        self.gestor = GestorDatos() 

        # Contenedor principal donde se renderizarán las vistas dinámicas.
        self.contenedor = tk.Frame(self)
        self.contenedor.pack(side="top", fill="both", expand=True)

        self.mostrarPantalla(PantallaInicio)

    def mostrarPantalla(self, clasePantalla):
        """
        Destruye los widgets de la vista actual en el contenedor 
        e inicializa y renderiza la nueva vista solicitada.
        """
        for widget in self.contenedor.winfo_children():
            widget.destroy()
        
        nuevaPantalla = clasePantalla(parent=self.contenedor, controlador=self)
        nuevaPantalla.pack(fill="both", expand=True)


if __name__ == "__main__":
    app = AppPrincipal()
    app.mainloop()