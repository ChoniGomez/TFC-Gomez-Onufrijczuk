import random
import numpy as np
import time
import copy
from clases import Hormiga, Cromosoma, Gen

# Importación de las restricciones individuales (Ahora adaptadas para tensores)
from restricciones import FR1, FR2, FR3, FR4, FR5, FR6, FR7, FR8

# =========================================================================
# FASE 1: CONSTRUCCIÓN HEURÍSTICA (COLONIA DE HORMIGAS)
# =========================================================================

def algoritmoOCH(och, gestorDatos):
    """
    Inicializa la matriz de feromonas global del algoritmo de Optimización 
    por Colonia de Hormigas (OCH).
    Asigna el valor inicial a todas las aristas posibles entre clases y facilitadores.
    """
    if not isinstance(och.feromonaGlobal, dict):
        och.feromonaGlobal = {}
        
    for clase in gestorDatos.listaClases:
        for facilitador in gestorDatos.listaFacilitadores:
            och.feromonaGlobal[(clase.idClase, facilitador.idFacilitador)] = och.feromonaInicial

def _girarRuleta(och, gestorDatos, clase, genActual, cromosomaActual, rol):
    """
    Función estocástica de selección basada en probabilidades (Ruleta).
    Aplica filtros de restricciones duras de manera anticipada para limitar 
    el espacio de búsqueda y reducir la complejidad combinatoria.
    """
    candidatos = gestorDatos.listaFacilitadores
    atractivos = {}
    sumaAtractivos = 0.0
    esPee = (rol == "PEE")
    
    diaClase = clase.horarioDeClase.dia
    modulosClaseActual = set(m.idModuloDeHorario for m in clase.horarioDeClase.modulos)
    
    for facilitador in candidatos:
        idCandidato = facilitador.idFacilitador
        tipoCandidato = facilitador.tipoFacilitador.idTipo
        
        # Filtro excluyente por tipo de perfil requerido
        if esPee and tipoCandidato != 4: continue
        if not esPee and tipoCandidato == 4: continue

        # Validación de competencias formativas (Trayecto)
        esCompetente = False
        if clase.trayecto is None:
            esCompetente = True
        elif facilitador.disponibilidadTrayecto:
            for t in facilitador.disponibilidadTrayecto.trayectos:
                if t.idTrayecto == clase.trayecto.idTrayecto:
                    esCompetente = True
                    break
        if not esCompetente: continue
        
        # Validación de disponibilidad horaria contractual
        estaDisponible = False
        for disp in facilitador.disponibilidadesHorarias:
            if disp.dia == diaClase:
                modulosFacilitador = set(m.idModuloDeHorario for m in disp.modulos)
                if modulosClaseActual.issubset(modulosFacilitador):
                    estaDisponible = True
                    break
        if not estaDisponible: continue
        
        # Validación de solapamiento horario con asignaciones previas en el cromosoma
        tieneChoque = False
        for genAnterior in cromosomaActual.genes:
            if genAnterior.idGen == clase.idClase: continue 
            
            if idCandidato in [genAnterior.idFacilitador1, genAnterior.idFacilitador2, 
                               genAnterior.idFacilitadorComplementario, genAnterior.idProfesorEducacionEspecial]:
                
                claseAnterior = next((c for c in gestorDatos.listaClases if c.idClase == genAnterior.idGen), None)
                if claseAnterior and claseAnterior.horarioDeClase.dia == diaClase:
                    modulosAnteriores = set(m.idModuloDeHorario for m in claseAnterior.horarioDeClase.modulos)
                    if modulosClaseActual.intersection(modulosAnteriores):
                        tieneChoque = True
                        break
        if tieneChoque: continue 

        # Cálculo de atractivo heurístico
        eta = 1.0 
        tau = och.feromonaGlobal.get((clase.idClase, idCandidato), och.feromonaInicial)
        atractivo = (tau ** och.importanciaFeromona) * (eta ** och.importanciaHeuristica)
        
        if atractivo > 0:
            atractivos[idCandidato] = atractivo
            sumaAtractivos += atractivo

    # Resolución en caso de conjunto de candidatos vacío
    if sumaAtractivos == 0.0:
        validos = [f for f in candidatos if (f.tipoFacilitador.idTipo == 4) == esPee]
        if validos: return random.choice(validos).idFacilitador
        return None

    # Selección mediante ruleta proporcional
    r = random.uniform(0.0, 1.0) * sumaAtractivos
    intervaloAcumulado = 0.0
    for idCandidato, valorAtractivo in atractivos.items():
        intervaloAcumulado += valorAtractivo
        if r <= intervaloAcumulado: return idCandidato
            
    return list(atractivos.keys())[-1]

