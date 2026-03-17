def f_solapar_clase(claseI, claseJ):
    """
    Verifica si dos clases se solapan en el espacio temporal.
    Corresponde a la función f_solapar_clase del modelo teórico.
    
    Retorna:
        1 si comparten el mismo día y existe intersección de módulos de horario.
        0 en caso contrario.
    """
    # Si no ocurren el mismo día, es imposible que se solapen
    if claseI.horarioDeClase.dia != claseJ.horarioDeClase.dia:
        return 0
    
    # Extracción de los números de módulos en conjuntos (sets) para búsqueda eficiente
    modulosI = {modulo.numeroModulo for modulo in claseI.horarioDeClase.modulos}
    modulosJ = {modulo.numeroModulo for modulo in claseJ.horarioDeClase.modulos}
    
    # Si la intersección de conjuntos no está vacía, hay choque horario
    if modulosI.intersection(modulosJ):
        return 1
    
    return 0


def FR1(cromosoma, gestorDatos):
    """
    Restricción 1 (R1): Un facilitador no puede estar asignado a dos clases 
    simultáneamente ni a clases con horarios solapados.
    
    Esta función itera sobre la configuración del cromosoma (Matriz_HCT teórica) 
    y retorna la sumatoria de penalizaciones detectadas.
    """
    conflictos = 0
    
    # ncl representa el número total de clases (filas de la matriz)
    ncl = len(cromosoma.genes)
    listaClases = gestorDatos.listaClases 
    
    # Recorrido con dos bucles anidados para comparar cada clase con las subsiguientes
    for i in range(0, ncl - 1):
        for j in range(i + 1, ncl):
            
            # Se obtienen las instancias de clase correspondientes al índice
            claseI = listaClases[i]
            claseJ = listaClases[j]
            
            if f_solapar_clase(claseI, claseJ) == 1:
                genI = cromosoma.genes[i]
                genJ = cromosoma.genes[j]
                
                # =========================================================
                # Instancia 1: Análisis de roles intercambiables
                # =========================================================
                listaFacilitadoresI = []
                if genI.idFacilitador1 is not None and genI.idFacilitador1 > 0:
                    listaFacilitadoresI.append(genI.idFacilitador1)
                if genI.idFacilitador2 is not None and genI.idFacilitador2 > 0:
                    listaFacilitadoresI.append(genI.idFacilitador2)
                if genI.idFacilitadorComplementario is not None and genI.idFacilitadorComplementario > 0:
                    listaFacilitadoresI.append(genI.idFacilitadorComplementario)
                    
                listaFacilitadoresJ = []
                if genJ.idFacilitador1 is not None and genJ.idFacilitador1 > 0:
                    listaFacilitadoresJ.append(genJ.idFacilitador1)
                if genJ.idFacilitador2 is not None and genJ.idFacilitador2 > 0:
                    listaFacilitadoresJ.append(genJ.idFacilitador2)
                if genJ.idFacilitadorComplementario is not None and genJ.idFacilitadorComplementario > 0:
                    listaFacilitadoresJ.append(genJ.idFacilitadorComplementario)
                    
                # Búsqueda de intersecciones de docentes
                for idDocente in listaFacilitadoresI:
                    if idDocente in listaFacilitadoresJ:
                        conflictos += 1
                        
                # =========================================================
                # Instancia 2: Análisis de carril exclusivo (Prof. Ed. Especial)
                # =========================================================
                peI = genI.idProfesorEducacionEspecial if genI.idProfesorEducacionEspecial is not None else 0
                peJ = genJ.idProfesorEducacionEspecial if genJ.idProfesorEducacionEspecial is not None else 0
                
                if peI > 0 and peJ > 0:
                    if peI == peJ:
                        conflictos += 1
                        
    return conflictos

def f_horas_clase(clase):
    """
    Extrae la información temporal de una clase.
    Corresponde a la función auxiliar f_horas_clase del modelo teórico.
    
    Retorna:
        Una tupla (dia_de_la_clase, lista_de_modulos)
    """
    dia = clase.horarioDeClase.dia
    modulos = [modulo.numeroModulo for modulo in clase.horarioDeClase.modulos]
    return dia, modulos


