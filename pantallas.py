import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class PantallaInicio(tk.Frame):
    """
    Vista inicial de la aplicación.
    Provee el punto de entrada principal al sistema de asignación.
    """
    def __init__(self, parent, controlador):
        super().__init__(parent)
        tk.Label(self, text="TFC Gomez - Onufrijczuk", font=("Arial", 20, "bold"), pady=50).pack()
        
        tk.Button(self, text="INICIAR", width=20, height=2, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"),
                  command=lambda: controlador.mostrarPantalla(PantallaCarga)).pack()


class PantallaCarga(tk.Frame):
    """
    Vista de gestión de datos.
    Permite la selección y carga en memoria de los archivos CSV requeridos.
    """
    def __init__(self, parent, controlador):
        super().__init__(parent)
        self.controlador = controlador
        self.checksVisuales = {}

        tk.Label(self, text="Carga de Archivos CSV", font=("Arial", 16, "bold"), pady=20).pack()

        # Definición de los módulos de datos requeridos para la ejecución
        opciones = [
            ("Cargar Facilitadores", "facilitadores"),
            ("Cargar Trayectos", "trayectos"),
            ("Cargar Facilitadores - Trayectos", "fac_trayectos"),
            ("Cargar Disponibilidad Horaria", "disponibilidad"),
            ("Cargar horarios de clases", "horarios_clases")
        ]

        # Contenedor central para la alineación de los elementos de carga
        frameCentral = tk.Frame(self)
        frameCentral.pack()

        for texto, clave in opciones:
            frameFila = tk.Frame(frameCentral)
            frameFila.pack(pady=10, fill="x")

            btn = tk.Button(frameFila, text=texto, width=40, anchor="w",
                            font=("Arial", 11), cursor="hand2",
                            command=lambda c=clave: self.seleccionarArchivo(c))
            btn.pack(side="left", ipady=5)

            # Verificación del estado de carga en el gestor de datos global
            cargado = self.controlador.gestor.tieneDatos(clave)
            
            estadoInicial = "✅" if cargado else "❌"
            colorInicial = "green" if cargado else "red"
            
            lblCheck = tk.Label(frameFila, text=estadoInicial, fg=colorInicial, font=("Arial", 14, "bold"), padx=15)
            lblCheck.pack(side="left")
            
            self.checksVisuales[clave] = lblCheck

        # Botón de navegación hacia la vista de configuración del algoritmo
        btnSiguiente = tk.Button(self, text="Siguiente →", width=15, bg="#2196F3", fg="white",
                                 font=("Arial", 12, "bold"), cursor="hand2",
                                 command=self.irAAlgoritmo)
        btnSiguiente.pack(side="bottom", pady=40, ipady=5)

    def seleccionarArchivo(self, clave):
        """
        Abre un cuadro de diálogo para la selección del archivo y delega 
        la persistencia en memoria al gestor de datos.
        """
        ruta = filedialog.askopenfilename(filetypes=[("Archivos CSV", "*.csv")])
        if ruta:
            exito, mensaje = self.controlador.gestor.cargarCsv(clave, ruta)
            if exito:
                self.checksVisuales[clave].config(text="✅", fg="green")
            else:
                messagebox.showerror("Error", mensaje)

    def irAAlgoritmo(self):
        """
        Validación de requisitos previos antes de inicializar la vista del algoritmo.
        """
        if not self.controlador.gestor.estanDatosListos():
            messagebox.showwarning("Atención", "Es necesario cargar todos los archivos CSV para continuar.")
        else:
            self.controlador.mostrarPantalla(PantallaAlgoritmo)