def generarPoblacionInicial(och, gestorDatos):
    """
    Ejecuta el ciclo constructivo de la Colonia de Hormigas.
    Retorna una lista de objetos Cromosoma que representan soluciones factibles iniciales.
    """
    poblacionTotal = []
    grupos = och.grupoHormigas if och.grupoHormigas > 0 else 1
    hormigasPorGrupo = och.numeroHormigas
    idHormigaGlobal = 1
    
    for numGrupo in range(grupos):
        poblacionDelGrupo = []
        for _ in range(hormigasPorGrupo):
            hormiga = Hormiga(idHormiga=idHormigaGlobal, algoritmoOCH=och, poblacion=None)
            cromosomaActual = Cromosoma(idCromosoma=idHormigaGlobal, funcionAptitud=0.0, ordenCromosoma=idHormigaGlobal, poblacion=None)
            
            for clase in gestorDatos.listaClases:
                genNuevo = Gen(idGen=clase.idClase, idFacilitador1=None, idFacilitador2=None, 
                               idFacilitadorComplementario=None, idProfesorEducacionEspecial=None, 
                               evaluar=True, cromosoma=cromosomaActual)
                cromosomaActual.agregarGen(genNuevo)
                genNuevo.idFacilitador1 = _girarRuleta(och, gestorDatos, clase, genNuevo, cromosomaActual, "F1")
                genNuevo.idFacilitador2 = _girarRuleta(och, gestorDatos, clase, genNuevo, cromosomaActual, "F2")
                genNuevo.idFacilitadorComplementario = _girarRuleta(och, gestorDatos, clase, genNuevo, cromosomaActual, "FC")
                
                if clase.tipoDeClase == 3 or clase.tipoDeClase == 4:
                    genNuevo.idProfesorEducacionEspecial = _girarRuleta(och, gestorDatos, clase, genNuevo, cromosomaActual, "PEE")
            
            poblacionDelGrupo.append(cromosomaActual)
            idHormigaGlobal += 1
            
        poblacionTotal.extend(poblacionDelGrupo)
        
    return poblacionTotal

# =========================================================================
# FASE 2: ADAPTACIÓN Y TRANSFORMACIÓN A MODELO MATRICIAL (NUMPY)
# =========================================================================