def FR2(cromosoma, gestorDatos):
    """
    Restricción 2 (R2): Respetar la disponibilidad horaria de cada facilitador.
    
    Evalúa el cumplimiento de la disponibilidad horaria contrastando 
    los genes de la solución candidata (Matriz_HCT) contra la disponibilidad 
    declarada en los objetos Facilitador (abstracción de Matriz_DF).
    """
    conflictos = 0
    ncl = len(cromosoma.genes)
    listaClases = gestorDatos.listaClases
    
    # Mapeo Hash para acceso O(1) a los facilitadores (Abstracción de Matriz_DF)
    diccFacilitadores = {f.idFacilitador: f for f in gestorDatos.listaFacilitadores}
    
    # Recorrido secuencial sobre la totalidad de las clases
    for i in range(ncl):
        gen = cromosoma.genes[i]
        clase = listaClases[i]
        
        diaClase, bloquesClase = f_horas_clase(clase)
        
        # =========================================================
        # Evaluación Facilitador 1 (NF1)
        # =========================================================
        idF1 = gen.idFacilitador1 if gen.idFacilitador1 is not None else 0
        if idF1 > 0:
            facilitador = diccFacilitadores.get(idF1)
            # Extracción de los módulos disponibles para el día evaluado
            dispDia = next((d for d in facilitador.disponibilidadesHorarias if d.dia == diaClase), None) if facilitador else None
            modulosDisp = {m.numeroModulo for m in dispDia.modulos} if dispDia else set()
            
            for bloqueK in bloquesClase:
                if bloqueK not in modulosDisp: # Equivalente a Matriz_DF[id_f1][bloque_k] == 0
                    conflictos += 1
                    break  # Mecanismo de interrupción controlada (Romper Bucle)
        
        # =========================================================
        # Evaluación Facilitador 2 (NF2)
        # =========================================================
        idF2 = gen.idFacilitador2 if gen.idFacilitador2 is not None else 0
        if idF2 > 0:
            facilitador = diccFacilitadores.get(idF2)
            dispDia = next((d for d in facilitador.disponibilidadesHorarias if d.dia == diaClase), None) if facilitador else None
            modulosDisp = {m.numeroModulo for m in dispDia.modulos} if dispDia else set()
            
            for bloqueK in bloquesClase:
                if bloqueK not in modulosDisp:
                    conflictos += 1
                    break  # Romper Bucle
        
        # =========================================================
        # Evaluación Facilitador Complementario (NFC)
        # =========================================================
        idFc = gen.idFacilitadorComplementario if gen.idFacilitadorComplementario is not None else 0
        if idFc > 0:
            facilitador = diccFacilitadores.get(idFc)
            dispDia = next((d for d in facilitador.disponibilidadesHorarias if d.dia == diaClase), None) if facilitador else None
            modulosDisp = {m.numeroModulo for m in dispDia.modulos} if dispDia else set()
            
            for bloqueK in bloquesClase:
                if bloqueK not in modulosDisp:
                    conflictos += 1
                    break  # Romper Bucle
        
        # =========================================================
        # Evaluación Profesor de Educación Especial (NPEE)
        # =========================================================
        idPee = gen.idProfesorEducacionEspecial if gen.idProfesorEducacionEspecial is not None else 0
        if idPee > 0:
            facilitador = diccFacilitadores.get(idPee)
            dispDia = next((d for d in facilitador.disponibilidadesHorarias if d.dia == diaClase), None) if facilitador else None
            modulosDisp = {m.numeroModulo for m in dispDia.modulos} if dispDia else set()
            
            for bloqueK in bloquesClase:
                if bloqueK not in modulosDisp:
                    conflictos += 1
                    break  # Romper Bucle

    return conflictos

