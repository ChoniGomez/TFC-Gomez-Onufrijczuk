import random
import numpy as np
import time
import copy
from collections import defaultdict
from clases import Hormiga, Cromosoma, Gen

# Importación de las restricciones del modelo adaptadas para el procesamiento tensorial
from restricciones import FR1, FR2, FR3, FR4, FR5, FR6, FR7, FR8

# =========================================================================
# FASE 1: CONSTRUCCIÓN HEURÍSTICA (COLONIA DE HORMIGAS)
# =========================================================================

def algoritmoOCH(och, gestorDatos):
    """
    Inicializa la matriz de feromonas con un valor base para todas las
    posibles asignaciones (clase, facilitador).
    """
    if not isinstance(och.feromonaGlobal, dict):
        och.feromonaGlobal = {}
        
    for clase in gestorDatos.listaClases:
        for facilitador in gestorDatos.listaFacilitadores:
            och.feromonaGlobal[(clase.idClase, facilitador.idFacilitador)] = och.feromonaInicial

def _girarRuleta(och, gestorDatos, clase, horarios_hormiga, workload_hormiga, rol, mapa_dias):
    """
    Selecciona un facilitador para una clase usando una ruleta.
    Aplica filtros previos (restricciones duras) para optimizar la búsqueda.
    """
    candidatos = gestorDatos.listaFacilitadores
    atractivos = {}
    sumaAtractivos = 0.0
    esPee = (rol == "PEE")
    
    dia_num = mapa_dias.get(clase.horarioDeClase.dia.strip().lower(), -1)
    modulos_clase = [m.numeroModulo for m in clase.horarioDeClase.modulos]
    
    for facilitador in candidatos:
        idCandidato = facilitador.idFacilitador
        tipoCandidato = facilitador.tipoFacilitador.idTipo
        
        # Filtro excluyente por tipo de perfil requerido
        if esPee and tipoCandidato != 4: continue
        if not esPee and tipoCandidato == 4: continue

        # Filtro: el facilitador debe ser competente para el trayecto.
        esCompetente = False
        if clase.trayecto is None:
            esCompetente = True
        elif facilitador.disponibilidadTrayecto:
            for t in facilitador.disponibilidadTrayecto.trayectos:
                if t.idTrayecto == clase.trayecto.idTrayecto:
                    esCompetente = True
                    break
        if not esCompetente: continue
        
        # Filtro: el facilitador debe tener disponibilidad horaria para la clase.
        estaDisponible = False
        for disp in facilitador.disponibilidadesHorarias:
            if disp.dia == clase.horarioDeClase.dia:
                modulosFacilitador = set(m.idModuloDeHorario for m in disp.modulos)
                modulosClaseActual = set(m.idModuloDeHorario for m in clase.horarioDeClase.modulos)
                if modulosClaseActual.issubset(modulosFacilitador):
                    estaDisponible = True
                    break
        if not estaDisponible: continue
        
        # Filtro: el facilitador no debe tener otra clase en el mismo horario.
        tieneChoque = False
        if idCandidato in horarios_hormiga and modulos_clase and dia_num != -1:
            timeline_candidato = horarios_hormiga[idCandidato]
            inicio_clase = min(modulos_clase)
            fin_clase = max(modulos_clase)
            if np.any(timeline_candidato[dia_num, inicio_clase:fin_clase+1] > 0):
                tieneChoque = True
        if tieneChoque: continue 
        
        # Filtro: la asignación no debe exceder las horas de contrato del facilitador.
        carga_actual_modulos = workload_hormiga.get(idCandidato, 0)
        duracion_clase_modulos = len(modulos_clase)
        max_modulos_contrato = facilitador.cantidadHorasCumplir * 4
        
        if max_modulos_contrato > 0 and (carga_actual_modulos + duracion_clase_modulos) > max_modulos_contrato:
            continue

        # Heurística: se priorizan facilitadores que aún no han cumplido su carga mínima.
        min_modulos_contrato = (facilitador.cantidadHorasCumplir * 4) * 0.8
        if min_modulos_contrato > 0 and carga_actual_modulos >= min_modulos_contrato:
            continue
            
        # Cálculo de atractivo: combina la feromona y una heurística.
        # La heurística prefiere a facilitadores con menor carga horaria actual.
        eta = 1.0 / (1.0 + carga_actual_modulos)

        tau = och.feromonaGlobal.get((clase.idClase, idCandidato), och.feromonaInicial)
        atractivo = (tau ** och.importanciaFeromona) * (eta ** och.importanciaHeuristica)
        
        if atractivo > 0:
            atractivos[idCandidato] = atractivo
            sumaAtractivos += atractivo

    # Si no hay candidatos atractivos, se elige uno al azar que cumpla el perfil.
    if sumaAtractivos == 0.0:
        # --- INICIO DE FALLBACK MEJORADO ---
        # Si no hay candidatos "perfectos", se intenta asignar uno que al menos no genere un choque de horario.
        candidatos_sin_choque = []
        for facilitador in candidatos:
            idCandidato = facilitador.idFacilitador
            tipoCandidato = facilitador.tipoFacilitador.idTipo
            
            if (esPee and tipoCandidato != 4) or (not esPee and tipoCandidato == 4): continue

            tieneChoque = False
            if idCandidato in horarios_hormiga and modulos_clase and dia_num != -1:
                timeline_candidato = horarios_hormiga[idCandidato]
                inicio_clase = min(modulos_clase)
                fin_clase = max(modulos_clase)
                if np.any(timeline_candidato[dia_num, inicio_clase:fin_clase+1] > 0):
                    tieneChoque = True
            
            if not tieneChoque:
                candidatos_sin_choque.append(facilitador)

        if candidatos_sin_choque:
            return random.choice(candidatos_sin_choque).idFacilitador
        return None # Si todos los candidatos posibles generan choque, no se asigna a nadie.

    # Gira la ruleta para seleccionar un candidato basado en su atractivo.
    r = random.uniform(0.0, 1.0) * sumaAtractivos
    intervaloAcumulado = 0.0
    for idCandidato, valorAtractivo in atractivos.items():
        intervaloAcumulado += valorAtractivo
        if r <= intervaloAcumulado: return idCandidato
            
    return list(atractivos.keys())[-1]