def inicializarEntornoMatricial(gestorDatos):
    """
    Genera estructuras de datos estáticas (Vectores y Matrices) a partir del 
    modelo de objetos para permitir el procesamiento en álgebra lineal.
    Retorna un diccionario con las estructuras optimizadas.
    """
    mapa_fac_id_a_idx = {fac.idFacilitador: idx for idx, fac in enumerate(gestorDatos.listaFacilitadores)}
    mapa_idx_a_fac_id = {idx: fac.idFacilitador for idx, fac in enumerate(gestorDatos.listaFacilitadores)}
    mapa_clase_id_a_idx = {clase.idClase: idx for idx, clase in enumerate(gestorDatos.listaClases)}
    mapa_idx_a_clase_id = {idx: clase.idClase for idx, clase in enumerate(gestorDatos.listaClases)}

    num_fac = len(gestorDatos.listaFacilitadores)
    num_clases = len(gestorDatos.listaClases)

    mapa_dias = {
        "lunes": 0, "martes": 1, "miercoles": 2, "miércoles": 2, 
        "jueves": 3, "viernes": 4, "sabado": 5, "sábado": 5, "domingo": 6
    }

    vector_horas_max = np.zeros(num_fac, dtype=float)
    vector_es_pee = np.zeros(num_fac, dtype=int)
    vector_perfil_fac = np.zeros(num_fac, dtype=int)
    
    # ==========================================================
    # NUEVO: CÁLCULO DINÁMICO DE LÍMITES (Evitando "Hardcoding")
    # ==========================================================
    # 1. Buscamos el ID máximo de trayecto
    max_id_trayecto = max([int(t.idTrayecto) for t in gestorDatos.listaTrayectos] + [0])
    
    # 2. Buscamos el ID máximo de módulo escaneando clases y disponibilidades
    modulos_en_clases = [int(m.numeroModulo) for c in gestorDatos.listaClases for m in c.horarioDeClase.modulos]
    modulos_en_disp = [int(m.numeroModulo) for f in gestorDatos.listaFacilitadores for d in f.disponibilidadesHorarias for m in d.modulos]
    max_id_modulo = max(modulos_en_clases + modulos_en_disp + [0])
    
    # Creamos las matrices con el tamaño exacto que requieren los datos (+1 por el índice 0)
    matriz_disp_horaria = np.zeros((num_fac, 7, max_id_modulo + 1), dtype=int)
    matriz_conocimiento_trayecto = np.zeros((num_fac, max_id_trayecto + 1), dtype=int)

    for fac in gestorDatos.listaFacilitadores:
        idx = mapa_fac_id_a_idx[fac.idFacilitador]
        vector_horas_max[idx] = float(fac.cantidadHorasCumplir)
        vector_perfil_fac[idx] = int(fac.tipoFacilitador.idTipo)
        if int(fac.tipoFacilitador.idTipo) == 4: vector_es_pee[idx] = 1
        
        for disp in fac.disponibilidadesHorarias:
            dia_texto = str(disp.dia).strip().lower()
            dia_num = mapa_dias.get(dia_texto, 0)
            
            for mod in disp.modulos:
                modulo_num = int(mod.numeroModulo) 
                matriz_disp_horaria[idx, dia_num, modulo_num] = 1
                
        if fac.disponibilidadTrayecto:
            for trayecto in fac.disponibilidadTrayecto.trayectos:
                id_trayecto = int(trayecto.idTrayecto) 
                matriz_conocimiento_trayecto[idx, id_trayecto] = 1

    vector_tipo_clase = np.zeros(num_clases, dtype=int)
    matriz_clases_req = np.zeros((num_clases, 4), dtype=int)
    
    for clase in gestorDatos.listaClases:
        idx = mapa_clase_id_a_idx[clase.idClase]
        vector_tipo_clase[idx] = int(clase.tipoDeClase)
        
        dia_texto_clase = str(clase.horarioDeClase.dia).strip().lower()
        matriz_clases_req[idx, 0] = mapa_dias.get(dia_texto_clase, 0)
        
        modulos = sorted([int(m.numeroModulo) for m in clase.horarioDeClase.modulos])
        if modulos:
            matriz_clases_req[idx, 1] = modulos[0]
            matriz_clases_req[idx, 2] = modulos[-1]
            
        matriz_clases_req[idx, 3] = int(clase.trayecto.idTrayecto) if clase.trayecto else -1

    datos_numpy = {
        "mapa_fac_id_a_idx": mapa_fac_id_a_idx,
        "mapa_idx_a_fac_id": mapa_idx_a_fac_id,
        "mapa_clase_id_a_idx": mapa_clase_id_a_idx,
        "mapa_idx_a_clase_id": mapa_idx_a_clase_id,
        "clases_req": matriz_clases_req,
        "disp_horaria": matriz_disp_horaria,
        "conocimiento_trayecto": matriz_conocimiento_trayecto,
        "horas_max": vector_horas_max,
        "es_pee": vector_es_pee,
        "tipo_clase": vector_tipo_clase,
        "perfil_fac": vector_perfil_fac
    }
    return datos_numpy