def FR3(cromosoma, gestorDatos):
    """
    Restricción 3 (R3): Respetar las horas contractuales por semana de cada facilitador.
    
    Evalúa el cumplimiento de las horas semanales contrastando la carga horaria 
    real asignada en el cromosoma frente a los límites contractuales del Facilitador.
    Los Profesores de Educación Especial están exentos de la penalización por subutilización.
    """
    conflictos = 0
    listaFacilitadores = gestorDatos.listaFacilitadores
    listaClases = gestorDatos.listaClases
    ncl = len(cromosoma.genes)
    
    for facilitador in listaFacilitadores:
        idFacilitador = facilitador.idFacilitador
        blcAcumulados = 0
        
        # Identifica si el perfil es Profesor de Educación Especial (idTipo == 4 según gestor_datos)
        esPee = (facilitador.tipoFacilitador.idTipo == 4)
        
        # Recorrido anidado para sumar las horas asignadas en la solución actual
        for i in range(ncl):
            gen = cromosoma.genes[i]
            
            # Verifica si el identificador del docente coincide con alguna de las asignaciones
            if (gen.idFacilitador1 == idFacilitador or 
                gen.idFacilitador2 == idFacilitador or 
                gen.idFacilitadorComplementario == idFacilitador or 
                gen.idProfesorEducacionEspecial == idFacilitador):
                
                # Se extrae la duración de la clase utilizando la función auxiliar
                clase = listaClases[i]
                diaClase, modulosClase = f_horas_clase(clase)
                
                # Cada módulo representa un bloque de 15 minutos
                blcAcumulados += len(modulosClase)
                
        # Conversión de bloques de 15 minutos a horas de reloj (4 bloques = 1 hora)
        horasTrabajadas = blcAcumulados / 4.0
        
        # Parámetros de la ventana de optimización
        limiteMaximo = facilitador.cantidadHorasCumplir
        limiteMinimo = limiteMaximo * 0.80
        
        # Evaluación de la restricción diferenciada
        if horasTrabajadas > limiteMaximo:
            # Infracción por sobrecarga: Penaliza a todos los perfiles por igual
            conflictos += 1
        elif (horasTrabajadas < limiteMinimo) and not esPee:
            # Infracción por subutilización: Excluye a los Profesores de Educación Especial
            conflictos += 1
            
    return conflictos

def CumplePorcentajeHoras(idFacilitador, idTrayecto, cromosoma, listaClases):
    """
    Función de evaluación de la Restricción 4 (Soporte).
    Verifica si el facilitador dictó al menos el 50% de las clases regulares de un trayecto.
    Corresponde a la función auxiliar CumplePorcentajeHoras del modelo teórico.
    """
    totalBloquesTrayecto = 0
    bloquesDelDocente = 0
    ncl = len(cromosoma.genes)
    
    for i in range(ncl):
        gen = cromosoma.genes[i]
        clase = listaClases[i]
        
        # Validación: La clase debe pertenecer al trayecto y NO ser un Sprint (TC=5)
        # Se requiere comprobación previa de existencia del objeto trayecto
        if clase.trayecto is not None and clase.trayecto.idTrayecto == idTrayecto and clase.tipoDeClase != 5:
            
            # Obtención de la duración en módulos (f_horas_clase)
            _, modulosClase = f_horas_clase(clase)
            duracion = len(modulosClase)
            
            # Sumatoria global de la duración del trayecto
            totalBloquesTrayecto += duracion
            
            # Sumatoria parcial si el docente participa en esta clase
            if (gen.idFacilitador1 == idFacilitador or 
                gen.idFacilitador2 == idFacilitador or 
                gen.idFacilitadorComplementario == idFacilitador):
                
                bloquesDelDocente += duracion
                
    # Cálculo del umbral (50%)
    mitadRequerida = totalBloquesTrayecto / 2.0
    
    if bloquesDelDocente >= mitadRequerida:
        return True
    else:
        return False


def FR4(cromosoma, gestorDatos):
    """
    Restricción 4 (R4): Organizar los grupos de Sprint de planificación de clases.
    
    Examina las clases de planificación (Sprints) para asegurar que los facilitadores 
    asignados (F1, F2, FC) sean aquellos que lideran el dictado del trayecto 
    correspondiente, utilizando la función de validación porcentual.
    """
    conflictos = 0
    ncl = len(cromosoma.genes)
    listaClases = gestorDatos.listaClases
    
    # Recorrido de búsqueda exclusiva de filas que representen Sprints
    for i in range(ncl):
        clase = listaClases[i]
        gen = cromosoma.genes[i]
        
        # TC == 5 identifica a las clases de tipo "Sprint"
        if clase.tipoDeClase == 5 and clase.trayecto is not None:
            idTrayecto = clase.trayecto.idTrayecto
            
            # Examen individual de los agentes asignados válidos
            idF1 = gen.idFacilitador1 if gen.idFacilitador1 is not None else 0
            if idF1 > 0:
                if not CumplePorcentajeHoras(idF1, idTrayecto, cromosoma, listaClases):
                    conflictos += 1
                    
            idF2 = gen.idFacilitador2 if gen.idFacilitador2 is not None else 0
            if idF2 > 0:
                if not CumplePorcentajeHoras(idF2, idTrayecto, cromosoma, listaClases):
                    conflictos += 1
                    
            idFc = gen.idFacilitadorComplementario if gen.idFacilitadorComplementario is not None else 0
            if idFc > 0:
                if not CumplePorcentajeHoras(idFc, idTrayecto, cromosoma, listaClases):
                    conflictos += 1
                    
    return conflictos