def generarPoblacionInicial(och, gestorDatos):
    """
    Crea la población inicial de soluciones usando el algoritmo de
    Colonia de Hormigas.
    """
    poblacionTotal = []
    grupos = och.grupoHormigas if och.grupoHormigas > 0 else 1
    hormigasPorGrupo = och.numeroHormigas
    idHormigaGlobal = 1
    
    # --- Setup para optimización de chequeo de choques ---
    mapa_dias = {
        "lunes": 0, "martes": 1, "miercoles": 2, "miércoles": 2, 
        "jueves": 3, "viernes": 4, "sabado": 5, "sábado": 5, "domingo": 6
    }
    modulos_en_clases = [int(m.numeroModulo) for c in gestorDatos.listaClases for m in c.horarioDeClase.modulos]
    max_id_modulo = max(modulos_en_clases + [0])
    # --- Fin Setup ---

    # --- Ordenamiento Estratégico de Clases ---
    # Agrupa las clases por trayecto y, dentro de cada grupo, pospone los Sprints (tipo 5) al final.
    # Esta estrategia es superior a un simple ordenamiento global porque:
    # 1. Procesa todas las clases de un mismo trayecto de forma contigua.
    # 2. Permite que los facilitadores acumulen la "experiencia" necesaria (FR4) para un trayecto específico
    #    justo antes de que se intenten asignar los Sprints de ESE MISMO trayecto.
    # 3. Mejora la calidad de la solución inicial y acelera la convergencia.
    
    clases_por_trayecto = defaultdict(list)
    clases_sin_trayecto = []
    for clase in gestorDatos.listaClases:
        if clase.trayecto:
            clases_por_trayecto[clase.trayecto.idTrayecto].append(clase)
        else:
            clases_sin_trayecto.append(clase)

    clases_ordenadas = []
    for id_trayecto in sorted(clases_por_trayecto.keys()):
        clases_del_trayecto = clases_por_trayecto[id_trayecto]
        clases_del_trayecto_ordenadas = sorted(clases_del_trayecto, key=lambda c: c.tipoDeClase == 5)
        clases_ordenadas.extend(clases_del_trayecto_ordenadas)
    clases_ordenadas.extend(clases_sin_trayecto)

    for numGrupo in range(grupos):
        poblacionDelGrupo = []
        for _ in range(hormigasPorGrupo):
            hormiga = Hormiga(idHormiga=idHormigaGlobal, algoritmoOCH=och, poblacion=None)
            cromosomaActual = Cromosoma(idCromosoma=idHormigaGlobal, funcionAptitud=0.0, ordenCromosoma=idHormigaGlobal, poblacion=None)
            horarios_hormiga = {} # Timeline para esta hormiga/solución
            workload_hormiga = {} # Carga de trabajo (en bloques) para esta hormiga
            
            for clase in clases_ordenadas:
                genNuevo = Gen(idGen=clase.idClase, idFacilitador1=None, idFacilitador2=None, 
                               idFacilitadorComplementario=None, idProfesorEducacionEspecial=None, 
                               evaluar=True, cromosoma=cromosomaActual)
                cromosomaActual.agregarGen(genNuevo)

                def asignar_y_actualizar(rol):
                    """Función auxiliar para asignar un facilitador y actualizar su timeline."""
                    id_fac = _girarRuleta(och, gestorDatos, clase, horarios_hormiga, workload_hormiga, rol, mapa_dias)
                    if id_fac is not None:
                        if id_fac not in horarios_hormiga:
                            horarios_hormiga[id_fac] = np.zeros((7, max_id_modulo + 1), dtype=np.int8)
                        if id_fac not in workload_hormiga:
                            workload_hormiga[id_fac] = 0
                        
                        dia_num = mapa_dias.get(clase.horarioDeClase.dia.strip().lower(), -1)
                        if dia_num != -1:
                            modulos_clase = [m.numeroModulo for m in clase.horarioDeClase.modulos]
                            if modulos_clase:
                                workload_hormiga[id_fac] += len(modulos_clase)
                                inicio = min(modulos_clase)
                                fin = max(modulos_clase)
                                horarios_hormiga[id_fac][dia_num, inicio:fin+1] += 1
                    return id_fac

                genNuevo.idFacilitador1 = asignar_y_actualizar("F1")
                genNuevo.idFacilitador2 = asignar_y_actualizar("F2")
                genNuevo.idFacilitadorComplementario = asignar_y_actualizar("FC")

                # Solo se asigna PEE si la clase es de tipo 2 o 4, que son las que lo requieren.
                if clase.tipoDeClase == 2 or clase.tipoDeClase == 4:
                    genNuevo.idProfesorEducacionEspecial = asignar_y_actualizar("PEE")
            
            poblacionDelGrupo.append(cromosomaActual)
            idHormigaGlobal += 1
            
        poblacionTotal.extend(poblacionDelGrupo)
        
    return poblacionTotal

