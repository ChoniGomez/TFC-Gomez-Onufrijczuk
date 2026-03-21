import tkinter as tk
import os
from datetime import datetime
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from clases import OCH

from algoritmo import (algoritmoOCH, generarPoblacionInicial, evaluarFuncionAptitud, 
                       algoritmoAG, ejecutarCicloGenetico)

class ConfiguracionAG:
    """Estructura para el encapsulamiento de los parámetros del Algoritmo Genético."""
    def __init__(self):
        pass


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

        lfGrafico = ttk.LabelFrame(frameIzq, text="Evolución de la Población")
        lfGrafico.pack(fill="both", expand=True, pady=10)

        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        
        # Configuración inicial del área de graficación (estado de espera).
        self.ax.set_title('Evolución de la Población', fontsize=10, fontweight='bold')
        self.ax.set_xlabel('Generaciones', fontweight='bold')
        self.ax.set_ylabel('Función de Aptitud', fontweight='bold')
        self.ax.set_xlim(0, 100)
        self.ax.set_ylim(0, 1.0)
        
        self.ax.text(50, 0.5, "En espera de inicialización del proceso...", 
                     ha='center', va='center', fontsize=10, alpha=0.6)
        
        self.fig.tight_layout()

        self.canvas = FigureCanvasTkAgg(self.fig, master=lfGrafico)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)

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

        # =========================================================
        # Configuración de criterios de finalización
        # =========================================================
        lfFin = ttk.LabelFrame(frameTopDer, text="Condición de Fin")
        lfFin.pack(side="left", fill="both", expand=True, padx=5)
        
        lfFin.columnconfigure(0, weight=1)
        lfFin.columnconfigure(1, weight=1)
        
        lfFin.rowconfigure(0, weight=1)
        lfFin.rowconfigure(1, weight=1)
        lfFin.rowconfigure(2, weight=1)

        tk.Label(lfFin, text="Número de Generaciones :").grid(row=0, column=0, sticky="e", padx=2, pady=15)
        self.entGeneraciones = ttk.Entry(lfFin, width=10)
        self.entGeneraciones.grid(row=0, column=1, sticky="w", padx=2, pady=15)
        self.entGeneraciones.insert(0, "500")
        
        tk.Label(lfFin, text="Soluciones Deseadas :").grid(row=1, column=0, sticky="e", padx=2, pady=15)
        self.entSoluciones = ttk.Entry(lfFin, width=10)
        self.entSoluciones.grid(row=1, column=1, sticky="w", padx=2, pady=15)
        self.entSoluciones.insert(0, "1")
        
        tk.Label(lfFin, text="Minutos de Ejecución :").grid(row=2, column=0, sticky="e", padx=2, pady=15)
        self.entMinutos = ttk.Entry(lfFin, width=10)
        self.entMinutos.grid(row=2, column=1, sticky="w", padx=2, pady=15)
        self.entMinutos.insert(0, "5")


        # =========================================================
        # Parámetros del Algoritmo de Colonia de Hormigas (OCH)
        # =========================================================
        lfOch = ttk.LabelFrame(frameTopDer, text="Optimización Colonia de Hormigas")
        lfOch.pack(side="right", fill="both", expand=True, padx=5)

        lfOch.columnconfigure(0, weight=1)
        lfOch.columnconfigure(1, weight=1)

        tk.Label(lfOch, text="Número de Hormigas :").grid(row=0, column=0, sticky="e", padx=2, pady=2)
        self.entNumHormigas = ttk.Entry(lfOch, width=10)
        self.entNumHormigas.grid(row=0, column=1, sticky="w", padx=2, pady=2)
        self.entNumHormigas.insert(0, "30")

        tk.Label(lfOch, text="Grupo de Hormigas :").grid(row=1, column=0, sticky="e", padx=2, pady=2)
        self.entGrupoHormigas = ttk.Entry(lfOch, width=10)
        self.entGrupoHormigas.grid(row=1, column=1, sticky="w", padx=2, pady=2)
        self.entGrupoHormigas.insert(0, "1")

        tk.Label(lfOch, text="Feromona Inicial :").grid(row=2, column=0, sticky="e", padx=2, pady=2)
        self.entFeromonaInicial = ttk.Entry(lfOch, width=10)
        self.entFeromonaInicial.grid(row=2, column=1, sticky="w", padx=2, pady=2)
        self.entFeromonaInicial.insert(0, "0.1")
        
        tk.Label(lfOch, text="Tasa Evaporación Feromona :").grid(row=3, column=0, sticky="e", padx=2, pady=2)
        self.entEvaporacion = ttk.Entry(lfOch, width=10)
        self.entEvaporacion.grid(row=3, column=1, sticky="w", padx=2, pady=2)
        self.entEvaporacion.insert(0, "0.01")

        tk.Label(lfOch, text="Depósito de Feromona :").grid(row=4, column=0, sticky="e", padx=2, pady=2)
        self.entDepositoFero = ttk.Entry(lfOch, width=10)
        self.entDepositoFero.grid(row=4, column=1, sticky="w", padx=2, pady=2)
        self.entDepositoFero.insert(0, "0.2")

        tk.Label(lfOch, text="Peso Heurístico :").grid(row=5, column=0, sticky="e", padx=2, pady=2)
        self.entPesoHeuristico = ttk.Entry(lfOch, width=10)
        self.entPesoHeuristico.grid(row=5, column=1, sticky="w", padx=2, pady=2)
        self.entPesoHeuristico.insert(0, "0.6")

        tk.Label(lfOch, text="Peso Feromona :").grid(row=6, column=0, sticky="e", padx=2, pady=2)
        self.entPesoFeromona = ttk.Entry(lfOch, width=10)
        self.entPesoFeromona.grid(row=6, column=1, sticky="w", padx=2, pady=2)
        self.entPesoFeromona.insert(0, "0.4")

        # =========================================================
        # Configuración de Técnicas de Selección
        # =========================================================
        lfSeleccion = ttk.LabelFrame(lfAlgoritmo, text="Técnicas de Selección", labelanchor="n")
        lfSeleccion.pack(fill="x", padx=10, pady=5)
        
        frameTorneo = tk.Frame(lfSeleccion, bd=1, relief="ridge")
        frameTorneo.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        tk.Label(frameTorneo, text="Torneo").grid(row=0, column=0, columnspan=2, pady=(2,5))
        tk.Label(frameTorneo, text="% Selección Torneo :").grid(row=1, column=0, sticky="e", padx=5)
        self.entTorneo = ttk.Entry(frameTorneo, width=12)
        self.entTorneo.insert(0, "0.05")
        self.entTorneo.grid(row=1, column=1, sticky="w", padx=5)

        tk.Label(frameTorneo, text="Presión Selectiva :").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.entPresion = ttk.Entry(frameTorneo, width=12)
        self.entPresion.insert(0, "20")
        self.entPresion.grid(row=2, column=1, sticky="w", padx=5)

        frameRuleta = tk.Frame(lfSeleccion, bd=1, relief="ridge")
        frameRuleta.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        tk.Label(frameRuleta, text="Ruleta").grid(row=0, column=0, columnspan=2)
        tk.Label(frameRuleta, text="% Selección Ruleta :").grid(row=1, column=0, sticky="e", padx=5)
        self.entRuleta = ttk.Entry(frameRuleta, width=12)
        self.entRuleta.insert(0, "0.94")
        self.entRuleta.grid(row=1, column=1, sticky="w", padx=5)

        tk.Label(frameRuleta, text="Elitista").grid(row=2, column=0, columnspan=2)
        tk.Label(frameRuleta, text="% Selección Elitista :").grid(row=3, column=0, sticky="e", padx=5)
        self.entElitista = ttk.Entry(frameRuleta, width=12)
        self.entElitista.insert(0, "0.01")
        self.entElitista.grid(row=3, column=1, sticky="w", padx=5, pady=(0,5))

        # =========================================================
        # Configuración de Operadores de Cruza y Mutación
        # =========================================================
        frameOperadores = tk.Frame(lfAlgoritmo)
        frameOperadores.pack(fill="x", padx=5, pady=5)

        lfCruza = ttk.LabelFrame(frameOperadores, text="Operador de Cruza", labelanchor="n")
        lfCruza.pack(side="left", fill="both", expand=True, padx=5)
        
        frameCruzaIn = tk.Frame(lfCruza)
        frameCruzaIn.pack(expand=True)
        tk.Label(frameCruzaIn, text="Puntos Cruza :").grid(row=0, column=0, sticky="e")
        self.entCruza = ttk.Entry(frameCruzaIn, width=12)
        self.entCruza.insert(0, "20")
        self.entCruza.grid(row=0, column=1, sticky="w", padx=5)

        lfMutacion = ttk.LabelFrame(frameOperadores, text="Operador de Mutación", labelanchor="n")
        lfMutacion.pack(side="right", fill="both", expand=True, padx=5)
        
        tk.Label(lfMutacion, text="Probabilidad General :").grid(row=0, column=0, sticky="e", padx=2, pady=(10, 2))
        self.entProb = ttk.Entry(lfMutacion, width=12)
        self.entProb.insert(0, "0.02")
        self.entProb.grid(row=0, column=1, sticky="w", padx=2, pady=(10, 2))

        tk.Label(lfMutacion, text="Probabilidad Facilitador 1 :").grid(row=1, column=0, sticky="e", padx=2, pady=(2, 10))
        self.entPf1 = ttk.Entry(lfMutacion, width=12)
        self.entPf1.insert(0, "0.25")
        self.entPf1.grid(row=1, column=1, sticky="w", padx=2, pady=(2, 10))

        tk.Label(lfMutacion, text="Probabilidad Facilitador 2 :").grid(row=2, column=0, sticky="e", padx=2, pady=(2, 10))
        self.entPf2 = ttk.Entry(lfMutacion, width=12)
        self.entPf2.insert(0, "0.25")
        self.entPf2.grid(row=2, column=1, sticky="w", padx=2, pady=(2, 10))

        tk.Label(lfMutacion, text="Probabilidad Fac. Complementario :").grid(row=3, column=0, sticky="e", padx=2, pady=(2, 10))
        self.entPfc = ttk.Entry(lfMutacion, width=12)
        self.entPfc.insert(0, "0.25")
        self.entPfc.grid(row=3, column=1, sticky="w", padx=2, pady=(2, 10))

        tk.Label(lfMutacion, text="Probabilidad Prof. Ed. Especial :").grid(row=4, column=0, sticky="e", padx=2, pady=(2, 10))
        self.entPfe = ttk.Entry(lfMutacion, width=12)
        self.entPfe.insert(0, "0.25")
        self.entPfe.grid(row=4, column=1, sticky="w", padx=2, pady=(2, 10))

        # =========================================================
        # Panel de visualización de métricas de ejecución
        # =========================================================
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

        # =========================================================
        # Controles de acción principales
        # =========================================================
        frameBotones = tk.Frame(frameDer)
        frameBotones.pack(side="bottom", fill="x", pady=5)

        btnEjecutar = tk.Button(frameBotones, text="Ejecutar Algoritmo", bg="#4CAF50", fg="white", font=("Arial", 10, "bold"),
                                command=self.ejecutarAlgoritmo)
        btnEjecutar.pack(side="left", expand=True, fill="x", padx=5, ipady=5)

        btnExportar = tk.Button(frameBotones, text="Exportar Horarios", bg="#2196F3", fg="white", font=("Arial", 10, "bold"),
                                command=lambda: print("[SISTEMA] Exportación de resultados solicitada."))
        btnExportar.pack(side="left", expand=True, fill="x", padx=5, ipady=5)

        btnCancelar = tk.Button(frameBotones, text="Cancelar", bg="#f44336", fg="white", font=("Arial", 10, "bold"),
                                command=self.volverACarga)
        btnCancelar.pack(side="left", expand=True, fill="x", padx=5, ipady=5)

    def volverACarga(self):
        """
        Finaliza el proceso actual y retorna a la vista de gestión de datos.
        """
        self.controlador.mostrarPantalla(PantallaCarga)

    def ejecutarAlgoritmo(self):
        """
        Orquesta la captura de parámetros, la inicialización espacial (OCH),
        la evolución poblacional (AG) y la actualización asíncrona de la vista.
        """
        try:
            # ==========================================
            # FASE 1: CAPTURA DE PARÁMETROS
            # ==========================================
            print("[SISTEMA] Evaluando parámetros de configuración gráfica...")
            
            # 1.1 Parámetros OCH
            configOCH = OCH(
                idOCH=1, 
                numeroHormigas=int(self.entNumHormigas.get()), 
                feromonaInicial=float(self.entFeromonaInicial.get()), 
                evaporacionFeromona=float(self.entEvaporacion.get()), 
                feromonaGlobal=None, 
                importanciaHeuristica=float(self.entPesoHeuristico.get()), 
                importanciaFeromona=float(self.entPesoFeromona.get()),
                grupoHormigas=int(self.entGrupoHormigas.get()), 
                premioFeromona=float(self.entDepositoFero.get())
            )

            # 1.2 Parámetros AG
            configAG = ConfiguracionAG()
            configAG.numeroGeneraciones = int(self.entGeneraciones.get())
            configAG.solucionesDeseadas = float(self.entSoluciones.get() if self.entSoluciones.get() else 1.0)
            configAG.minutosEjecucion = float(self.entMinutos.get())
            
            configAG.seleccionTorneo = float(self.entTorneo.get())
            configAG.seleccionRuleta = float(self.entRuleta.get())
            configAG.seleccionElitista = float(self.entElitista.get())
            configAG.probGeneralMutacion = float(self.entProb.get())
            
            # Parámetros adicionales capturados de la vista
            configAG.presionSelectiva = float(self.entPresion.get())
            configAG.puntosCruza = int(self.entCruza.get())
            configAG.probMutacionF1 = float(self.entPf1.get())
            configAG.probMutacionF2 = float(self.entPf2.get())
            configAG.probMutacionFC = float(self.entPfc.get())
            configAG.probMutacionPEE = float(self.entPfe.get())

            # ==========================================
            # FASE 1.5: GUARDAR DATOS EN ARCHIVO .TXT
            # ==========================================
            carpeta_logs = "logs_ejecucion"
            if not os.path.exists(carpeta_logs):
                os.makedirs(carpeta_logs)
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_archivo = os.path.join(carpeta_logs, f"ejecucion_{timestamp}.txt")
            
            with open(nombre_archivo, "w", encoding="utf-8") as f:
                f.write("==================================================\n")
                f.write(f"LOG DE EJECUCIÓN - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("==================================================\n\n")
                f.write("--- PARÁMETROS DE PARADA ---\n")
                f.write(f"Generaciones a evaluar: {configAG.numeroGeneraciones}\n")
                f.write(f"Minutos máximos de ejecución: {configAG.minutosEjecucion}\n\n")
                f.write("--- PARÁMETROS OPTIMIZACIÓN COLONIA DE HORMIGAS (OCH) ---\n")
                f.write(f"Número de Hormigas: {configOCH.numeroHormigas}\n")
                f.write(f"Grupo de Hormigas: {configOCH.grupoHormigas}\n")
                f.write(f"Feromona Inicial: {configOCH.feromonaInicial}\n")
                f.write(f"Tasa Evaporación: {configOCH.evaporacionFeromona}\n")
                f.write(f"Depósito de Feromona: {configOCH.premioFeromona}\n")
                f.write(f"Peso Heurístico: {configOCH.importanciaHeuristica}\n")
                f.write(f"Peso Feromona: {configOCH.importanciaFeromona}\n\n")
                f.write("--- PARÁMETROS ALGORITMO GENÉTICO (AG) ---\n")
                f.write(f"Selección Torneo (%): {configAG.seleccionTorneo}\n")
                f.write(f"Selección Ruleta (%): {configAG.seleccionRuleta}\n")
                f.write(f"Selección Elitista (%): {configAG.seleccionElitista}\n")
                f.write(f"Presión Selectiva: {configAG.presionSelectiva}\n")
                f.write(f"Puntos Cruza: {configAG.puntosCruza}\n")
                f.write(f"Probabilidad General Mutación: {configAG.probGeneralMutacion}\n")
                f.write(f"Prob. Mutación F1: {configAG.probMutacionF1}\n")
                f.write(f"Prob. Mutación F2: {configAG.probMutacionF2}\n")
                f.write(f"Prob. Mutación FC: {configAG.probMutacionFC}\n")
                f.write(f"Prob. Mutación PEE: {configAG.probMutacionPEE}\n")
                
            print(f"[SISTEMA] Registro de configuración guardado en {nombre_archivo}.")

            # ==========================================
            # FASE 2: COLONIA DE HORMIGAS (Población Inicial)
            # ==========================================
            print("[SISTEMA] Desplegando Matriz global de Feromonas OCH.")
            algoritmoOCH(configOCH, self.controlador.gestor)
            
            total_esperado = configOCH.numeroHormigas * configOCH.grupoHormigas
            print(f"[SISTEMA] Construyendo heurísticamente {total_esperado} soluciones base (Configuración: {configOCH.grupoHormigas} sub-colonias).")
            
            poblacion_inicial = generarPoblacionInicial(configOCH, self.controlador.gestor)

            # --- Finalización Constructiva ---
            print(f"[SISTEMA] Población inicial conformada por {len(poblacion_inicial)} individuos estocásticos.")

            # ==========================================
            # FASE 3: EVOLUCIÓN GENÉTICA
            # ==========================================
            print("[SISTEMA] Parametrizando motor de inferencia genética.")
            algoritmoAG(configAG) 
            
            print("[SISTEMA] Inicializando evaluación generacional. Procesando en segundo plano...")
            poblacion_final = ejecutarCicloGenetico(poblacion_inicial, configAG, self.controlador.gestor, log_file=nombre_archivo)
            
            campeon = poblacion_final[0]

            # ==========================================
            # FASE 4: ACTUALIZACIÓN DE LA INTERFAZ
            # ==========================================
            print("[SISTEMA] Proceso evolutivo concluido. Renderizando métricas resultantes.")
            
            # 4.1 Actualizar Textos
            minutos, segundos = divmod(configAG.tiempo_ejecucion_final, 60)
            self.lblTiempo.config(text=f"Tiempo de ejecución: {int(minutos)}m {int(segundos)}s")
            self.lblGeneracion.config(text=f"Número de generación: {configAG.generacion_actual}")
            self.lblAptitud.config(text=f"Función de aptitud: {campeon.funcionAptitud:.4f}")

            # 4.2 Actualizar Gráfico
            self.ax.clear() 
            eje_x = list(range(len(configAG.historial_maximos)))
            
            self.ax.fill_between(eje_x, configAG.historial_maximos, color='red', label='Máximo')
            self.ax.fill_between(eje_x, configAG.historial_promedios, color='lime', label='Promedio')
            
            self.ax.set_title("Evolución de la Población", fontsize=10, fontweight='bold')
            self.ax.set_xlabel("Generaciones", fontweight='bold')
            self.ax.set_ylabel("Función de Aptitud", fontweight='bold')
            
            # Ajuste dinámico del eje X para que coincida con las generaciones reales
            max_x = max(1, configAG.generacion_actual - 1) if configAG.generacion_actual > 0 else 1
            self.ax.set_xlim(0, max_x) 
            
            self.ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.25), ncol=2)
            
            self.canvas.draw()

            messagebox.showinfo("Proceso Terminado", 
                                f"Se completó la optimización de horarios.\n\n"
                                f"Generaciones evaluadas: {configAG.generacion_actual}\n"
                                f"Aptitud final alcanzada: {campeon.funcionAptitud:.4f}")

        except ValueError as ve:
            messagebox.showerror("Error de Formato", "Verifique que todos los campos contengan números válidos.\nDetalle: " + str(ve))
        except Exception as e:
            messagebox.showerror("Error de Ejecución", f"Ocurrió un error inesperado:\n{str(e)}")