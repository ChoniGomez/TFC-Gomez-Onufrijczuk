import numpy as np

def FR1(cromosoma, gestorDatos):
    """
    Restricción 1 (R1): Choques de horario.
    Verifica que un facilitador no tenga clases en el mismo horario. Usa una 'timeline' para ser más eficiente.
    """
    conflictos = 0
    dias = gestorDatos["clases_req"][:, 0]
    inicios = gestorDatos["clases_req"][:, 1]
    fines = gestorDatos["clases_req"][:, 2]
    num_modulos = gestorDatos["disp_horaria"].shape[2]
    
    facilitadores_unicos = np.unique(cromosoma)
    facilitadores_unicos = facilitadores_unicos[facilitadores_unicos != -1]
    
    for id_fac in facilitadores_unicos:
        # Timeline: 7 días, N módulos por día.
        timeline_facilitador = np.zeros((7, num_modulos), dtype=np.int16)
        
        mascara_clases = np.any(cromosoma == id_fac, axis=1)
        clases_asignadas = np.where(mascara_clases)[0]
        
        for clase_idx in clases_asignadas:
            dia_clase = dias[clase_idx]
            inicio_clase = inicios[clase_idx]
            fin_clase = fines[clase_idx]
            # Se marca el rango de módulos como ocupado en el día correspondiente.
            timeline_facilitador[dia_clase, inicio_clase:fin_clase+1] += 1
            
        # Se cuentan los conflictos: cualquier módulo con valor > 1 indica un solapamiento.
        # La penalización es la suma de los solapamientos (valor - 1).
        conflictos += np.sum(np.maximum(0, timeline_facilitador - 1))

    return conflictos


def FR2(cromosoma, gestorDatos):
    """
    Restricción 2 (R2): Respetar disponibilidad horaria contractual.
    Verifica que la clase asignada esté dentro de la disponibilidad horaria del facilitador.
    """
    conflictos = 0
    matriz_disp_horaria = gestorDatos["disp_horaria"]
    matriz_clases_req = gestorDatos["clases_req"]
    
    # Crear una matriz de requerimientos de módulos
    matriz_requerimientos = np.zeros_like(matriz_disp_horaria, dtype=np.int8)
    
    # Encontrar todas las asignaciones activas
    clases_indices, _ = np.where(cromosoma != -1)
    if len(clases_indices) == 0:
        return 0
        
    # Obtener los datos de todas las asignaciones activas de una vez
    facilitadores_indices = cromosoma[cromosoma != -1]
    dias_clases = matriz_clases_req[clases_indices, 0]
    inicios_clases = matriz_clases_req[clases_indices, 1]
    fines_clases = matriz_clases_req[clases_indices, 2]

    # Marcar todos los módulos requeridos en una sola pasada
    for i in range(len(facilitadores_indices)):
        matriz_requerimientos[facilitadores_indices[i], dias_clases[i], inicios_clases[i]:fines_clases[i]+1] = 1
    
    # Un módulo es un conflicto si es requerido (1) pero no está disponible (0)
    conflictos_matriz = (matriz_requerimientos == 1) & (matriz_disp_horaria == 0)
    conflictos = np.sum(conflictos_matriz)
                
    return int(conflictos)


def FR3(cromosoma, gestorDatos):
    """
    Restricción 3 (R3): Horas semanales (Máximo).
    Verifica que los facilitadores no excedan su máximo de horas por contrato.
    """
    matriz_clases_req = gestorDatos["clases_req"]
    vector_horas_max = gestorDatos["horas_max"]

    # Determinación de la duración absoluta en módulos de la totalidad de clases requeridas.
    duraciones = matriz_clases_req[:, 2] - matriz_clases_req[:, 1] + 1
    max_id_fac = len(vector_horas_max)

    # Crear una matriz de pesos (duraciones) con la misma forma que el cromosoma
    pesos_matriz = np.broadcast_to(duraciones[:, np.newaxis], cromosoma.shape)

    # Aplanar el cromosoma y los pesos para bincount
    ids_asignados = cromosoma.flatten()
    pesos = pesos_matriz.flatten()
    mascara_validos = ids_asignados != -1

    # Usar bincount una sola vez para sumar todos los bloques por facilitador
    if np.any(mascara_validos):
        bloques_acumulados = np.bincount(ids_asignados[mascara_validos], weights=pesos[mascara_validos], minlength=max_id_fac)
    else:
        bloques_acumulados = np.zeros(max_id_fac, dtype=float)
            
    # Conversión dimensional de módulos a la unidad de horas estándar (Factor 4:1).
    horas_trabajadas = bloques_acumulados / 4.0
    
    # Cuantificación del NÚMERO de facilitadores en conflicto, no la suma de horas.

    # Facilitadores que trabajan más de sus horas de contrato.
    # Si el contrato es 0, cualquier hora trabajada es un exceso.
    facilitadores_excedidos = horas_trabajadas > vector_horas_max

    # La penalización es la cantidad de facilitadores que exceden su máximo.
    conflictos = np.sum(facilitadores_excedidos)

    return int(conflictos)