# =========================================================================
# FASE 2: ADAPTACIÓN Y TRANSFORMACIÓN A MODELO MATRICIAL (NUMPY)
# =========================================================================

def inicializarEntornoMatricial(gestorDatos):
    """
    Convierte los datos de objetos a matrices y vectores de NumPy para un
    cálculo más rápido y eficiente durante la evaluación de restricciones.
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
    
    # --- Cálculo de dimensiones para las matrices ---
    # 1. ID máximo de trayectos
    max_id_trayecto = max([int(t.idTrayecto) for t in gestorDatos.listaTrayectos] + [0])
    
    # 2. ID máximo de módulos horarios
    modulos_en_clases = [int(m.numeroModulo) for c in gestorDatos.listaClases for m in c.horarioDeClase.modulos]
    modulos_en_disp = [int(m.numeroModulo) for f in gestorDatos.listaFacilitadores for d in f.disponibilidadesHorarias for m in d.modulos]
    max_id_modulo = max(modulos_en_clases + modulos_en_disp + [0])
    
    # 3. Mapeo de trayectos a "familias" por nombre, para agrupar niveles (Básico/Avanzado).
    trayecto_nombres = sorted(list(set([t.nombre for t in gestorDatos.listaTrayectos])))
    mapa_nombre_a_familia_id = {nombre: i for i, nombre in enumerate(trayecto_nombres)}
    max_id_familia = len(trayecto_nombres)
    vector_trayecto_familia = np.zeros(max_id_trayecto + 1, dtype=int)
    for trayecto in gestorDatos.listaTrayectos:
        id_t = int(trayecto.idTrayecto)
        familia_id = mapa_nombre_a_familia_id[trayecto.nombre]
        if id_t < len(vector_trayecto_familia):
            vector_trayecto_familia[id_t] = familia_id

    # 4. Vector para mapear ID de trayecto a su tipo (1: Tradicional, 2: Propuesta)
    vector_tipo_trayecto = np.zeros(max_id_trayecto + 1, dtype=int)
    for trayecto in gestorDatos.listaTrayectos:
        id_t = int(trayecto.idTrayecto)
        tipo_t = int(trayecto.tipoTrayecto.idTipo)
        if id_t < len(vector_tipo_trayecto):
            vector_tipo_trayecto[id_t] = tipo_t
            
    # Inicialización de matrices con las dimensiones calculadas.
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
        "perfil_fac": vector_perfil_fac,
        "tipo_trayecto": vector_tipo_trayecto,
        "trayecto_familia": vector_trayecto_familia,
        "max_id_familia": max_id_familia
    }
    return datos_numpy

def codificarPoblacionMatricial(poblacion_objetos, datos_numpy):
    """
    Convierte la población (lista de objetos Cromosoma) a un tensor 3D de NumPy
    para procesarlo eficientemente. Dimensiones: [Individuos, Clases, Roles].
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
    Convierte la mejor solución (matriz de NumPy) de vuelta a un objeto
    Cromosoma para poder interpretar y guardar el resultado.
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
    Calcula la aptitud (fitness) de una solución. Una aptitud más alta es mejor.
    Se basa en la suma de todas las penalizaciones de las restricciones.
    Fórmula: Aptitud = 1 / (1 + Suma de Penalizaciones)
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
    Selecciona los individuos para la siguiente generación usando una combinación
    de Elitismo, Torneo y Ruleta.
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

