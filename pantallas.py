import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd

# --- PANTALLA 1: INICIO ---
class PantallaInicio(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent)
        tk.Label(self, text="TFC 2026", font=("Arial", 20, "bold"), pady=50).pack()
        
        tk.Button(self, text="INICIAR", width=20, height=2, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"),
                  command=lambda: controlador.mostrar_pantalla(PantallaCarga)).pack()

# --- PANTALLA 2: CARGA DE DATOS (CON CHECKS) ---
class PantallaCarga(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent)
        self.controlador = controlador
        self.checks_visuales = {} # Diccionario para guardar las etiquetas de ✅/❌

        tk.Label(self, text="Carga de Archivos CSV", font=("Arial", 16, "bold"), pady=20).pack()

        # Configuración de los botones requeridos
        opciones = [
            ("Cargar Facilitadores", "facilitadores"),
            ("Cargar Horas a Cumplir", "horas"),
            ("Cargar Trayectos", "trayectos"),
            ("Cargar Facilitadores - Trayectos", "fac_trayectos"),
            ("Cargar Disponibilidad Horaria", "disponibilidad")
        ]

        # Crear una fila para cada botón con su respectivo check
        for texto, clave in opciones:
            frame_fila = tk.Frame(self)
            frame_fila.pack(pady=8, fill="x", padx=100)

            btn = tk.Button(frame_fila, text=texto, width=35, anchor="w",
                            command=lambda c=clave: self.seleccionar_archivo(c))
            btn.pack(side="left")

            # El check: Iniciamos con una "X" roja o vacío
            estado_inicial = "✅" if self.controlador.datos[clave] is not None else "❌"
            color_inicial = "green" if self.controlador.datos[clave] is not None else "red"
            
            lbl_check = tk.Label(frame_fila, text=estado_inicial, fg=color_inicial, font=("Arial", 12, "bold"), padx=10)
            lbl_check.pack(side="left")
            
            # Guardamos la referencia para actualizarla después
            self.checks_visuales[clave] = lbl_check

        # Botón Siguiente
        btn_siguiente = tk.Button(self, text="Siguiente →", width=15, bg="#2196F3", fg="white",
                                  command=self.ir_a_resultados)
        btn_siguiente.pack(side="bottom", pady=30)

    def seleccionar_archivo(self, clave):
        ruta = filedialog.askopenfilename(filetypes=[("Archivos CSV", "*.csv")])
        if ruta:
            try:
                # Cargar datos
                self.controlador.datos[clave] = pd.read_csv(ruta)
                # Actualizar el check visual
                self.checks_visuales[clave].config(text="✅", fg="green")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cargar el archivo: {e}")

    def ir_a_resultados(self):
        # Validar si se cargó algo antes de seguir
        cargados = [v for v in self.controlador.datos.values() if v is not None]
        if not cargados:
            messagebox.showwarning("Atención", "Carga al menos un archivo para continuar.")
        else:
            self.controlador.mostrar_pantalla(PantallaResultados)

# --- PANTALLA 3: SIGUIENTE ---
class PantallaResultados(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent)
        tk.Label(self, text="Datos Listos para Procesar", font=("Arial", 16, "bold"), pady=20).pack()
        
        # Mostrar resumen de lo cargado
        for clave, df in controlador.datos.items():
            if df is not None:
                tk.Label(self, text=f"• {clave.replace('_', ' ').capitalize()}: {len(df)} filas cargadas").pack()

        tk.Button(self, text="Volver", command=lambda: controlador.mostrar_pantalla(PantallaCarga)).pack(pady=20)