def codificarPoblacionMatricial(poblacion_objetos, datos_numpy):
    """
    Convierte la lista de objetos Cromosoma en un tensor 3D de NumPy.
    Dimensiones: [Num_Individuos, Num_Clases, 4_Roles].
    """
    mapa_clase_id_a_idx = datos_numpy["mapa_clase_id_a_idx"]
    mapa_fac_id_a_idx = datos_numpy["mapa_fac_id_a_idx"]
    
    num_individuos = len(poblacion_objetos)
    num_clases = len(mapa_clase_id_a_idx)
    
    tensor_poblacion = np.full((num_individuos, num_clases, 4), -1, dtype=int)
    
    for i, cromosoma in enumerate(poblacion_objetos):
        for gen in cromosoma.genes:
            idx_clase = mapa_clase_id_a_idx[gen.idGen]
            if gen.idFacilitador1 is not None: tensor_poblacion[i, idx_clase, 0] = mapa_fac_id_a_idx[gen.idFacilitador1]
            if gen.idFacilitador2 is not None: tensor_poblacion[i, idx_clase, 1] = mapa_fac_id_a_idx[gen.idFacilitador2]
            if gen.idFacilitadorComplementario is not None: tensor_poblacion[i, idx_clase, 2] = mapa_fac_id_a_idx[gen.idFacilitadorComplementario]
            if gen.idProfesorEducacionEspecial is not None: tensor_poblacion[i, idx_clase, 3] = mapa_fac_id_a_idx[gen.idProfesorEducacionEspecial]
                
    return tensor_poblacion

def decodificarCromosomaOptimo(tensor_ganador, modelo_cromosoma, datos_numpy):
    """
    Reconstruye el objeto Cromosoma original a partir del tensor bidimensional 
    que representa la mejor solución encontrada.
    """
    mapa_idx_a_fac_id = datos_numpy["mapa_idx_a_fac_id"]
    
    cromosoma_final = copy.deepcopy(modelo_cromosoma)
    
    for gen in cromosoma_final.genes:
        idx_clase = datos_numpy["mapa_clase_id_a_idx"][gen.idGen]
        roles = tensor_ganador[idx_clase]
        
        gen.idFacilitador1 = mapa_idx_a_fac_id[roles[0]] if roles[0] != -1 else None
        gen.idFacilitador2 = mapa_idx_a_fac_id[roles[1]] if roles[1] != -1 else None
        gen.idFacilitadorComplementario = mapa_idx_a_fac_id[roles[2]] if roles[2] != -1 else None
        gen.idProfesorEducacionEspecial = mapa_idx_a_fac_id[roles[3]] if roles[3] != -1 else None
        
    return cromosoma_final

# =========================================================================
# EVALUACIÓN DE APTITUD INTEGRADORA
# =========================================================================

def evaluarFuncionAptitud(tensor_cromosoma, datos_numpy):
    """
    Calcula la función de aptitud (fitness) de un cromosoma evaluando
    todas las restricciones (duras y blandas) mediante procesamiento tensorial.
    Fórmula: f_fitness(Ck) = 1 / (1 + sumatoria_penalizaciones)
    """
    total_penalizaciones = (
        FR1(tensor_cromosoma, datos_numpy) +
        FR2(tensor_cromosoma, datos_numpy) +
        FR3(tensor_cromosoma, datos_numpy) +
        FR4(tensor_cromosoma, datos_numpy) +
        FR5(tensor_cromosoma, datos_numpy) +
        FR6(tensor_cromosoma, datos_numpy) +
        FR7(tensor_cromosoma, datos_numpy) +
        FR8(tensor_cromosoma, datos_numpy)
    )
    
    return 1.0 / (1.0 + total_penalizaciones)

# =========================================================================
# FASE 3: OPERADORES GENÉTICOS (PROCESAMIENTO TENSORIAL)
# =========================================================================

def operadorSeleccion(tensor_poblacion, aptitudes, elitismo, torneo, ruleta):
    """
    Aplica los métodos de selección (Elitismo, Torneo y Ruleta) sobre la población 
    representada matricialmente.
    Retorna el tensor correspondiente a la población intermedia.
    """
    num_individuos = tensor_poblacion.shape[0]
    poblacion_intermedia = np.zeros_like(tensor_poblacion)
    
    indices_ordenados = np.argsort(aptitudes)[::-1]
    
    # Conservación de la élite
    cantidad_elite = max(1, int(num_individuos * elitismo))
    indices_elite = indices_ordenados[:cantidad_elite]
    poblacion_intermedia[:cantidad_elite] = tensor_poblacion[indices_elite]
    
    promedio_TR = (torneo + ruleta) / 2.0
    umbral_formula = 1.0 - (torneo / promedio_TR) if promedio_TR > 0 else 0.5
    
    suma_aptitud = np.sum(aptitudes)
    probabilidades = aptitudes / suma_aptitud if suma_aptitud > 0 else np.ones(num_individuos) / num_individuos
    
    for i in range(cantidad_elite, num_individuos):
        alfa = random.uniform(0.0, 1.0)
        if alfa > umbral_formula:
            participantes = np.random.choice(num_individuos, size=3, replace=False)
            mejor_idx = participantes[np.argmax(aptitudes[participantes])]
            poblacion_intermedia[i] = tensor_poblacion[mejor_idx]
        else:
            elegido_idx = np.random.choice(num_individuos, p=probabilidades)
            poblacion_intermedia[i] = tensor_poblacion[elegido_idx]
            
    return poblacion_intermedia

