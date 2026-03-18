import random
from clases import Hormiga, Cromosoma, Gen
from restricciones import FR1, FR2, FR3, FR4, FR5, FR6, FR7, FR8

def algoritmoOCH(och, gestorDatos):
    """
    Inicializa la Matriz de Feromonas global dentro del objeto OCH.
    Recibe la instancia de OCH (ya configurada con sus parámetros) y el GestorDatos.
    """
    # Si el diccionario de feromonas no está inicializado, se lo crea
    if not isinstance(och.feromonaGlobal, dict):
        och.feromonaGlobal = {}
        
    for clase in gestorDatos.listaClases:
        for facilitador in gestorDatos.listaFacilitadores:
            och.feromonaGlobal[(clase.idClase, facilitador.idFacilitador)] = och.feromonaInicial

def _girarRuleta(och, gestorDatos, clase, genActual, cromosomaActual, rol):
    """
    Función de soporte: Aplica el filtro heurístico (FR1, FR2, FR8) y la ruleta estocástica.
    """
    candidatos = gestorDatos.listaFacilitadores
    atractivos = {}
    sumaAtractivos = 0.0
    esPee = (rol == "PEE")
    
    for facilitador in candidatos:
        idCandidato = facilitador.idFacilitador
        tipoCandidato = facilitador.tipoFacilitador.idTipo
        
        # Filtro lógico de roles para Educación Especial
        if esPee and tipoCandidato != 4:
            continue
        if not esPee and tipoCandidato == 4:
            continue

        # Disfraz temporal para evaluar restricciones duras
        if rol == "F1": genActual.idFacilitador1 = idCandidato
        elif rol == "F2": genActual.idFacilitador2 = idCandidato
        elif rol == "FC": genActual.idFacilitadorComplementario = idCandidato
        elif rol == "PEE": genActual.idProfesorEducacionEspecial = idCandidato
        
        conflictos = (FR1(cromosomaActual, gestorDatos) + 
                      FR2(cromosomaActual, gestorDatos) + 
                      FR8(cromosomaActual, gestorDatos))
        
        # Limpiamos el disfraz
        if rol == "F1": genActual.idFacilitador1 = None
        elif rol == "F2": genActual.idFacilitador2 = None
        elif rol == "FC": genActual.idFacilitadorComplementario = None
        elif rol == "PEE": genActual.idProfesorEducacionEspecial = None
        
        eta = 1.0 if conflictos == 0 else 0.0
        tau = och.feromonaGlobal.get((clase.idClase, idCandidato), och.feromonaInicial)
        
        atractivo = (tau ** och.importanciaFeromona) * (eta ** och.importanciaHeuristica)
        
        if atractivo > 0:
            atractivos[idCandidato] = atractivo
            sumaAtractivos += atractivo

    # Callejón sin salida: si ningún facilitador es válido, elige uno al azar del perfil correcto
    # Esto ya seria un caso extremo de evaporacion
    if sumaAtractivos == 0.0:
        validos = [f for f in candidatos if (f.tipoFacilitador.idTipo == 4) == esPee]
        if validos:
            return random.choice(validos).idFacilitador
        return None

    # Selección estocástica
    r = random.uniform(0.0, 1.0) * sumaAtractivos
    intervaloAcumulado = 0.0
    for idCandidato, valorAtractivo in atractivos.items():
        intervaloAcumulado += valorAtractivo
        if r <= intervaloAcumulado:
            return idCandidato
            
    return list(atractivos.keys())[-1]

def generarPoblacionInicial(och, gestorDatos):
    """
    Ejecuta el ciclo de las hormigas en grupos y retorna la lista de Cromosomas factibles.
    """
    poblacionTotal = []
    
    # Manejo de seguridad por si grupoHormigas es 0 o nulo
    grupos = och.grupoHormigas if och.grupoHormigas > 0 else 1
    hormigasPorGrupo = och.numeroHormigas // grupos
    
    idHormigaGlobal = 1
    
    for numGrupo in range(grupos):
        poblacionDelGrupo = []
        
        # FASE 1: CONSTRUCCIÓN
        for _ in range(hormigasPorGrupo):
            hormiga = Hormiga(idHormiga=idHormigaGlobal, algoritmoOCH=och, poblacion=None)
            cromosomaActual = Cromosoma(idCromosoma=idHormigaGlobal, funcionAptitud=0.0, ordenCromosoma=idHormigaGlobal, poblacion=None)
            
            for clase in gestorDatos.listaClases:
                genNuevo = Gen(idGen=clase.idClase, idFacilitador1=None, idFacilitador2=None, 
                               idFacilitadorComplementario=None, idProfesorEducacionEspecial=None, 
                               evaluar=True, cromosoma=cromosomaActual)
                
                # Añadimos el gen vacío PRIMERO para que las restricciones evalúen el contexto
                cromosomaActual.agregarGen(genNuevo)
                
                # Asignación guiada por Ruleta y Restricciones Duras
                genNuevo.idFacilitador1 = _girarRuleta(och, gestorDatos, clase, genNuevo, cromosomaActual, "F1")
                genNuevo.idFacilitador2 = _girarRuleta(och, gestorDatos, clase, genNuevo, cromosomaActual, "F2")
                genNuevo.idFacilitadorComplementario = _girarRuleta(och, gestorDatos, clase, genNuevo, cromosomaActual, "FC")
                
                # Si la clase requiere Profesor de Educación Especial (TC = 3 o 4)
                if clase.tipoDeClase == 3 or clase.tipoDeClase == 4:
                    genNuevo.idProfesorEducacionEspecial = _girarRuleta(och, gestorDatos, clase, genNuevo, cromosomaActual, "PEE")
            
            poblacionDelGrupo.append(cromosomaActual)
            idHormigaGlobal += 1
            
        # FASE 2: EVALUACIÓN PARA BUSCAR A LA CAMPEONA DEL GRUPO
        mejorCromosoma = None
        menorConflictos = float('inf')
        
        for cromosoma in poblacionDelGrupo:
            conflictosCalidad = (FR3(cromosoma, gestorDatos) + 
                                 FR4(cromosoma, gestorDatos) + 
                                 FR5(cromosoma, gestorDatos) + 
                                 FR6(cromosoma, gestorDatos) + 
                                 FR7(cromosoma, gestorDatos))
            
            if conflictosCalidad < menorConflictos:
                menorConflictos = conflictosCalidad
                mejorCromosoma = cromosoma
        
        # FASE 3: EVAPORACIÓN GLOBAL
        for clave in och.feromonaGlobal:
            och.feromonaGlobal[clave] *= (1.0 - och.evaporacionFeromona)
            
        # FASE 4: DEPÓSITO DE FEROMONAS (PREMIO ELITISTA)
        if mejorCromosoma is not None:
            for gen in mejorCromosoma.genes:
                idClase = gen.idGen
                if gen.idFacilitador1: och.feromonaGlobal[(idClase, gen.idFacilitador1)] += och.premioFeromona
                if gen.idFacilitador2: och.feromonaGlobal[(idClase, gen.idFacilitador2)] += och.premioFeromona
                if gen.idFacilitadorComplementario: och.feromonaGlobal[(idClase, gen.idFacilitadorComplementario)] += och.premioFeromona
                if gen.idProfesorEducacionEspecial: och.feromonaGlobal[(idClase, gen.idProfesorEducacionEspecial)] += och.premioFeromona

        poblacionTotal.extend(poblacionDelGrupo)
        
    return poblacionTotal