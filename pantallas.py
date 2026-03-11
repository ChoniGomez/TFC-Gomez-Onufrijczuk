import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- PANTALLA 1: INICIO ---
class PantallaInicio(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent)
        tk.Label(self, text="TFC Gomez - Onufrijczuk", font=("Arial", 20, "bold"), pady=50).pack()
        
        tk.Button(self, text="INICIAR", width=20, height=2, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"),
                  command=lambda: controlador.mostrar_pantalla(PantallaCarga)).pack()

# --- PANTALLA 2: CARGA DE DATOS CSV  ---
class PantallaCarga(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent)
        self.controlador = controlador
        self.checks_visuales = {}

        tk.Label(self, text="Carga de Archivos CSV", font=("Arial", 16, "bold"), pady=20).pack()

        opciones = [
            ("Cargar Facilitadores", "facilitadores"),
            ("Cargar Horas a Cumplir", "horas"),
            ("Cargar Trayectos", "trayectos"),
            ("Cargar Facilitadores - Trayectos", "fac_trayectos"),
            ("Cargar Disponibilidad Horaria", "disponibilidad")
        ]

        # Contenedor central para alinear los botones
        frame_central = tk.Frame(self)
        frame_central.pack()

        for texto, clave in opciones:
            frame_fila = tk.Frame(frame_central)
            frame_fila.pack(pady=8, fill="x")

            btn = tk.Button(frame_fila, text=texto, width=35, anchor="w",
                            command=lambda c=clave: self.seleccionar_archivo(c))
            btn.pack(side="left")

            estado_inicial = "✅" if self.controlador.datos[clave] is not None else "❌"
            color_inicial = "green" if self.controlador.datos[clave] is not None else "red"
            
            lbl_check = tk.Label(frame_fila, text=estado_inicial, fg=color_inicial, font=("Arial", 12, "bold"), padx=10)
            lbl_check.pack(side="left")
            
            self.checks_visuales[clave] = lbl_check

        # Botón Siguiente direcciona a Pantalla del Algoritmo 
        btn_siguiente = tk.Button(self, text="Siguiente →", width=15, bg="#2196F3", fg="white",
                                  command=self.ir_a_algoritmo)
        btn_siguiente.pack(side="bottom", pady=30)

    def seleccionar_archivo(self, clave):
        ruta = filedialog.askopenfilename(filetypes=[("Archivos CSV", "*.csv")])
        if ruta:
            try:
                self.controlador.datos[clave] = pd.read_csv(ruta)
                self.checks_visuales[clave].config(text="✅", fg="green")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cargar el archivo: {e}")

    def ir_a_algoritmo(self):
        cargados = [v for v in self.controlador.datos.values() if v is not None]
        if not cargados:
            messagebox.showwarning("Atención", "Carga al menos un archivo para continuar.")
        else:
            # Pasa a la pantalla de algoritmo
            self.controlador.mostrar_pantalla(PantallaAlgoritmo)