def FR4(cromosoma, gestorDatos):
    """
    Restricción 4 (R4): Liderazgo en Sprints.
    Verifica la experiencia requerida para liderar Sprints.
    Penaliza con 1 por cada asignación a un Sprint que no cumpla el requisito.
    """
    vector_tipo_clase = gestorDatos["tipo_clase"]
    matriz_clases_req = gestorDatos["clases_req"]
    vector_tipo_trayecto = gestorDatos["tipo_trayecto"]
    vector_trayecto_familia = gestorDatos["trayecto_familia"]
    max_id_familia = gestorDatos["max_id_familia"]
    
    trayectos = matriz_clases_req[:, 3]
    num_fac = len(gestorDatos["horas_max"])

    # Paso 1: Contar participaciones en clases regulares por facilitador y FAMILIA de trayecto.
    # La experiencia se agrupa por el nombre del trayecto (ej. 'tecnokids'), sin importar
    # el nivel (Básico/Avanzado), lo que permite que la experiencia en un nivel
    # sea válida para un SPRINT de otro nivel dentro de la misma familia.
    participaciones = np.zeros((num_fac, max_id_familia), dtype=int)
    
    mascara_regulares = (vector_tipo_clase != 5) & (trayectos != -1)
    clases_regulares_idx = np.where(mascara_regulares)[0]
    
    if len(clases_regulares_idx) > 0:
        # Para cada clase regular, obtener los facilitadores únicos y el trayecto.
        for clase_idx in clases_regulares_idx:
            facs_en_clase = np.unique(cromosoma[clase_idx, 0:3])
            facs_en_clase = facs_en_clase[facs_en_clase != -1]
            trayecto_clase_id = trayectos[clase_idx]
            
            if len(facs_en_clase) > 0 and trayecto_clase_id != -1:
                familia_id = vector_trayecto_familia[trayecto_clase_id]
                participaciones[facs_en_clase, familia_id] += 1

    # Paso 2: Verificar los Sprints.
    conflictos = 0
    sprints_idx = np.where(vector_tipo_clase == 5)[0]
    if len(sprints_idx) == 0: return 0

    # Iterar sobre cada asignación a un Sprint
    for clase_idx in sprints_idx:
        # Contador de fallos local para este Sprint específico.
        fallos_en_sprint_actual = 0

        trayecto_sprint_id = trayectos[clase_idx]
        if trayecto_sprint_id == -1: continue

        tipo_trayecto_sprint = vector_tipo_trayecto[trayecto_sprint_id]
        
        # Definir el requisito de participación basado en el tipo de trayecto
        requisito = 3 if tipo_trayecto_sprint == 1 else (1 if tipo_trayecto_sprint == 2 else 0)
        if requisito == 0: continue

        familia_sprint_id = vector_trayecto_familia[trayecto_sprint_id]

        # Obtener los facilitadores asignados al Sprint (F1, F2, FC)
        facs_en_sprint = cromosoma[clase_idx, 0:3]
        facs_en_sprint = facs_en_sprint[facs_en_sprint != -1]

        for fac_idx in facs_en_sprint:
            # Verificar si el facilitador cumple el requisito para la FAMILIA del trayecto.
            if participaciones[fac_idx, familia_sprint_id] < requisito:
                fallos_en_sprint_actual += 1
        
        # Nueva regla: Un Sprint tiene un conflicto solo si MÁS DE UN facilitador no cumple.
        if fallos_en_sprint_actual > 1:
            conflictos += 1
                
    return int(conflictos)