def FR5(cromosoma, gestorDatos):
    """
    Restricción 5 (R5): Un facilitador puede estar asignado en tres Sprint 
    de planificaciones de clases como máximo.
    
    Evalúa la sobrecarga en la asignación a Sprints mediante un mapeo 
    de frecuencias (diccionario). La ejecución consta de una fase de 
    recuento y una fase posterior de validación contra el umbral máximo.
    """
    conflictos = 0
    conteoSprints = {} 
    
    ncl = len(cromosoma.genes)
    listaClases = gestorDatos.listaClases
    
    # =========================================================
    # Primera Fase: Recuento de asignaciones a Sprints (TC == 5)
    # =========================================================
    for i in range(ncl):
        clase = listaClases[i]
        gen = cromosoma.genes[i]
        
        if clase.tipoDeClase == 5:
            idF1 = gen.idFacilitador1 if gen.idFacilitador1 is not None else 0
            idF2 = gen.idFacilitador2 if gen.idFacilitador2 is not None else 0
            idFc = gen.idFacilitadorComplementario if gen.idFacilitadorComplementario is not None else 0
            
            # Registro Facilitador 1
            if idF1 > 0:
                if idF1 not in conteoSprints:
                    conteoSprints[idF1] = 0
                conteoSprints[idF1] += 1
                
            # Registro Facilitador 2
            if idF2 > 0:
                if idF2 not in conteoSprints:
                    conteoSprints[idF2] = 0
                conteoSprints[idF2] += 1
                
            # Registro Facilitador Complementario
            if idFc > 0:
                if idFc not in conteoSprints:
                    conteoSprints[idFc] = 0
                conteoSprints[idFc] += 1
                
    # =========================================================
    # Segunda Fase: Evaluación de umbrales organizativos
    # =========================================================
    for idFacilitador, cantidadAsignada in conteoSprints.items():
        # Límite máximo permitido de tres instancias
        if cantidadAsignada > 3:
            conflictos += 1
            
    return conflictos

def FR6(cromosoma, gestorDatos):
    """
    Restricción 6 (R6): Verificar la asistencia de un Profesor de Educación 
    Especial en las clases donde se necesite su presencia.
    
    Evalúa la cobertura obligatoria de Profesores de Educación Especial 
    realizando un recorrido lineal sobre la solución candidata. Si el Tipo 
    de Clase exige integración (TC = 3 o 4), verifica que el rol no esté vacante.
    """
    conflictos = 0
    ncl = len(cromosoma.genes)
    listaClases = gestorDatos.listaClases
    
    # Recorrido lineal sobre la totalidad de las filas que componen la solución candidata
    for i in range(ncl):
        clase = listaClases[i]
        gen = cromosoma.genes[i]
        
        tipoClase = clase.tipoDeClase
        idPee = gen.idProfesorEducacionEspecial if gen.idProfesorEducacionEspecial is not None else 0
        
        # Validación de exigencia estructural para grupos con necesidades de integración
        if tipoClase == 3 or tipoClase == 4:
            # Si el valor resulta menor o igual a cero, denota ausencia del profesional designado
            if idPee <= 0:
                conflictos += 1
                
    return conflictos

