import numpy as np

def FR1(cromosoma, gestorDatos):
    """
    Restricción 1 (R1): Choques de horario.
    Verifica que un facilitador no tenga superposición de módulos el mismo día.
    """
    conflictos = 0
    dias = gestorDatos["clases_req"][:, 0]
    inicios = gestorDatos["clases_req"][:, 1]
    fines = gestorDatos["clases_req"][:, 2]
    
    # Obtenemos todos los facilitadores asignados en la planilla, ignorando los espacios vacíos (-1)
    facilitadores_unicos = np.unique(cromosoma)
    facilitadores_unicos = facilitadores_unicos[facilitadores_unicos != -1]
    
    for id_fac in facilitadores_unicos:
        # Buscamos todas las clases donde participa este facilitador
        mascara_clases = np.any(cromosoma == id_fac, axis=1)
        clases_asignadas = np.where(mascara_clases)[0]
        
        # Si tiene más de una clase, comprobamos si chocan
        if len(clases_asignadas) > 1:
            for i in range(len(clases_asignadas) - 1):
                for j in range(i + 1, len(clases_asignadas)):
                    c1 = clases_asignadas[i]
                    c2 = clases_asignadas[j]
                    
                    # Si caen el mismo día, verificamos si los bloques se pisan
                    if dias[c1] == dias[c2]:
                        if inicios[c1] <= fines[c2] and fines[c1] >= inicios[c2]:
                            conflictos += 1
                            
    return conflictos


def FR2(cromosoma, gestorDatos):
    """
    Restricción 2 (R2): Respetar disponibilidad horaria contractual.
    Compara los módulos de la clase asignada con la matriz tridimensional de disponibilidad.
    """
    conflictos = 0
    matriz_clases_req = gestorDatos["clases_req"]
    matriz_disp_horaria = gestorDatos["disp_horaria"]
    
    # Evaluamos los 4 roles posibles (F1, F2, FC, PEE)
    for rol in range(4):
        ids_asignados = cromosoma[:, rol]
        clases_activas = np.where(ids_asignados != -1)[0]
        
        for clase_idx in clases_activas:
            id_fac = ids_asignados[clase_idx]
            dia = matriz_clases_req[clase_idx, 0]
            inicio = matriz_clases_req[clase_idx, 1]
            fin = matriz_clases_req[clase_idx, 2]
            
            # Calculamos cuántos bloques dura la clase y cuántos tiene disponibles el profe
            bloques_necesarios = fin - inicio + 1
            bloques_disponibles = np.sum(matriz_disp_horaria[id_fac, dia, inicio:fin+1])
            
            # Si no le alcanzan los bloques disponibles, se cuenta como conflicto
            if bloques_disponibles < bloques_necesarios:
                conflictos += 1
                
    return conflictos


def FR3(cromosoma, gestorDatos):
    """
    Restricción 3 (R3): Horas contractuales por semana (Máximo y Mínimo 80%).
    Suma las horas totales de cada facilitador y las contrasta con su contrato.
    """
    matriz_clases_req = gestorDatos["clases_req"]
    vector_horas_max = gestorDatos["horas_max"]
    vector_es_pee = gestorDatos["es_pee"]
    
    # Calculamos la duración en bloques de todas las clases
    duraciones = matriz_clases_req[:, 2] - matriz_clases_req[:, 1] + 1
    max_id_fac = len(vector_horas_max)
    bloques_acumulados = np.zeros(max_id_fac, dtype=int)
    
    for rol in range(4):
        ids_asignados = cromosoma[:, rol]
        mascara_validos = ids_asignados != -1
        
        pesos = duraciones[mascara_validos]
        indices = ids_asignados[mascara_validos]
        
        if len(indices) > 0:
            # Sumamos de forma agrupada los bloques correspondientes a cada ID
            acumulado_parcial = np.bincount(indices, weights=pesos, minlength=max_id_fac)
            bloques_acumulados += acumulado_parcial.astype(int)
            
    # Pasamos los bloques a horas reloj (1 bloque = 15 min -> 4 bloques = 1 hr)
    horas_trabajadas = bloques_acumulados / 4.0
    limite_min = vector_horas_max * 0.80
    
    # Verificamos si se pasaron del máximo
    infraccion_max = horas_trabajadas > vector_horas_max
    # Verificamos si no llegan al mínimo (excluyendo a los de Educación Especial)
    infraccion_min = (horas_trabajadas < limite_min) & (vector_es_pee == 0) & (vector_horas_max > 0)
    
    conflictos = np.sum(infraccion_max) + np.sum(infraccion_min)
    return conflictos