def operadorCruza(poblacion_intermedia, cantidad_elite, puntos_cruza):
    """
    Realiza el cruce entre padres para generar nuevos individuos (hijos),
    combinando partes de sus cromosomas.
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
        
        # Se asume que la cruza siempre ocurre para cada pareja de padres.
        num_cortes = min(puntos_cruza, num_clases - 1)
        
        hijo1 = poblacion_intermedia[idx_p1].copy()
        hijo2 = poblacion_intermedia[idx_p2].copy()

        # La lógica actual de cruce requiere al menos 2 puntos para funcionar.
        if num_cortes >= 2:
            cortes = sorted(random.sample(range(1, num_clases), num_cortes))
            hijo1[cortes[0]:cortes[1]] = poblacion_intermedia[idx_p2, cortes[0]:cortes[1]]
            hijo2[cortes[0]:cortes[1]] = poblacion_intermedia[idx_p1, cortes[0]:cortes[1]]
            
            if len(cortes) > 2:
                hijo1[cortes[2]:] = poblacion_intermedia[idx_p2, cortes[2]:]
                hijo2[cortes[2]:] = poblacion_intermedia[idx_p1, cortes[2]:]
        
        poblacion_cruzada[cantidad_elite + i] = hijo1
        poblacion_cruzada[cantidad_elite + i + 1] = hijo2
            
    return poblacion_cruzada

def operadorMutacion(poblacion_cruzada, datos_numpy, cantidad_elite, prob_mutacion=0.02, probs_mutacion=None):
    """
    Introduce cambios aleatorios (mutaciones) en los individuos para mantener
    la diversidad en la población y evitar estancamiento.
    """
    num_individuos, num_clases, num_roles = poblacion_cruzada.shape
    
    # Extracción de datos para validaciones
    matriz_es_pee = datos_numpy["es_pee"]
    matriz_clases_req = datos_numpy["clases_req"]
    matriz_disp_horaria = datos_numpy["disp_horaria"]
    matriz_conocimiento_trayecto = datos_numpy["conocimiento_trayecto"]
    vector_horas_max = datos_numpy["horas_max"]
    duraciones = matriz_clases_req[:, 2] - matriz_clases_req[:, 1] + 1
    
    ids_regulares = np.where(matriz_es_pee == 0)[0]
    ids_pee = np.where(matriz_es_pee == 1)[0]
    
    mascara_mutacion = np.random.random((num_individuos - cantidad_elite, num_clases)) < prob_mutacion
    
    for idx_indiv_relativo in range(num_individuos - cantidad_elite):
        idx_real = cantidad_elite + idx_indiv_relativo
        clases_a_mutar = np.where(mascara_mutacion[idx_indiv_relativo])[0]
        
        # Si hay clases para mutar en este individuo, pre-calculamos su carga horaria
        if len(clases_a_mutar) > 0:
            cromosoma_actual = poblacion_cruzada[idx_real]
            workload_actual = np.bincount(
                cromosoma_actual[cromosoma_actual != -1],
                weights=np.broadcast_to(duraciones[:, np.newaxis], cromosoma_actual.shape)[cromosoma_actual != -1],
                minlength=len(vector_horas_max)
            )

        for clase_idx in clases_a_mutar:
            roles_activos = np.where(poblacion_cruzada[idx_real, clase_idx] != -1)[0]
            if len(roles_activos) == 0: continue
            
            # Selección del rol a mutar
            if probs_mutacion is not None:
                probs_activos = [probs_mutacion[r] for r in roles_activos]
                suma_probs = sum(probs_activos)
                rol_a_mutar = np.random.choice(roles_activos, p=[p / suma_probs for p in probs_activos]) if suma_probs > 0 else np.random.choice(roles_activos)
            else:
                rol_a_mutar = np.random.choice(roles_activos)
            
            # --- Mutación Inteligente: busca un reemplazo válido ---
            original_fac_idx = poblacion_cruzada[idx_real, clase_idx, rol_a_mutar]
            candidate_pool = ids_pee if rol_a_mutar == 3 else ids_regulares
            if len(candidate_pool) == 0: continue

            clase_dia, clase_inicio, clase_fin, clase_trayecto = matriz_clases_req[clase_idx]
            clase_duracion = duraciones[clase_idx]
            valid_candidates = []

            for cand_idx in candidate_pool:
                if cand_idx == original_fac_idx: continue

                # FR8: Competencia
                if clase_trayecto != -1 and matriz_conocimiento_trayecto[cand_idx, clase_trayecto] == 0: continue
                # FR2: Disponibilidad
                if np.sum(matriz_disp_horaria[cand_idx, clase_dia, clase_inicio:clase_fin+1]) < clase_duracion: continue
                # FR3: Horas máximas
                max_modulos_contrato = vector_horas_max[cand_idx] * 4
                if max_modulos_contrato > 0 and (workload_actual[cand_idx] + clase_duracion) > max_modulos_contrato: continue
                

                # FR1: Choque de horario
                tiene_choque = False
                otras_clases_mask = np.any(cromosoma_actual == cand_idx, axis=1)
                otras_clases_mask[clase_idx] = False
                for otra_clase_idx in np.where(otras_clases_mask)[0]:
                    if matriz_clases_req[otra_clase_idx, 0] == clase_dia and \
                       matriz_clases_req[otra_clase_idx, 1] <= clase_fin and \
                       matriz_clases_req[otra_clase_idx, 2] >= clase_inicio:
                        tiene_choque = True
                        break
                if tiene_choque: continue
                
                # Verificación adicional: Evitar duplicados en la misma clase.
                if cand_idx in cromosoma_actual[clase_idx]:
                    continue

                valid_candidates.append(cand_idx)

            if valid_candidates:
                # La lista de candidatos ya está filtrada, por lo que se elige uno al azar.
                nuevo_fac_idx = np.random.choice(valid_candidates)

                poblacion_cruzada[idx_real, clase_idx, rol_a_mutar] = nuevo_fac_idx
                
                # Actualización de la carga para la siguiente mutación en el mismo individuo
                workload_actual[nuevo_fac_idx] += clase_duracion
                if original_fac_idx != -1:
                    workload_actual[original_fac_idx] -= clase_duracion
            # --- Fin de Mutación Inteligente ---
                    
    return poblacion_cruzada

# =========================================================================
# FASE 4: ORQUESTACIÓN PRINCIPAL DEL ALGORITMO GENÉTICO
# =========================================================================

def algoritmoAG(configAG):
    """
    Prepara las variables para registrar el progreso del algoritmo genético.
    """
    configAG.historial_maximos = []
    configAG.historial_promedios = []
    configAG.generacion_actual = 0
    configAG.tiempo_inicio = time.time()
    configAG.tiempo_ejecucion_final = 0.0

def ejecutarCicloGenetico(poblacion_objetos, configAG, gestorDatos, log_file=None):
    """
    Orquesta el ciclo principal del algoritmo genético: evalúa, selecciona,
    cruza y muta la población a lo largo de las generaciones.
    """
    print("[SISTEMA] Inicializando entorno matricial de validación de restricciones.")
    datos_numpy = inicializarEntornoMatricial(gestorDatos)
    
    print("[SISTEMA] Transformando población inicial al modelo tensorial.")
    tensor_poblacion = codificarPoblacionMatricial(poblacion_objetos, datos_numpy)
    
    num_individuos = tensor_poblacion.shape[0]
    aptitudes = np.zeros(num_individuos)
    
    for i in range(num_individuos):
        aptitudes[i] = evaluarFuncionAptitud(tensor_poblacion[i], datos_numpy)
        
    configAG.historial_maximos.append(np.max(aptitudes))
    configAG.historial_promedios.append(np.mean(aptitudes))

    elitismo = configAG.seleccionElitista
    cantidad_elite = max(1, int(num_individuos * elitismo))

    print("[SISTEMA] Iniciando ciclo evolutivo del Algoritmo Genético.")

    while True:
        # Verificación de criterios de convergencia y parada
        if configAG.generacion_actual >= configAG.numeroGeneraciones:
            print(f"[SISTEMA] Criterio de parada alcanzado: Límite de iteraciones ({configAG.numeroGeneraciones}).")
            break
            
        tiempo_transcurrido_minutos = (time.time() - configAG.tiempo_inicio) / 60.0
        if tiempo_transcurrido_minutos >= configAG.minutosEjecucion:
            print(f"[SISTEMA] Criterio de parada alcanzado: Límite temporal ({configAG.minutosEjecucion} min).")
            break
            
        if np.max(aptitudes) >= 1.0:
            print("[SISTEMA] Convergencia absoluta: Solución óptima global alcanzada (Aptitud = 1.0).")
            break
            
        # Aplicación de operadores genéticos matriciales
        pob_intermedia = operadorSeleccion(tensor_poblacion, aptitudes, elitismo, 
                                           configAG.seleccionTorneo, configAG.seleccionRuleta)
        
        pob_cruzada = operadorCruza(pob_intermedia, cantidad_elite, puntos_cruza=configAG.puntosCruza)
        
        probs_roles = [
            configAG.probMutacionF1,
            configAG.probMutacionF2,
            configAG.probMutacionFC,
            configAG.probMutacionPEE
        ]
        tensor_poblacion = operadorMutacion(pob_cruzada, datos_numpy, cantidad_elite,
                                            prob_mutacion=configAG.probGeneralMutacion,
                                            probs_mutacion=probs_roles)
        
        # Evaluación de la descendencia
        for i in range(num_individuos):
            aptitudes[i] = evaluarFuncionAptitud(tensor_poblacion[i], datos_numpy)
            
        # Registro de métricas poblacionales
        configAG.generacion_actual += 1
        configAG.historial_maximos.append(np.max(aptitudes))
        configAG.historial_promedios.append(np.mean(aptitudes))

    configAG.tiempo_ejecucion_final = time.time() - configAG.tiempo_inicio
    
    print("[SISTEMA] Evolución finalizada. Decodificando cromosoma óptimo.")
    idx_mejor = np.argmax(aptitudes)
    matriz_campeona = tensor_poblacion[idx_mejor]
    
    # --- CÁLCULO CONSOLIDADO DE RESTRICCIONES ---
    v_fr1 = FR1(matriz_campeona, datos_numpy)
    v_fr2 = FR2(matriz_campeona, datos_numpy)
    v_fr3 = FR3(matriz_campeona, datos_numpy)
    v_fr4 = FR4(matriz_campeona, datos_numpy)
    v_fr5 = FR5(matriz_campeona, datos_numpy)
    v_fr6 = FR6(matriz_campeona, datos_numpy)
    v_fr7 = FR7(matriz_campeona, datos_numpy)
    v_fr8 = FR8(matriz_campeona, datos_numpy)

    # --- REPORTE DE PENALIZACIONES DE LA MEJOR SOLUCIÓN ---
    print("\n==================================================")
    print("[SISTEMA] Desglose de penalizaciones del cromosoma campeón:")
    print(f" - FR1 (Choques de horario)        : {v_fr1}")
    print(f" - FR2 (Disponibilidad horaria)    : {v_fr2}")
    print(f" - FR3 (Horas semanales)           : {v_fr3}")
    print(f" - FR4 (Liderazgo en Sprints)      : {v_fr4}")
    print(f" - FR5 (Límite de Sprints)         : {v_fr5}")
    print(f" - FR6 (PEE obligatorio)           : {v_fr6}")
    print(f" - FR7 (Compatibilidad de parejas) : {v_fr7}")
    print(f" - FR8 (Competencia en trayecto)   : {v_fr8}")
    print("==================================================\n")

    # --- PERSISTENCIA DE RESULTADOS FINALES EN ARCHIVO DE REGISTRO ---
    if log_file:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write("\n==================================================\n")
            f.write("RESULTADOS FINALES DE LA EJECUCIÓN\n")
            f.write("==================================================\n")
            f.write(f"Tiempo total de ejecución : {configAG.tiempo_ejecucion_final:.2f} segundos\n")
            f.write(f"Aptitud de la mejor solución: {aptitudes[idx_mejor]:.4f}\n\n")
            f.write("--- DESGLOSE DE PENALIZACIONES ---\n")
            f.write(f" - FR1 (Choques de horario)        : {v_fr1}\n")
            f.write(f" - FR2 (Disponibilidad horaria)    : {v_fr2}\n")
            f.write(f" - FR3 (Horas semanales)           : {v_fr3}\n")
            f.write(f" - FR4 (Liderazgo en Sprints)      : {v_fr4}\n")
            f.write(f" - FR5 (Límite de Sprints)         : {v_fr5}\n")
            f.write(f" - FR6 (PEE obligatorio)           : {v_fr6}\n")
            f.write(f" - FR7 (Compatibilidad de parejas) : {v_fr7}\n")
            f.write(f" - FR8 (Competencia en trayecto)   : {v_fr8}\n")
            f.write("==================================================\n\n")
            f.write("--- EVOLUCIÓN DE LA POBLACIÓN POR GENERACIÓN ---\n")
            f.write("Generación | Aptitud Máxima | Aptitud Promedio\n")
            f.write("----------------------------------------------\n")
            for i in range(len(configAG.historial_maximos)):
                max_apt = configAG.historial_maximos[i]
                avg_apt = configAG.historial_promedios[i]
                f.write(f"{i:<10} | {max_apt:<14.4f} | {avg_apt:<16.4f}\n")
            f.write("==================================================\n")

    modelo_cromosoma = poblacion_objetos[0]
    cromosoma_ganador = decodificarCromosomaOptimo(matriz_campeona, modelo_cromosoma, datos_numpy)
    cromosoma_ganador.funcionAptitud = aptitudes[idx_mejor]
    
    return [cromosoma_ganador]