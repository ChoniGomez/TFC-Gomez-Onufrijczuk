import tkinter as tk
import os
from datetime import datetime
from collections import defaultdict
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from clases import OCH

from algoritmo import (algoritmoOCH, generarPoblacionInicial, evaluarFuncionAptitud, 
                       algoritmoAG, ejecutarCicloGenetico)

class ConfiguracionAG:
    """Clase para guardar los parámetros del Algoritmo Genético."""
    def __init__(self):
        pass


class PantallaInicio(tk.Frame):
    """
    Pantalla de bienvenida.
    """
    def __init__(self, parent, controlador):
        super().__init__(parent)
        # Contenedor para centrar los elementos verticalmente
        container = tk.Frame(self)
        container.pack(expand=True)

        tk.Label(container, text="Trabajo Final de Carrera (TFC)", font=("Arial", 20, "bold")).pack()

        ttk.Separator(container, orient='horizontal').pack(fill='x', padx=100, pady=15)

        details_text = (
            "• Título: Optimización de la planificación de horarios y recursos en la Escuela de Robótica de Misiones\n"
            "  mediante algoritmos genéticos y de colonia de hormigas.\n\n"
            "• Autores: Gomez, Jonathan Matias & Onufrijczuk, Juan Marcos.\n\n"
            "• Director: Esp. Ing. Berger, Javier.\n"
            "• Codirector: Mgtr. Ing. Pedrazzini, Liliana.\n\n"
            "• Carrera: Ingeniería en Informática (Plan 2017).\n"
            "• Universidad: Universidad Gastón Dachary (UGD).\n"
            "• Año: 2026."
        )
        
        # Frame para alinear el bloque de texto a la izquierda dentro del contenedor centrado
        details_frame = tk.Frame(container)
        details_frame.pack(pady=10)
        
        tk.Label(details_frame, text=details_text, justify=tk.LEFT, font=("Arial", 15)).pack()

        tk.Button(container, text="INICIAR", width=20, height=2, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"),
                  command=lambda: controlador.mostrarPantalla(PantallaCarga)).pack(pady=40)


class PantallaCarga(tk.Frame):
    """
    Pantalla para cargar los archivos CSV.
    """
    def __init__(self, parent, controlador):
        super().__init__(parent)
        self.controlador = controlador
        self.checksVisuales = {}

        # Contenedor principal para centrar todo el contenido
        container = tk.Frame(self)
        container.pack(expand=True)

        tk.Label(container, text="Carga de Archivos CSV", font=("Arial", 16, "bold"), pady=20).pack()
        # Archivos necesarios
        opciones = [
            ("Cargar facilitadores", "facilitadores"),
            ("Cargar trayectos", "trayectos"),
            ("Cargar facilitadores - trayectos", "fac_trayectos"),
            ("Cargar disponibilidad horaria", "disponibilidad"),
            ("Cargar horarios de clases", "horarios_clases")
        ]

        # Frame para alinear los botones
        frameCentral = tk.Frame(container)
        frameCentral.pack(pady=10)

        for texto, clave in opciones:
            frameFila = tk.Frame(frameCentral)
            frameFila.pack(pady=10, fill="x")

            btn = tk.Button(frameFila, text=texto, width=40, anchor="w",
                            font=("Arial", 11), cursor="hand2",
                            command=lambda c=clave: self.seleccionarArchivo(c))
            btn.pack(side="left", ipady=5)

            # Revisa si el archivo ya se cargó
            cargado = self.controlador.gestor.tieneDatos(clave)
            
            estadoInicial = "✅" if cargado else "❌"
            colorInicial = "green" if cargado else "red"
            
            lblCheck = tk.Label(frameFila, text=estadoInicial, fg=colorInicial, font=("Arial", 14, "bold"), padx=15)
            lblCheck.pack(side="left")
            
            self.checksVisuales[clave] = lblCheck

        # Botón para ir a la siguiente pantalla
        btnSiguiente = tk.Button(container, text="Siguiente →", width=15, bg="#2196F3", fg="white",
                                 font=("Arial", 12, "bold"), cursor="hand2",
                                 command=self.irAAlgoritmo)
        btnSiguiente.pack(pady=40, ipady=5)

    def seleccionarArchivo(self, clave):
        """
        Abre el diálogo para seleccionar un archivo y lo manda a cargar.
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
        Verifica que todos los archivos estén cargados antes de continuar.
        """
        if not self.controlador.gestor.estanDatosListos():
            messagebox.showwarning("Atención", "Es necesario cargar todos los archivos CSV para continuar.")
        else:
            self.controlador.mostrarPantalla(PantallaAlgoritmo)