def FR7(cromosoma, gestorDatos):
    """
    Restricción 7 (R7): Comprobar la asignación de grupos de facilitadores a las clases de trayectos.
    
    Evalúa la correcta configuración de la pareja docente (Facilitador 1 y 2). 
    Penaliza vacantes y combinaciones incompatibles según el tipo de clase 
    (ej. dos técnicos en grupos de menores o dos pedagógicos en grupos mayores).
    """
    conflictos = 0
    ncl = len(cromosoma.genes)
    listaClases = gestorDatos.listaClases
    
    # Estructura de diccionario para acceso rápido a los facilitadores (O(1))
    diccFacilitadores = {f.idFacilitador: f for f in gestorDatos.listaFacilitadores}
    
    # Recorrido secuencial sobre la totalidad de las filas de la solución candidata
    for i in range(ncl):
        gen = cromosoma.genes[i]
        clase = listaClases[i]
        
        idF1 = gen.idFacilitador1 if gen.idFacilitador1 is not None else 0
        idF2 = gen.idFacilitador2 if gen.idFacilitador2 is not None else 0
        tipoClase = clase.tipoDeClase
        
        # Validación de existencia obligatoria de la pareja docente principal
        if idF1 <= 0 or idF2 <= 0:
            conflictos += 1
            continue  # Se interrumpe el análisis y se avanza hacia la siguiente fila
            
        facilitador1 = diccFacilitadores.get(idF1)
        facilitador2 = diccFacilitadores.get(idF2)
        
        # Validación de seguridad por si el objeto no se encuentra en memoria
        if not facilitador1 or not facilitador2:
            conflictos += 1
            continue
            
        # Determinación de la especialidad de cada agente
        perfilF1 = facilitador1.tipoFacilitador.idTipo
        perfilF2 = facilitador2.tipoFacilitador.idTipo
        
        # Evaluación para grupos de estudiantes menores (apoyo pedagógico obligatorio)
        if tipoClase == 1 or tipoClase == 3:
            # Se penaliza la conformación con dos perfiles exclusivamente técnicos
            if perfilF1 == 1 and perfilF2 == 1:
                conflictos += 1
                
        # Evaluación para grupos de estudiantes mayores (apoyo técnico necesario)
        elif tipoClase == 2 or tipoClase == 4:
            # Se penaliza la superposición de dos perfiles netamente pedagógicos
            if perfilF1 == 2 and perfilF2 == 2:
                conflictos += 1
                
    return conflictos

def FR8(cromosoma, gestorDatos):
    """
    Restricción 8 (R8): Verificar la competencia de cada facilitador por clase de trayecto.
    
    Evalúa la idoneidad y competencia técnica de los docentes asignados.
    Reemplaza la consulta teórica a la Matriz_FT verificando si el idTrayecto 
    de la clase existe dentro del objeto de disponibilidad del facilitador.
    """
    conflictos = 0
    ncl = len(cromosoma.genes)
    listaClases = gestorDatos.listaClases
    
    # Diccionario para acceso rápido O(1) a los facilitadores
    diccFacilitadores = {f.idFacilitador: f for f in gestorDatos.listaFacilitadores}
    
    # Recorrido lineal sobre la totalidad de las filas de la solución candidata
    for i in range(ncl):
        gen = cromosoma.genes[i]
        clase = listaClases[i]
        
        # Validación de seguridad: se requiere que la clase tenga un trayecto asignado
        if clase.trayecto is None:
            continue
            
        idTrayecto = clase.trayecto.idTrayecto
        
        idF1 = gen.idFacilitador1 if gen.idFacilitador1 is not None else 0
        idF2 = gen.idFacilitador2 if gen.idFacilitador2 is not None else 0
        idFc = gen.idFacilitadorComplementario if gen.idFacilitadorComplementario is not None else 0
        idPee = gen.idProfesorEducacionEspecial if gen.idProfesorEducacionEspecial is not None else 0
        
        # =========================================================
        # Validación de idoneidad individual por rol
        # =========================================================
        
        # Facilitador 1
        if idF1 > 0:
            facilitador = diccFacilitadores.get(idF1)
            # Se extraen los IDs de los trayectos en los que el docente es competente
            trayectosDominados = [t.idTrayecto for t in facilitador.disponibilidadTrayecto.trayectos] if (facilitador and facilitador.disponibilidadTrayecto) else []
            
            if idTrayecto not in trayectosDominados: # Equivalente a Matriz_FT[id_f1][id_trayecto] == 0
                conflictos += 1
                
        # Facilitador 2
        if idF2 > 0:
            facilitador = diccFacilitadores.get(idF2)
            trayectosDominados = [t.idTrayecto for t in facilitador.disponibilidadTrayecto.trayectos] if (facilitador and facilitador.disponibilidadTrayecto) else []
            
            if idTrayecto not in trayectosDominados:
                conflictos += 1
                
        # Facilitador Complementario
        if idFc > 0:
            facilitador = diccFacilitadores.get(idFc)
            trayectosDominados = [t.idTrayecto for t in facilitador.disponibilidadTrayecto.trayectos] if (facilitador and facilitador.disponibilidadTrayecto) else []
            
            if idTrayecto not in trayectosDominados:
                conflictos += 1
                
        # Profesor de Educación Especial
        if idPee > 0:
            facilitador = diccFacilitadores.get(idPee)
            trayectosDominados = [t.idTrayecto for t in facilitador.disponibilidadTrayecto.trayectos] if (facilitador and facilitador.disponibilidadTrayecto) else []
            
            if idTrayecto not in trayectosDominados:
                conflictos += 1
                
    return conflictos