def FR4(cromosoma, gestorDatos):
    """
    Restricción 4 (R4): Facilitadores de Sprints (TC=5) deben liderar el trayecto.
    Calcula si el profe tiene más del 50% de las horas totales de ese trayecto.
    """
    conflictos = 0
    matriz_clases_req = gestorDatos["clases_req"]
    vector_tipo_clase = gestorDatos["tipo_clase"]
    
    duraciones = matriz_clases_req[:, 2] - matriz_clases_req[:, 1] + 1
    trayectos = matriz_clases_req[:, 3]
    
    # Buscamos qué clases son Sprints de planificación
    sprints = np.where(vector_tipo_clase == 5)[0]
    if len(sprints) == 0:
        return 0
        
    for clase_sprint in sprints:
        id_trayecto = trayectos[clase_sprint]
        if id_trayecto == -1: continue
        
        # Filtramos todas las clases regulares de este trayecto específico
        mascara_trayecto = (trayectos == id_trayecto) & (vector_tipo_clase != 5)
        bloques_totales_trayecto = np.sum(duraciones[mascara_trayecto])
        mitad_requerida = bloques_totales_trayecto / 2.0
        
        # Vemos quiénes están asignados a este sprint
        roles_sprint = cromosoma[clase_sprint, 0:3]
        roles_sprint = roles_sprint[roles_sprint != -1]
        
        for id_fac in roles_sprint:
            # Verificamos cuántas horas regulares dio este profesor en el trayecto
            mascara_fac = (cromosoma[:, 0] == id_fac) | (cromosoma[:, 1] == id_fac) | (cromosoma[:, 2] == id_fac)
            bloques_docente = np.sum(duraciones[mascara_trayecto & mascara_fac])
            
            if bloques_docente < mitad_requerida:
                conflictos += 1
                
    return conflictos


def FR5(cromosoma, gestorDatos):
    """
    Restricción 5 (R5): Un facilitador no puede estar en más de 3 Sprints.
    """
    conflictos = 0
    vector_tipo_clase = gestorDatos["tipo_clase"]
    
    sprints = np.where(vector_tipo_clase == 5)[0]
    if len(sprints) == 0:
        return 0
        
    # Extraemos a todos los asignados en las clases tipo Sprint
    ids_en_sprints = cromosoma[sprints, 0:3].flatten()
    ids_en_sprints = ids_en_sprints[ids_en_sprints != -1]
    
    if len(ids_en_sprints) > 0:
        # Contamos cuántas veces aparece cada ID
        conteos = np.bincount(ids_en_sprints)
        conflictos = np.sum(conteos > 3)
        
    return conflictos


def FR6(cromosoma, gestorDatos):
    """
    Restricción 6 (R6): PEE obligatorio en clases integradas (Tipo 3 y 4).
    """
    vector_tipo_clase = gestorDatos["tipo_clase"]
    
    necesita_pee = (vector_tipo_clase == 3) | (vector_tipo_clase == 4)
    asignaciones_pee = cromosoma[:, 3] # La columna 3 corresponde al rol PEE
    
    # Buscamos dónde necesita PEE y el valor está vacío (-1)
    infracciones = necesita_pee & (asignaciones_pee == -1)
    
    return np.sum(infracciones)


def FR7(cromosoma, gestorDatos):
    """
    Restricción 7 (R7): Compatibilidad de parejas docentes (Técnico/Pedagógico).
    Evita que dos perfiles del mismo tipo se asignen juntos cuando no corresponde.
    """
    conflictos = 0
    vector_tipo_clase = gestorDatos["tipo_clase"]
    vector_perfil_fac = gestorDatos["perfil_fac"]
    
    ids_f1 = cromosoma[:, 0]
    ids_f2 = cromosoma[:, 1]
    
    # Solo analizamos las clases que tienen los dos facilitadores asignados
    ambos_asignados = (ids_f1 != -1) & (ids_f2 != -1)
    
    for idx in np.where(ambos_asignados)[0]:
        tc = vector_tipo_clase[idx]
        perfil1 = vector_perfil_fac[ids_f1[idx]]
        perfil2 = vector_perfil_fac[ids_f2[idx]]
        
        # Condición: Grupos de menores (1, 3) no pueden tener dos técnicos (1)
        if (tc == 1 or tc == 3) and perfil1 == 1 and perfil2 == 1:
            conflictos += 1
        # Condición: Grupos de mayores (2, 4) no pueden tener dos pedagógicos (2)
        elif (tc == 2 or tc == 4) and perfil1 == 2 and perfil2 == 2:
            conflictos += 1
            
    return conflictos


def FR8(cromosoma, gestorDatos):
    """
    Restricción 8 (R8): Competencia del facilitador en el trayecto asignado.
    Cruza los IDs de los asignados con la matriz de conocimientos.
    """
    conflictos = 0
    matriz_clases_req = gestorDatos["clases_req"]
    matriz_conocimiento_trayecto = gestorDatos["conocimiento_trayecto"]
    
    trayectos_clases = matriz_clases_req[:, 3]
    
    # Recorremos cada uno de los roles para verificar si saben el trayecto
    for rol in range(4):
        ids_asignados = cromosoma[:, rol]
        
        mascara_validos = (ids_asignados != -1) & (trayectos_clases != -1)
        clases_a_evaluar = np.where(mascara_validos)[0]
        
        if len(clases_a_evaluar) > 0:
            facs = ids_asignados[clases_a_evaluar]
            trays = trayectos_clases[clases_a_evaluar]
            
            # Comprobamos en la matriz si el cruce Facilitador-Trayecto es 0 (no sabe)
            conocimientos = matriz_conocimiento_trayecto[facs, trays]
            conflictos += np.sum(conocimientos == 0)
            
    return conflictos