class PantallaAlgoritmo(tk.Frame):
    """
    Pantalla principal para configurar y ejecutar el algoritmo.
    """
    def __init__(self, parent, controlador):
        super().__init__(parent)
        self.controlador = controlador
        self.solucion_campeona = None
        
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.crearPanelIzquierdo()
        self.crearPanelDerecho()

    def crearPanelIzquierdo(self):
        """
        Crea el panel del gráfico de evolución.
        """
        frameIzq = tk.Frame(self, padx=10, pady=10)
        frameIzq.grid(row=0, column=0, sticky="nsew")

        lfGrafico = ttk.LabelFrame(frameIzq, text="Evolución de la Población")
        lfGrafico.pack(fill="both", expand=True, pady=10)

        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        
        # Configura el gráfico antes de la ejecución.
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
        Crea el panel de configuración y resultados.
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
        tk.Label(frameCruzaIn, text="Puntos Cruza :").grid(row=0, column=0, sticky="e", pady=5)
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
                                command=self.exportarHorarios)
        btnExportar.pack(side="left", expand=True, fill="x", padx=5, ipady=5)

        btnCancelar = tk.Button(frameBotones, text="Cancelar", bg="#f44336", fg="white", font=("Arial", 10, "bold"),
                                command=self.volverACarga)
        btnCancelar.pack(side="left", expand=True, fill="x", padx=5, ipady=5)

    def volverACarga(self):
        """
        Finaliza el proceso actual y retorna a la vista de gestión de datos.
        """
        self.controlador.mostrarPantalla(PantallaCarga)

    def exportarHorarios(self):
        """
        Exporta la solución campeona a un archivo CSV.
        """
        if not self.solucion_campeona:
            messagebox.showwarning("Advertencia", "Primero debe ejecutar el algoritmo para generar un horario antes de exportar.")
            return

        try:
            # Mapas para búsquedas eficientes
            clase_id_map = {c.idClase: c for c in self.controlador.gestor.listaClases}
            fac_id_name_map = {f.idFacilitador: f"{f.nombre} {f.apellido}" for f in self.controlador.gestor.listaFacilitadores}

            def _modulo_a_hora_str(modulo):
                if not modulo or modulo <= 0:
                    return ""
                total_cuartos = modulo - 1
                hora = 8 + total_cuartos // 4
                minutos = (total_cuartos % 4) * 15
                return f"{hora:02d}:{minutos:02d}"

            data_para_exportar = []
            for gen in self.solucion_campeona.genes:
                clase = clase_id_map.get(gen.idGen)
                if not clase:
                    continue

                modulos = [m.numeroModulo for m in clase.horarioDeClase.modulos]
                hora_inicio_str = ""
                hora_fin_str = ""
                if modulos:
                    start_mod = min(modulos)
                    # La hora de fin es el inicio del siguiente bloque al último
                    end_mod = max(modulos) + 1
                    hora_inicio_str = _modulo_a_hora_str(start_mod)
                    hora_fin_str = _modulo_a_hora_str(end_mod)

                # Determinar el string del tipo de clase
                tipo_clase_str = "-"
                if clase.tipoDeClase == 5:
                    tipo_clase_str = "SPRINT"
                elif clase.trayecto and clase.trayecto.tipoTrayecto:
                    tipo_clase_str = clase.trayecto.tipoTrayecto.nombre

                record = {
                    'Salon': clase.salon.nombre if clase.salon else "-",
                    'Dia': clase.horarioDeClase.dia,
                    'Hora Inicio': hora_inicio_str,
                    'Hora Fin': hora_fin_str,
                    'Trayecto': clase.trayecto.nombre.upper() if clase.trayecto else "-",
                    'Nivel': clase.trayecto.nivel.upper() if clase.trayecto else "-",
                    'Tipo de Clase': tipo_clase_str,
                    'Facilitador 1': fac_id_name_map.get(gen.idFacilitador1, "-"),
                    'Facilitador 2': fac_id_name_map.get(gen.idFacilitador2, "-"),
                    'Facilitador Complementario': fac_id_name_map.get(gen.idFacilitadorComplementario, "-"),
                    'Profesor de Educacion Especial': fac_id_name_map.get(gen.idProfesorEducacionEspecial, "-")
                }

                # --- Búsqueda de Suplentes (Lógica de Emergencia Simplificada) ---
                # Un suplente es cualquier Facilitador Complementario (FC) de otra clase que se esté dando al mismo tiempo.
                # No se considera competencia, disponibilidad ni experiencia.
                suplentes_potenciales_ids = set()
                ranked_substitutes = []

                if clase and clase.trayecto and clase.horarioDeClase.modulos:
                    clase_actual_dia = clase.horarioDeClase.dia
                    clase_actual_modulos = [m.numeroModulo for m in clase.horarioDeClase.modulos]
                    clase_actual_start = min(clase_actual_modulos)
                    clase_actual_end = max(clase_actual_modulos)

                    # Iterar a través de todas las demás clases para encontrar las concurrentes
                    for other_gen in self.solucion_campeona.genes:
                        if other_gen.idGen == gen.idGen:
                            continue

                        other_clase = clase_id_map.get(other_gen.idGen)
                        if not other_clase or not other_clase.horarioDeClase.modulos:
                            continue
                        
                        # Verificar si hay superposición de horarios
                        if other_clase.horarioDeClase.dia == clase_actual_dia:
                            other_modulos = [m.numeroModulo for m in other_clase.horarioDeClase.modulos]
                            other_start = min(other_modulos)
                            other_end = max(other_modulos)

                            # Si los horarios se superponen y la otra clase tiene un FC, se añade como potencial suplente
                            if (clase_actual_start <= other_end and other_start <= clase_actual_end) and other_gen.idFacilitadorComplementario is not None:
                                suplentes_potenciales_ids.add(other_gen.idFacilitadorComplementario)

                    # Eliminar de la lista de suplentes a los facilitadores que ya están asignados a la clase actual
                    current_assigned_facs = {gen.idFacilitador1, gen.idFacilitador2, gen.idFacilitadorComplementario, gen.idProfesorEducacionEspecial}
                    suplentes_final_ids = list(suplentes_potenciales_ids - current_assigned_facs)
                    
                    # Obtener los nombres de los primeros 4 suplentes
                    ranked_substitutes = [fac_id_name_map.get(fid) for fid in suplentes_final_ids[:4]]

                record['Suplente 1'] = ranked_substitutes[0] if len(ranked_substitutes) > 0 else "-"
                record['Suplente 2'] = ranked_substitutes[1] if len(ranked_substitutes) > 1 else "-"
                record['Suplente 3'] = ranked_substitutes[2] if len(ranked_substitutes) > 2 else "-"
                record['Suplente 4'] = ranked_substitutes[3] if len(ranked_substitutes) > 3 else "-"
                data_para_exportar.append(record)
            
            df = pd.DataFrame(data_para_exportar)

            filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Archivos CSV", "*.csv")], initialfile="Horas_Clases_Solucion.csv", title="Guardar Horario Generado")
            if filepath:
                # --- Lógica para reordenar y ordenar el DataFrame antes de exportar ---
                
                # 1. Definir el nuevo orden de las columnas según lo solicitado.
                nuevo_orden_columnas = [
                    'Hora Inicio', 'Hora Fin', 'Dia', 'Salon', 'Trayecto', 'Nivel', 
                    'Tipo de Clase', 'Facilitador 1', 'Facilitador 2', 
                    'Facilitador Complementario', 'Profesor de Educacion Especial',
                    'Suplente 1', 'Suplente 2', 'Suplente 3', 'Suplente 4'
                ]
                df = df[nuevo_orden_columnas]

                # 2. Definir el orden correcto de los días de la semana para el ordenamiento de filas.
                dias_ordenados = ['Lunes', 'Martes', 'Miercoles', 'Miércoles', 'Jueves', 'Viernes', 'Sabado', 'Sábado', 'Domingo']
                
                # 3. Convertir la columna 'Dia' a un tipo categórico con el orden personalizado.
                #    Esto asegura que al ordenar, se respete el orden de la semana y no el alfabético.
                df['Dia'] = pd.Categorical(df['Dia'], categories=dias_ordenados, ordered=True)
                
                # 4. Ordenar las filas: primero por día y luego por hora de inicio.
                df.sort_values(by=['Dia', 'Hora Inicio'], inplace=True)
                df.to_csv(filepath, index=False, encoding='utf-8-sig')
                messagebox.showinfo("Éxito", f"El horario ha sido exportado correctamente en:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Error de Exportación", f"Ocurrió un error al exportar el horario:\n{str(e)}")

    def ejecutarAlgoritmo(self):
        """
        Orquesta todo el proceso: captura parámetros, ejecuta OCH y AG, y actualiza la interfaz.
        """
        try:
            # ==========================================
            # FASE 1: CAPTURAR PARÁMETROS DE LA INTERFAZ
            # ==========================================
            print("[SISTEMA] Evaluando parámetros de configuración gráfica...")
            
            # 1.1 Parámetros OCH
            configOCH = OCH( # noqa
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
            # FASE 2: GUARDAR CONFIGURACIÓN EN LOG
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
            # FASE 3: EJECUTAR OCH PARA POBLACIÓN INICIAL
            # ==========================================
            print("[SISTEMA] Desplegando Matriz global de Feromonas OCH.")
            algoritmoOCH(configOCH, self.controlador.gestor)
            
            total_esperado = configOCH.numeroHormigas * configOCH.grupoHormigas
            print(f"[SISTEMA] Construyendo heurísticamente {total_esperado} soluciones base (Configuración: {configOCH.grupoHormigas} sub-colonias).")
            
            poblacion_inicial = generarPoblacionInicial(configOCH, self.controlador.gestor)

            # --- Finalización Constructiva ---
            print(f"[SISTEMA] Población inicial conformada por {len(poblacion_inicial)} individuos estocásticos.")

            # ==========================================
            # FASE 4: EJECUTAR ALGORITMO GENÉTICO
            # ==========================================
            print("[SISTEMA] Parametrizando motor de inferencia genética.")
            algoritmoAG(configAG) 
            
            print("[SISTEMA] Inicializando evaluación generacional. Procesando en segundo plano...")
            poblacion_final = ejecutarCicloGenetico(poblacion_inicial, configAG, self.controlador.gestor, log_file=nombre_archivo)
            
            campeon = poblacion_final[0]
            self.solucion_campeona = campeon

            # ==========================================
            # FASE 5: MOSTRAR RESULTADOS
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
            
            # Ajuste dinámico del eje X para las generaciones
            max_x_limit = max(1, configAG.generacion_actual)
            self.ax.set_xlim(0, max_x_limit) 
            
            self.ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.3), ncol=2)
            
            self.fig.tight_layout()  # Ajusta el gráfico para que la leyenda sea visible.
            self.canvas.draw()

            messagebox.showinfo("Proceso Terminado", 
                                f"Se completó la optimización de horarios.\n\n"
                                f"Generaciones evaluadas: {configAG.generacion_actual}\n"
                                f"Aptitud final alcanzada: {campeon.funcionAptitud:.4f}")

        except ValueError as ve:
            messagebox.showerror("Error de Formato", "Verifique que todos los campos contengan números válidos.\nDetalle: " + str(ve))
        except Exception as e:
            messagebox.showerror("Error de Ejecución", f"Ocurrió un error inesperado:\n{str(e)}")