def operadorCruza(poblacion_intermedia, cantidad_elite, prob_cruza=0.90):
    """
    Aplica el operador de cruce multipunto mediante partición e intercambio 
    de segmentos de matrices (Slicing).
    """
    num_individuos, num_clases, num_roles = poblacion_intermedia.shape
    poblacion_cruzada = np.zeros_like(poblacion_intermedia)
    
    poblacion_cruzada[:cantidad_elite] = poblacion_intermedia[:cantidad_elite]
    
    indices_padres = np.arange(cantidad_elite, num_individuos)
    np.random.shuffle(indices_padres)
    
    for i in range(0, len(indices_padres), 2):
        if i + 1 >= len(indices_padres):
            poblacion_cruzada[cantidad_elite + i] = poblacion_intermedia[indices_padres[i]]
            break
            
        idx_p1 = indices_padres[i]
        idx_p2 = indices_padres[i+1]
        
        if random.random() <= prob_cruza:
            cortes = sorted(random.sample(range(1, num_clases), 3))
            
            hijo1 = poblacion_intermedia[idx_p1].copy()
            hijo2 = poblacion_intermedia[idx_p2].copy()
            
            hijo1[cortes[0]:cortes[1]] = poblacion_intermedia[idx_p2, cortes[0]:cortes[1]]
            hijo2[cortes[0]:cortes[1]] = poblacion_intermedia[idx_p1, cortes[0]:cortes[1]]
            
            if len(cortes) > 2:
                hijo1[cortes[2]:] = poblacion_intermedia[idx_p2, cortes[2]:]
                hijo2[cortes[2]:] = poblacion_intermedia[idx_p1, cortes[2]:]
                
            poblacion_cruzada[cantidad_elite + i] = hijo1
            poblacion_cruzada[cantidad_elite + i + 1] = hijo2
        else:
            poblacion_cruzada[cantidad_elite + i] = poblacion_intermedia[idx_p1]
            poblacion_cruzada[cantidad_elite + i + 1] = poblacion_intermedia[idx_p2]
            
    return poblacion_cruzada

def operadorMutacion(poblacion_cruzada, datos_numpy, cantidad_elite, prob_mutacion=0.05):
    """
    Aplica alteraciones genéticas aleatorias sobre las matrices generadas, 
    garantizando la integridad referencial de los índices de facilitadores.
    """
    num_individuos, num_clases, num_roles = poblacion_cruzada.shape
    matriz_es_pee = datos_numpy["es_pee"]
    
    ids_regulares = np.where(matriz_es_pee == 0)[0]
    ids_pee = np.where(matriz_es_pee == 1)[0]
    
    mascara_mutacion = np.random.random((num_individuos - cantidad_elite, num_clases)) < prob_mutacion
    
    for idx_indiv_relativo in range(num_individuos - cantidad_elite):
        idx_real = cantidad_elite + idx_indiv_relativo
        clases_a_mutar = np.where(mascara_mutacion[idx_indiv_relativo])[0]
        
        for clase_idx in clases_a_mutar:
            roles_activos = np.where(poblacion_cruzada[idx_real, clase_idx] != -1)[0]
            if len(roles_activos) == 0: continue
            
            rol_a_mutar = np.random.choice(roles_activos)
            
            if rol_a_mutar == 3:
                if len(ids_pee) > 0:
                    poblacion_cruzada[idx_real, clase_idx, rol_a_mutar] = np.random.choice(ids_pee)
            else:
                if len(ids_regulares) > 0:
                    poblacion_cruzada[idx_real, clase_idx, rol_a_mutar] = np.random.choice(ids_regulares)
                    
    return poblacion_cruzada