def FR5(cromosoma, gestorDatos):
    """
    Restricción 5 (R5): Límite de Sprints. Un facilitador no puede estar en más de 3.
    """
    conflictos = 0
    vector_tipo_clase = gestorDatos["tipo_clase"]
    
    sprints = np.where(vector_tipo_clase == 5)[0]
    if len(sprints) == 0:
        return 0
        
    # Consolidación de participaciones docentes en los Sprints programados.
    ids_en_sprints = cromosoma[sprints, 0:3].flatten()
    ids_en_sprints = ids_en_sprints[ids_en_sprints != -1]
    
    if len(ids_en_sprints) > 0:
        # Agrupación y conteo de incidencias mediante procesamiento matricial.
        conteos = np.bincount(ids_en_sprints)
        # Penalidad escalonada para excedentes por encima del límite regulatorio (3 Sprints).
        conflictos = np.sum(np.maximum(0, conteos - 3))
        
    return conflictos


def FR6(cromosoma, gestorDatos):
    """
    Restricción 6 (R6): PEE obligatorio. Verifica que las clases que lo requieren tengan un PEE.
    """
    vector_tipo_clase = gestorDatos["tipo_clase"]
    
    necesita_pee = (vector_tipo_clase == 2) | (vector_tipo_clase == 4)
    asignaciones_pee = cromosoma[:, 3] # La columna 3 corresponde al rol PEE
    
    # Evaluación lógica: Verificación de carencia (-1) sobre clases que exigen PEE obligatoriamente.
    infracciones = necesita_pee & (asignaciones_pee == -1)
    
    return np.sum(infracciones)


def FR7(cromosoma, gestorDatos):
    """
    Restricción 7 (R7): Compatibilidad de parejas docentes (Técnico/Pedagógico).
    Verifica la compatibilidad de los perfiles en las parejas docentes.
    """
    conflictos = 0
    vector_tipo_clase = gestorDatos["tipo_clase"]
    vector_perfil_fac = gestorDatos["perfil_fac"]
    
    ids_f1 = cromosoma[:, 0]
    ids_f2 = cromosoma[:, 1]
    
    # Encontrar los índices de clases donde ambos F1 y F2 están asignados
    ambos_asignados_idx = np.where((ids_f1 != -1) & (ids_f2 != -1))[0]
    
    if len(ambos_asignados_idx) == 0:
        return 0
        
    # Obtener los datos relevantes para esas clases usando los índices
    clases_con_pareja_tc = vector_tipo_clase[ambos_asignados_idx]
    perfiles1 = vector_perfil_fac[ids_f1[ambos_asignados_idx]]
    perfiles2 = vector_perfil_fac[ids_f2[ambos_asignados_idx]]
    
    # Condición A: Clases tipo 1 o 3 no pueden tener dos técnicos (perfil 1)
    conflictos_a = ((clases_con_pareja_tc == 1) | (clases_con_pareja_tc == 3)) & (perfiles1 == 1) & (perfiles2 == 1)
    # Condición B: Clases tipo 2 o 4 no pueden tener dos pedagógicos (perfil 2)
    conflictos_b = ((clases_con_pareja_tc == 2) | (clases_con_pareja_tc == 4)) & (perfiles1 == 2) & (perfiles2 == 2)
    
    conflictos = np.sum(conflictos_a) + np.sum(conflictos_b)
            
    return int(conflictos)


def FR8(cromosoma, gestorDatos):
    """
    Restricción 8 (R8): Competencia en trayecto. Verifica que el facilitador sea competente.
    """
    matriz_clases_req = gestorDatos["clases_req"]
    matriz_conocimiento_trayecto = gestorDatos["conocimiento_trayecto"]
    
    trayectos_clases = matriz_clases_req[:, 3]
    
    # Aplanar el cromosoma y repetir los trayectos para alinear
    ids_asignados = cromosoma.flatten()
    trayectos_repetidos = np.repeat(trayectos_clases, 4) # 4 roles
    
    # Crear una máscara para las asignaciones válidas y que requieren trayecto
    mascara_validos = (ids_asignados != -1) & (trayectos_repetidos != -1)
    if not np.any(mascara_validos):
        return 0
        
    facs = ids_asignados[mascara_validos]
    trays = trayectos_repetidos[mascara_validos]
    
    conocimientos = matriz_conocimiento_trayecto[facs, trays]
    conflictos = np.sum(conocimientos == 0)
            
    return int(conflictos)