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
    Función de soporte: Aplica un filtro heurístico rápido (FR1, FR2, FR8) 
    verificando propiedades directas en lugar de evaluar todo el cromosoma, 
    evitando la explosión combinatoria.
    """
    candidatos = gestorDatos.listaFacilitadores
    atractivos = {}
    sumaAtractivos = 0.0
    esPee = (rol == "PEE")
    
    # Pre-calculamos los datos de la clase actual para no repetir código
    diaClase = clase.horarioDeClase.dia
    modulosClaseActual = set(m.idModuloDeHorario for m in clase.horarioDeClase.modulos)
    
    for facilitador in candidatos:
        idCandidato = facilitador.idFacilitador
        tipoCandidato = facilitador.tipoFacilitador.idTipo
        
        # 1. Filtro lógico de roles
        if esPee and tipoCandidato != 4: continue
        if not esPee and tipoCandidato == 4: continue

        # =========================================================
        # EVALUACIÓN RÁPIDA (Reemplaza a las FR pesadas)
        # =========================================================
        
        # FAST FR8: ¿Tiene la competencia para este trayecto?
        esCompetente = False
        if facilitador.disponibilidadTrayecto:
            for t in facilitador.disponibilidadTrayecto.trayectos:
                if t.idTrayecto == clase.trayecto.idTrayecto:
                    esCompetente = True
                    break
        if not esCompetente: continue # Falla la competencia, descartar
        
        # FAST FR2: ¿Tiene disponibilidad horaria contractual hoy?
        estaDisponible = False
        for disp in facilitador.disponibilidadesHorarias:
            if disp.dia == diaClase:
                modulosProfe = set(m.idModuloDeHorario for m in disp.modulos)
                # Verificamos si los módulos de la clase están dentro de los módulos del profe
                if modulosClaseActual.issubset(modulosProfe):
                    estaDisponible = True
                    break
        if not estaDisponible: continue # Falla la disponibilidad, descartar
        
        # FAST FR1: ¿Ya está asignado a otra clase que se solapa ahora mismo?
        tieneChoque = False
        for genAnterior in cromosomaActual.genes:
            # Ignoramos el gen que estamos construyendo ahora
            if genAnterior.idGen == clase.idClase: continue 
            
            # Si el profe ya está asignado a esa clase anterior...
            if idCandidato in [genAnterior.idFacilitador1, genAnterior.idFacilitador2, 
                               genAnterior.idFacilitadorComplementario, genAnterior.idProfesorEducacionEspecial]:
                
                # Buscamos los datos de esa clase anterior
                claseAnterior = next((c for c in gestorDatos.listaClases if c.idClase == genAnterior.idGen), None)
                if claseAnterior and claseAnterior.horarioDeClase.dia == diaClase:
                    modulosAnteriores = set(m.idModuloDeHorario for m in claseAnterior.horarioDeClase.modulos)
                    # Si hay intersección de módulos, significa que chocan los horarios
                    if modulosClaseActual.intersection(modulosAnteriores):
                        tieneChoque = True
                        break
        if tieneChoque: continue # Falla por choque de horario, descartar

        # =========================================================
        # CÁLCULO DE PROBABILIDAD (Si llegó hasta acá, es apto)
        # =========================================================
        eta = 1.0 
        tau = och.feromonaGlobal.get((clase.idClase, idCandidato), och.feromonaInicial)
        
        atractivo = (tau ** och.importanciaFeromona) * (eta ** och.importanciaHeuristica)
        
        if atractivo > 0:
            atractivos[idCandidato] = atractivo
            sumaAtractivos += atractivo

    # Callejón sin salida (Si todos fallaron los filtros)
    if sumaAtractivos == 0.0:
        validos = [f for f in candidatos if (f.tipoFacilitador.idTipo == 4) == esPee]
        if validos:
            return random.choice(validos).idFacilitador
        return None

    # Selección estocástica (Ruleta)
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
    
    # La cantidad ingresada es igual la cantidad por cada grupo
    hormigasPorGrupo = och.numeroHormigas
    
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