# =========================================================================
# FASE 4: ORQUESTACIÓN PRINCIPAL DEL ALGORITMO GENÉTICO
# =========================================================================

def algoritmoAG(configAG):
    """
    Inicializa los parámetros de seguimiento de la ejecución evolutiva.
    """
    configAG.historial_maximos = []
    configAG.historial_promedios = []
    configAG.generacion_actual = 0
    configAG.tiempo_inicio = time.time()
    configAG.tiempo_ejecucion_final = 0.0

def ejecutarCicloGenetico(poblacion_objetos, configAG, gestorDatos):
    """
    Controlador principal. Mapea la población a tensores matriciales, evalúa,
    aplica presiones evolutivas y decodifica el resultado óptimo al formato original.
    """
    print("Sistema: Inicializando entorno matricial de restricciones...")
    datos_numpy = inicializarEntornoMatricial(gestorDatos)
    
    print("Sistema: Codificando población inicial a modelo tensorial...")
    tensor_poblacion = codificarPoblacionMatricial(poblacion_objetos, datos_numpy)
    
    num_individuos = tensor_poblacion.shape[0]
    aptitudes = np.zeros(num_individuos)
    
    for i in range(num_individuos):
        aptitudes[i] = evaluarFuncionAptitud(tensor_poblacion[i], datos_numpy)
        
    configAG.historial_maximos.append(np.max(aptitudes))
    configAG.historial_promedios.append(np.mean(aptitudes))

    elitismo = configAG.seleccionElitista
    cantidad_elite = max(1, int(num_individuos * elitismo))

    print("Sistema: Iniciando ciclo evolutivo del Algoritmo Genético...")

    while True:
        # Verificación de criterios de convergencia y parada
        if configAG.generacion_actual >= configAG.numeroGeneraciones:
            print(f"Sistema: Criterio de parada alcanzado: Límite de generaciones ({configAG.numeroGeneraciones}).")
            break
            
        tiempo_transcurrido_minutos = (time.time() - configAG.tiempo_inicio) / 60.0
        if tiempo_transcurrido_minutos >= configAG.minutosEjecucion:
            print(f"Sistema: Criterio de parada alcanzado: Límite de tiempo ({configAG.minutosEjecucion} min).")
            break
            
        if np.max(aptitudes) >= 1.0:
            print("Sistema: Solución óptima global encontrada (Aptitud 1.0).")
            break
            
        # Aplicación de operadores genéticos matriciales
        pob_intermedia = operadorSeleccion(tensor_poblacion, aptitudes, elitismo, 
                                           configAG.seleccionTorneo, configAG.seleccionRuleta)
        
        pob_cruzada = operadorCruza(pob_intermedia, cantidad_elite, prob_cruza=0.90)
        
        tensor_poblacion = operadorMutacion(pob_cruzada, datos_numpy, cantidad_elite, 
                                            prob_mutacion=configAG.probGeneralMutacion)
        
        # Evaluación de la descendencia
        for i in range(num_individuos):
            aptitudes[i] = evaluarFuncionAptitud(tensor_poblacion[i], datos_numpy)
            
        # Registro de métricas poblacionales
        configAG.generacion_actual += 1
        configAG.historial_maximos.append(np.max(aptitudes))
        configAG.historial_promedios.append(np.mean(aptitudes))

    configAG.tiempo_ejecucion_final = time.time() - configAG.tiempo_inicio
    
    print("Sistema: Evolución finalizada. Decodificando cromosoma óptimo...")
    idx_mejor = np.argmax(aptitudes)
    matriz_campeona = tensor_poblacion[idx_mejor]
    
    modelo_cromosoma = poblacion_objetos[0]
    cromosoma_ganador = decodificarCromosomaOptimo(matriz_campeona, modelo_cromosoma, datos_numpy)
    cromosoma_ganador.funcionAptitud = aptitudes[idx_mejor]
    
    return [cromosoma_ganador]