# --- PANTALLA 3: ALGORITMO ---
class PantallaAlgoritmo(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent)
        self.controlador = controlador
        
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.crear_panel_izquierdo()
        self.crear_panel_derecho()

    def crear_panel_izquierdo(self):
        frame_izq = tk.Frame(self, padx=10, pady=10)
        frame_izq.grid(row=0, column=0, sticky="nsew")

        lf_grafico = ttk.LabelFrame(frame_izq, text="Gráfico ")
        lf_grafico.pack(fill="both", expand=True, pady=10)

        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)
        
        generaciones = np.arange(0, 150)
        promedio = np.log(generaciones + 1) * 6 + np.random.rand(150) * 2
        maximo = promedio + np.random.rand(150) * 4 + 2
        
        ax.fill_between(generaciones, maximo, color='red', label='Máximo')
        ax.fill_between(generaciones, promedio, color='lime', label='Promedio')
        
        ax.set_title('Evolución de la Población', fontsize=10, fontweight='bold')
        ax.set_xlabel('Generaciones', fontweight='bold')
        ax.set_ylabel('Función de Aptitud', fontweight='bold')
        ax.set_xlim(0, 150)
        ax.set_ylim(0, max(maximo) + 5)
        ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.25), ncol=2)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=lf_grafico)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)

    def crear_panel_derecho(self):
        frame_der = tk.Frame(self, padx=10, pady=10)
        frame_der.grid(row=0, column=1, sticky="nsew")

        lf_algoritmo = ttk.LabelFrame(frame_der, text="Datos del Algoritmo")
        # Le quitamos el expand=True para que deje espacio al panel de abajo
        lf_algoritmo.pack(fill="both", pady=(0, 10))

        # --- Condición de Fin y Optimización Colonia de Hormiga ---
        frame_top_der = tk.Frame(lf_algoritmo)
        frame_top_der.pack(fill="x", pady=5, padx=5)

        # 1. Condición de Fin (Mitad Izquierda)
        lf_fin = ttk.LabelFrame(frame_top_der, text="Condición de Fin")
        lf_fin.pack(side="left", fill="both", expand=True, padx=5)
        
        lf_fin.columnconfigure(0, weight=1)
        lf_fin.columnconfigure(1, weight=1)

        tk.Label(lf_fin, text="Número de Generaciones :").grid(row=0, column=0, sticky="e", padx=2, pady=5)
        ttk.Entry(lf_fin, width=10).grid(row=0, column=1, sticky="w", padx=2, pady=5)
        
        tk.Label(lf_fin, text="Soluciones Deseadas :").grid(row=1, column=0, sticky="e", padx=2, pady=5)
        ttk.Entry(lf_fin, width=10).grid(row=1, column=1, sticky="w", padx=2, pady=5)
        
        tk.Label(lf_fin, text="Minutos de Ejecución :").grid(row=2, column=0, sticky="e", padx=2, pady=5)
        ttk.Entry(lf_fin, width=10).grid(row=2, column=1, sticky="w", padx=2, pady=5)

        # 2. Optimización Colonia de Hormiga (Mitad Derecha)
        lf_och = ttk.LabelFrame(frame_top_der, text="Optimización Colonia de Hormiga")
        lf_och.pack(side="right", fill="both", expand=True, padx=5)

        lf_och.columnconfigure(0, weight=1)
        lf_och.columnconfigure(1, weight=1)

        tk.Label(lf_och, text="Número de Hormigas :").grid(row=0, column=0, sticky="e", padx=2, pady=2)
        ttk.Entry(lf_och, width=10).grid(row=0, column=1, sticky="w", padx=2, pady=2)
        
        tk.Label(lf_och, text="Feromona Inicial :").grid(row=1, column=0, sticky="e", padx=2, pady=2)
        ttk.Entry(lf_och, width=10).grid(row=1, column=1, sticky="w", padx=2, pady=2)
        
        tk.Label(lf_och, text="Peso Heurístico :").grid(row=2, column=0, sticky="e", padx=2, pady=2)
        ttk.Entry(lf_och, width=10).grid(row=2, column=1, sticky="w", padx=2, pady=2)

        tk.Label(lf_och, text="Peso Feromona :").grid(row=3, column=0, sticky="e", padx=2, pady=2)
        ttk.Entry(lf_och, width=10).grid(row=3, column=1, sticky="w", padx=2, pady=2)

        # --- Técnicas de Selección ---
        lf_seleccion = ttk.LabelFrame(lf_algoritmo, text="Técnicas de Selección", labelanchor="n")
        lf_seleccion.pack(fill="x", padx=10, pady=5)
        
        frame_torneo = tk.Frame(lf_seleccion, bd=1, relief="ridge")
        frame_torneo.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        tk.Label(frame_torneo, text="Torneo").grid(row=0, column=0, columnspan=2, pady=(2,5))
        tk.Label(frame_torneo, text="% Selección Torneo :").grid(row=1, column=0, sticky="e", padx=5)
        ent_torneo = ttk.Entry(frame_torneo, width=12)
        ent_torneo.insert(0, "0.05")
        ent_torneo.grid(row=1, column=1, sticky="w", padx=5)

        tk.Label(frame_torneo, text="Presión Selectiva :").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        ent_presion = ttk.Entry(frame_torneo, width=12)
        ent_presion.insert(0, "20")
        ent_presion.grid(row=2, column=1, sticky="w", padx=5)

        frame_ruleta = tk.Frame(lf_seleccion, bd=1, relief="ridge")
        frame_ruleta.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        tk.Label(frame_ruleta, text="Ruleta").grid(row=0, column=0, columnspan=2)
        tk.Label(frame_ruleta, text="% Selección Ruleta :").grid(row=1, column=0, sticky="e", padx=5)
        ent_ruleta = ttk.Entry(frame_ruleta, width=12)
        ent_ruleta.insert(0, "0.94")
        ent_ruleta.grid(row=1, column=1, sticky="w", padx=5)

        tk.Label(frame_ruleta, text="Elitsta").grid(row=2, column=0, columnspan=2)
        tk.Label(frame_ruleta, text="% Selección Elitista :").grid(row=3, column=0, sticky="e", padx=5)
        ent_elitista = ttk.Entry(frame_ruleta, width=12)
        ent_elitista.insert(0, "0.01")
        ent_elitista.grid(row=3, column=1, sticky="w", padx=5, pady=(0,5))

        # --- Operadores de Cruza y Mutación ---
        frame_operadores = tk.Frame(lf_algoritmo)
        frame_operadores.pack(fill="x", padx=5, pady=5)

        # Operador de Cruza
        lf_cruza = ttk.LabelFrame(frame_operadores, text="Operador de Cruza", labelanchor="n")
        lf_cruza.pack(side="left", fill="both", expand=True, padx=5)
        
        frame_cruza_in = tk.Frame(lf_cruza)
        frame_cruza_in.pack(expand=True)
        tk.Label(frame_cruza_in, text="Puntos Cruza :").grid(row=0, column=0, sticky="e")
        ent_cruza = ttk.Entry(frame_cruza_in, width=12)
        ent_cruza.insert(0, "20")
        ent_cruza.grid(row=0, column=1, sticky="w", padx=5)

        # Operador de Mutacion 
        lf_mutacion = ttk.LabelFrame(frame_operadores, text="Operador de Mutación", labelanchor="n")
        lf_mutacion.pack(side="right", fill="both", expand=True, padx=5)
        
        tk.Label(lf_mutacion, text="Probabilidad :").grid(row=0, column=0, sticky="e", padx=2, pady=(10, 2))
        ent_prob = ttk.Entry(lf_mutacion, width=12)
        ent_prob.insert(0, "0.02")
        ent_prob.grid(row=0, column=1, sticky="w", padx=2, pady=(10, 2))

        tk.Label(lf_mutacion, text="Probabilidad Facilitador 1:").grid(row=1, column=0, sticky="e", padx=2, pady=(2, 10))
        ent_pf1 = ttk.Entry(lf_mutacion, width=12)
        ent_pf1.insert(0, "0.25")
        ent_pf1.grid(row=1, column=1, sticky="w", padx=2, pady=(2, 10))

        tk.Label(lf_mutacion, text="Probabilidad Facilitador 2:").grid(row=2, column=0, sticky="e", padx=2, pady=(2, 10))
        ent_pf2 = ttk.Entry(lf_mutacion, width=12)
        ent_pf2.insert(0, "0.25")
        ent_pf2.grid(row=2, column=1, sticky="w", padx=2, pady=(2, 10))

        tk.Label(lf_mutacion, text="Probabilidad Facilitador Complementario:").grid(row=3, column=0, sticky="e", padx=2, pady=(2, 10))
        ent_pfc = ttk.Entry(lf_mutacion, width=12)
        ent_pfc.insert(0, "0.25")
        ent_pfc.grid(row=3, column=1, sticky="w", padx=2, pady=(2, 10))

        tk.Label(lf_mutacion, text="Probabilidad Profesor Ed. Especial:").grid(row=4, column=0, sticky="e", padx=2, pady=(2, 10))
        ent_pfc = ttk.Entry(lf_mutacion, width=12)
        ent_pfc.insert(0, "0.25")
        ent_pfc.grid(row=4, column=1, sticky="w", padx=2, pady=(2, 10))
        

        # =========================================================
        # NUEVO FRAME: DATOS DE LA EJECUCIÓN
        # =========================================================
        lf_ejecucion = tk.LabelFrame(frame_der, text=" Datos de la Ejecución ", font=("Arial", 11, "bold"), fg="#333333")
        lf_ejecucion.pack(fill="both", expand=True, pady=(0, 10), padx=5)

        # Creamos un marco interno invisible para centrar la lista perfectamente
        frame_datos = tk.Frame(lf_ejecucion)
        frame_datos.pack(expand=True)

        # Tiempo
        self.lbl_tiempo = tk.Label(frame_datos, text="Tiempo de ejecución: --", font=("Arial", 15, "bold"), fg="#000000")
        self.lbl_tiempo.pack(anchor="w", pady=5)

        # Generación
        self.lbl_generacion = tk.Label(frame_datos, text="Número de generación: --", font=("Arial", 15, "bold"), fg="#000000")
        self.lbl_generacion.pack(anchor="w", pady=5)

        # Aptitud
        self.lbl_aptitud = tk.Label(frame_datos, text="Función de aptitud: --", font=("Arial", 15, "bold"), fg="#000000")
        self.lbl_aptitud.pack(anchor="w", pady=5)


        # --- BOTONES DE ACCIÓN ---
        frame_botones = tk.Frame(frame_der)
        frame_botones.pack(side="bottom", fill="x", pady=5)

        btn_ejecutar = tk.Button(frame_botones, text="Ejecutar Algoritmo", bg="#4CAF50", fg="white", font=("Arial", 10, "bold"),
                                 command=lambda: print("Próximamente: Ejecutar algoritmo..."))
        btn_ejecutar.pack(side="left", expand=True, fill="x", padx=5, ipady=5)

        btn_exportar = tk.Button(frame_botones, text="Exportar Horarios", bg="#2196F3", fg="white", font=("Arial", 10, "bold"),
                                 command=lambda: print("Próximamente: Exportando..."))
        btn_exportar.pack(side="left", expand=True, fill="x", padx=5, ipady=5)

        btn_cancelar = tk.Button(frame_botones, text="Cancelar", bg="#f44336", fg="white", font=("Arial", 10, "bold"),
                                 command=self.volver_a_carga)
        btn_cancelar.pack(side="left", expand=True, fill="x", padx=5, ipady=5)

    def volver_a_carga(self):
        # Regresar a la pantalla de carga
        self.controlador.mostrar_pantalla(PantallaCarga)