class PantallaAlgoritmo(tk.Frame):
    """
    Vista principal de ejecución y monitoreo del Algoritmo de Optimización.
    """
    def __init__(self, parent, controlador):
        super().__init__(parent)
        self.controlador = controlador
        
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.crearPanelIzquierdo()
        self.crearPanelDerecho()

    def crearPanelIzquierdo(self):
        """
        Inicializa y renderiza el panel de gráficos estadísticos de evolución.
        """
        frameIzq = tk.Frame(self, padx=10, pady=10)
        frameIzq.grid(row=0, column=0, sticky="nsew")

        lfGrafico = ttk.LabelFrame(frameIzq, text="Gráfico de Evolución")
        lfGrafico.pack(fill="both", expand=True, pady=10)

        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)
        
        # Simulación inicial de datos para la vista del gráfico
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

        canvas = FigureCanvasTkAgg(fig, master=lfGrafico)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)

    def crearPanelDerecho(self):
        """
        Inicializa y renderiza el panel de configuración de parámetros del algoritmo 
        y las métricas de ejecución.
        """
        frameDer = tk.Frame(self, padx=10, pady=10)
        frameDer.grid(row=0, column=1, sticky="nsew")

        lfAlgoritmo = ttk.LabelFrame(frameDer, text="Parámetros del Algoritmo")
        lfAlgoritmo.pack(fill="both", pady=(0, 10))

        # Contenedor superior derecho
        frameTopDer = tk.Frame(lfAlgoritmo)
        frameTopDer.pack(fill="x", pady=5, padx=5)

        # Configuración de criterios de finalización
        lfFin = ttk.LabelFrame(frameTopDer, text="Condición de Fin")
        lfFin.pack(side="left", fill="both", expand=True, padx=5)
        
        lfFin.columnconfigure(0, weight=1)
        lfFin.columnconfigure(1, weight=1)
        
        # Asignación de peso dinámico a las filas para distribución vertical equitativa
        lfFin.rowconfigure(0, weight=1)
        lfFin.rowconfigure(1, weight=1)
        lfFin.rowconfigure(2, weight=1)

        tk.Label(lfFin, text="Número de Generaciones :").grid(row=0, column=0, sticky="e", padx=2, pady=15)
        ttk.Entry(lfFin, width=10).grid(row=0, column=1, sticky="w", padx=2, pady=15)
        
        tk.Label(lfFin, text="Soluciones Deseadas :").grid(row=1, column=0, sticky="e", padx=2, pady=15)
        ttk.Entry(lfFin, width=10).grid(row=1, column=1, sticky="w", padx=2, pady=15)
        
        tk.Label(lfFin, text="Minutos de Ejecución :").grid(row=2, column=0, sticky="e", padx=2, pady=15)
        ttk.Entry(lfFin, width=10).grid(row=2, column=1, sticky="w", padx=2, pady=15)

        # Parámetros del Algoritmo de Colonia de Hormigas (OCH)
        lfOch = ttk.LabelFrame(frameTopDer, text="Optimización Colonia de Hormigas")
        lfOch.pack(side="right", fill="both", expand=True, padx=5)

        lfOch.columnconfigure(0, weight=1)
        lfOch.columnconfigure(1, weight=1)

        tk.Label(lfOch, text="Número de Hormigas :").grid(row=0, column=0, sticky="e", padx=2, pady=2)
        ttk.Entry(lfOch, width=10).grid(row=0, column=1, sticky="w", padx=2, pady=2)

        tk.Label(lfOch, text="Grupo de Hormigas :").grid(row=1, column=0, sticky="e", padx=2, pady=2)
        ttk.Entry(lfOch, width=10).grid(row=1, column=1, sticky="w", padx=2, pady=2)
        
        tk.Label(lfOch, text="Feromona Inicial :").grid(row=2, column=0, sticky="e", padx=2, pady=2)
        ttk.Entry(lfOch, width=10).grid(row=2, column=1, sticky="w", padx=2, pady=2)
        
        tk.Label(lfOch, text="Tasa Evaporación Feromona :").grid(row=3, column=0, sticky="e", padx=2, pady=2)
        ttk.Entry(lfOch, width=10).grid(row=3, column=1, sticky="w", padx=2, pady=2)

        tk.Label(lfOch, text="Peso Heurístico :").grid(row=4, column=0, sticky="e", padx=2, pady=2)
        ttk.Entry(lfOch, width=10).grid(row=4, column=1, sticky="w", padx=2, pady=2)

        tk.Label(lfOch, text="Peso Feromona :").grid(row=5, column=0, sticky="e", padx=2, pady=2)
        ttk.Entry(lfOch, width=10).grid(row=5, column=1, sticky="w", padx=2, pady=2)

        # Configuración de Técnicas de Selección
        lfSeleccion = ttk.LabelFrame(lfAlgoritmo, text="Técnicas de Selección", labelanchor="n")
        lfSeleccion.pack(fill="x", padx=10, pady=5)
        
        frameTorneo = tk.Frame(lfSeleccion, bd=1, relief="ridge")
        frameTorneo.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        tk.Label(frameTorneo, text="Torneo").grid(row=0, column=0, columnspan=2, pady=(2,5))
        tk.Label(frameTorneo, text="% Selección Torneo :").grid(row=1, column=0, sticky="e", padx=5)
        entTorneo = ttk.Entry(frameTorneo, width=12)
        entTorneo.insert(0, "0.05")
        entTorneo.grid(row=1, column=1, sticky="w", padx=5)

        tk.Label(frameTorneo, text="Presión Selectiva :").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        entPresion = ttk.Entry(frameTorneo, width=12)
        entPresion.insert(0, "20")
        entPresion.grid(row=2, column=1, sticky="w", padx=5)

        frameRuleta = tk.Frame(lfSeleccion, bd=1, relief="ridge")
        frameRuleta.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        tk.Label(frameRuleta, text="Ruleta").grid(row=0, column=0, columnspan=2)
        tk.Label(frameRuleta, text="% Selección Ruleta :").grid(row=1, column=0, sticky="e", padx=5)
        entRuleta = ttk.Entry(frameRuleta, width=12)
        entRuleta.insert(0, "0.94")
        entRuleta.grid(row=1, column=1, sticky="w", padx=5)

        tk.Label(frameRuleta, text="Elitista").grid(row=2, column=0, columnspan=2)
        tk.Label(frameRuleta, text="% Selección Elitista :").grid(row=3, column=0, sticky="e", padx=5)
        entElitista = ttk.Entry(frameRuleta, width=12)
        entElitista.insert(0, "0.01")
        entElitista.grid(row=3, column=1, sticky="w", padx=5, pady=(0,5))

        # Configuración de Operadores de Cruza y Mutación
        frameOperadores = tk.Frame(lfAlgoritmo)
        frameOperadores.pack(fill="x", padx=5, pady=5)

        lfCruza = ttk.LabelFrame(frameOperadores, text="Operador de Cruza", labelanchor="n")
        lfCruza.pack(side="left", fill="both", expand=True, padx=5)
        
        frameCruzaIn = tk.Frame(lfCruza)
        frameCruzaIn.pack(expand=True)
        tk.Label(frameCruzaIn, text="Puntos Cruza :").grid(row=0, column=0, sticky="e")
        entCruza = ttk.Entry(frameCruzaIn, width=12)
        entCruza.insert(0, "20")
        entCruza.grid(row=0, column=1, sticky="w", padx=5)

        lfMutacion = ttk.LabelFrame(frameOperadores, text="Operador de Mutación", labelanchor="n")
        lfMutacion.pack(side="right", fill="both", expand=True, padx=5)
        
        tk.Label(lfMutacion, text="Probabilidad General :").grid(row=0, column=0, sticky="e", padx=2, pady=(10, 2))
        entProb = ttk.Entry(lfMutacion, width=12)
        entProb.insert(0, "0.02")
        entProb.grid(row=0, column=1, sticky="w", padx=2, pady=(10, 2))

        tk.Label(lfMutacion, text="Probabilidad Facilitador 1 :").grid(row=1, column=0, sticky="e", padx=2, pady=(2, 10))
        entPf1 = ttk.Entry(lfMutacion, width=12)
        entPf1.insert(0, "0.25")
        entPf1.grid(row=1, column=1, sticky="w", padx=2, pady=(2, 10))

        tk.Label(lfMutacion, text="Probabilidad Facilitador 2 :").grid(row=2, column=0, sticky="e", padx=2, pady=(2, 10))
        entPf2 = ttk.Entry(lfMutacion, width=12)
        entPf2.insert(0, "0.25")
        entPf2.grid(row=2, column=1, sticky="w", padx=2, pady=(2, 10))

        tk.Label(lfMutacion, text="Probabilidad Fac. Complementario :").grid(row=3, column=0, sticky="e", padx=2, pady=(2, 10))
        entPfc = ttk.Entry(lfMutacion, width=12)
        entPfc.insert(0, "0.25")
        entPfc.grid(row=3, column=1, sticky="w", padx=2, pady=(2, 10))

        tk.Label(lfMutacion, text="Probabilidad Prof. Ed. Especial :").grid(row=4, column=0, sticky="e", padx=2, pady=(2, 10))
        entPfe = ttk.Entry(lfMutacion, width=12)
        entPfe.insert(0, "0.25")
        entPfe.grid(row=4, column=1, sticky="w", padx=2, pady=(2, 10))

        # Panel de visualización de métricas de ejecución
        lfEjecucion = tk.LabelFrame(frameDer, text=" Datos de la Ejecución ", font=("Arial", 11, "bold"), fg="#333333")
        lfEjecucion.pack(fill="both", expand=True, pady=(0, 10), padx=5)

        # Contenedor para el centrado de los indicadores
        frameDatos = tk.Frame(lfEjecucion)
        frameDatos.pack(expand=True)

        self.lblTiempo = tk.Label(frameDatos, text="Tiempo de ejecución: --", font=("Arial", 15, "bold"), fg="#000000")
        self.lblTiempo.pack(anchor="w", pady=5)

        self.lblGeneracion = tk.Label(frameDatos, text="Número de generación: --", font=("Arial", 15, "bold"), fg="#000000")
        self.lblGeneracion.pack(anchor="w", pady=5)

        self.lblAptitud = tk.Label(frameDatos, text="Función de aptitud: --", font=("Arial", 15, "bold"), fg="#000000")
        self.lblAptitud.pack(anchor="w", pady=5)

        # Controles de acción principales
        frameBotones = tk.Frame(frameDer)
        frameBotones.pack(side="bottom", fill="x", pady=5)

        btnEjecutar = tk.Button(frameBotones, text="Ejecutar Algoritmo", bg="#4CAF50", fg="white", font=("Arial", 10, "bold"),
                                command=lambda: print("Sistema: Inicializando ejecución del algoritmo..."))
        btnEjecutar.pack(side="left", expand=True, fill="x", padx=5, ipady=5)

        btnExportar = tk.Button(frameBotones, text="Exportar Horarios", bg="#2196F3", fg="white", font=("Arial", 10, "bold"),
                                command=lambda: print("Sistema: Exportando resultados..."))
        btnExportar.pack(side="left", expand=True, fill="x", padx=5, ipady=5)

        btnCancelar = tk.Button(frameBotones, text="Cancelar", bg="#f44336", fg="white", font=("Arial", 10, "bold"),
                                command=self.volverACarga)
        btnCancelar.pack(side="left", expand=True, fill="x", padx=5, ipady=5)

    def volverACarga(self):
        """
        Finaliza el proceso actual y retorna a la vista de gestión de datos.
        """
        self.controlador.mostrarPantalla(PantallaCarga)