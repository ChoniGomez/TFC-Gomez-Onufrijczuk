import random
from clases import Hormiga, Cromosoma, Gen, Poblacion
from restricciones import FR3, FR4, FR5, FR6, FR7

class OCH:
    """
    Clase que encapsula la lógica del Algoritmo de Optimización de Colonia de Hormigas.
    Se encarga de inicializar el entorno y generar la población inicial factible 
    para el posterior Algoritmo Genético.
    """
    def __init__(self, gestorDatos):
        self.gestorDatos = gestorDatos
        
        # Matriz de Feromonas Global: Diccionario con clave (idClase, idFacilitador)
        self.matrizFeromonas = {}
        
        # Parámetros del algoritmo
        self.cantidadHormigas = 0
        self.grupoHormigas = 0
        self.tasaEvaporacion = 0.0
        self.feromonaInicial = 0.0
        self.pesoHeuristica = 0.0
        self.pesoFeromona = 0.0
        self.premioFeromona = 0.0  # El premio que dejará la hormiga campeona

    def algoritmoOCH(self, cantidadHormigas, grupoHormigas, tasaEvaporacion, 
                     feromonaInicial, pesoHeuristica, pesoFeromona, premioFeromona):
        """
        Sin retorno. Recibe los parámetros de inicialización del algoritmo de 
        colonia de hormigas y configura la Matriz de Feromonas global.
        """
        self.cantidadHormigas = int(cantidadHormigas)
        self.grupoHormigas = int(grupoHormigas)
        self.tasaEvaporacion = float(tasaEvaporacion)
        self.feromonaInicial = float(feromonaInicial)
        self.pesoHeuristica = float(pesoHeuristica)
        self.pesoFeromona = float(pesoFeromona)
        self.premioFeromona = float(premioFeromona)
        
        # Inicialización de la Matriz de Feromonas (Todas las celdas arrancan en feromonaInicial)
        for clase in self.gestorDatos.listaClases:
            for facilitador in self.gestorDatos.listaFacilitadores:
                self.matrizFeromonas[(clase.idClase, facilitador.idFacilitador)] = self.feromonaInicial
                
        print(f"Sistema: OCH Inicializado con {self.cantidadHormigas} hormigas en {self.grupoHormigas} grupos.")

    def generarPoblacionInicial(self):
        """
        Retorna: Lista de individuos (Cromosomas).
        Ejecuta el ciclo de vida de las hormigas en grupos, aplicando heurísticas 
        (FR1, FR2, FR8), selección por ruleta, evaporación y depósito elitista.
        """
        poblacionTotal = []
        
        # Cálculo de cuántas hormigas van por cada grupo (ej. 40 / 2 = 20)
        hormigasPorGrupo = self.cantidadHormigas // self.grupoHormigas
        idHormigaGlobal = 1
        
        for numGrupo in range(self.grupoHormigas):
            poblacionDelGrupo = []
            
            # =========================================================
            # FASE 1: CONSTRUCCIÓN (Las hormigas arman sus planillas)
            # =========================================================
            for _ in range(hormigasPorGrupo):
                # Instanciamos la hormiga y su cromosoma vacío
                hormiga = Hormiga(idHormiga=idHormigaGlobal, algoritmoOCH=self, poblacion=None)
                cromosomaActual = Cromosoma(idCromosoma=idHormigaGlobal, funcionAptitud=0.0, ordenCromosoma=idHormigaGlobal, poblacion=None)
                
                # La hormiga recorre clase por clase
                for clase in self.gestorDatos.listaClases:
                    genNuevo = Gen(idGen=clase.idClase, idFacilitador1=None, idFacilitador2=None, 
                                   idFacilitadorComplementario=None, idProfesorEducacionEspecial=None, 
                                   evaluar=True, cromosoma=cromosomaActual)
                    
                    # ---------------------------------------------------------
                    # ACA VA LA LÓGICA DE LA RULETA Y EL FILTRO (FR1, FR2, FR8)
                    # Para elegir qué ID asignar a genNuevo.idFacilitador1, etc.
                    # ---------------------------------------------------------
                    
                    cromosomaActual.agregarGen(genNuevo)
                
                poblacionDelGrupo.append(cromosomaActual)
                idHormigaGlobal += 1
                
            # =========================================================
            # FASE 2: EVALUACIÓN PARA BUSCAR A LA CAMPEONA DEL GRUPO
            # =========================================================
            mejorCromosoma = None
            menorConflictos = float('inf')
            
            for cromosoma in poblacionDelGrupo:
                # Se evalúan las restricciones blandas de calidad (las duras ya dieron 0 en la construcción)
                conflictosCalidad = (FR3(cromosoma, self.gestorDatos) + 
                                     FR4(cromosoma, self.gestorDatos) + 
                                     FR5(cromosoma, self.gestorDatos) + 
                                     FR6(cromosoma, self.gestorDatos) + 
                                     FR7(cromosoma, self.gestorDatos))
                
                # Actualizamos quién es la campeona temporal de este lote
                if conflictosCalidad < menorConflictos:
                    menorConflictos = conflictosCalidad
                    mejorCromosoma = cromosoma
            
            # =========================================================
            # FASE 3: EVAPORACIÓN GLOBAL DE LA MATRIZ
            # =========================================================
            for clave in self.matrizFeromonas:
                # Fórmula: Feromona = Feromona * (1 - TasaEvaporacion)
                self.matrizFeromonas[clave] *= (1.0 - self.tasaEvaporacion)
                
            # =========================================================
            # FASE 4: DEPÓSITO DE FEROMONAS (PREMIO ELITISTA)
            # =========================================================
            if mejorCromosoma is not None:
                for gen in mejorCromosoma.genes:
                    idClase = gen.idGen # Como mapeamos idGen = idClase en la creación
                    
                    # Le damos el premio a los facilitadores que la campeona eligió
                    if gen.idFacilitador1:
                        self.matrizFeromonas[(idClase, gen.idFacilitador1)] += self.premioFeromona
                    if gen.idFacilitador2:
                        self.matrizFeromonas[(idClase, gen.idFacilitador2)] += self.premioFeromona
                    if gen.idFacilitadorComplementario:
                        self.matrizFeromonas[(idClase, gen.idFacilitadorComplementario)] += self.premioFeromona
                    if gen.idProfesorEducacionEspecial:
                        self.matrizFeromonas[(idClase, gen.idProfesorEducacionEspecial)] += self.premioFeromona

            # Guardamos las planillas de este grupo en el listado total
            poblacionTotal.extend(poblacionDelGrupo)
            
        print(f"Sistema: Se generaron {len(poblacionTotal)} planillas iniciales.")
        return poblacionTotal