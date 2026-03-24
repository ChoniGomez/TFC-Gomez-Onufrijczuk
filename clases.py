from datetime import datetime

class Persona:
    def __init__(self, nombre, apellido, dni):
        # Limpia los espacios en blanco de nombre, apellido y DNI.
        self.nombre = str(nombre).strip()
        self.apellido = str(apellido).strip()
        self.dni = str(dni).strip()

class TipoFacilitador:
    def __init__(self, idTipo, nombre):
        self.idTipo = int(idTipo)
        self.nombre = str(nombre)

class Facilitador(Persona):
    def __init__(self, nombre, apellido, dni, idFacilitador, cantidadHorasCumplir, tipoFacilitador):
        super().__init__(nombre, apellido, dni)
        self.idFacilitador = int(idFacilitador)
        self.cantidadHorasCumplir = int(cantidadHorasCumplir)
        self.tipoFacilitador = tipoFacilitador 
        self.disponibilidadTrayecto = None 

        # Guarda la disponibilidad horaria del facilitador.
        self.disponibilidadesHorarias = [] 

    def agregarDisponibilidadDia(self, disponibilidadDia):
        self.disponibilidadesHorarias.append(disponibilidadDia)

    def __repr__(self):
        # Muestra un resumen del facilitador.
        cantidad = len(self.disponibilidadTrayecto.trayectos) if self.disponibilidadTrayecto else 0
        return f"<Facilitador: {self.nombre} | Horas: {self.cantidadHorasCumplir} | Trayectos: {cantidad} | Días Disp: {len(self.disponibilidadesHorarias)}>"

class TipoTrayecto:
    def __init__(self, idTipo, nombre):
        self.idTipo = int(idTipo)
        self.nombre = str(nombre).strip()

class Trayecto:
    def __init__(self, idTrayecto, nombre, nivel, tipoTrayecto):
        self.idTrayecto = int(idTrayecto)
        self.nombre = str(nombre).strip()
        self.nivel = str(nivel).strip()  # Valores esperados: "Básico" o "Avanzado"

        # Guarda el tipo de trayecto (Tradicional o Propuesta).
        self.tipoTrayecto = tipoTrayecto

    def __repr__(self):
        return f"<Trayecto ID: {self.idTrayecto} | {self.nombre} ({self.nivel}) | Tipo: {self.tipoTrayecto.nombre}>"

class DisponibilidadTrayecto:
    def __init__(self, idDisponibilidadTrayecto):
        self.idDisponibilidadTrayecto = int(idDisponibilidadTrayecto)
        self.trayectos = [] 

    def agregarTrayecto(self, trayecto):
        self.trayectos.append(trayecto)

    def __repr__(self):
        return f"<Disponibilidad ID: {self.idDisponibilidadTrayecto} | Total trayectos: {len(self.trayectos)}>"
    
class ModuloDeHorario:
    def __init__(self, idModuloDeHorario, numeroModulo):
        self.idModuloDeHorario = int(idModuloDeHorario)
        self.numeroModulo = int(numeroModulo)

    def __repr__(self):
        # Muestra el módulo como [M12].
        return f"[M{self.numeroModulo}]"

class DisponibilidadHoraria:
    def __init__(self, idDisponibilidadHoraria, dia):
        self.idDisponibilidadHoraria = int(idDisponibilidadHoraria)
        self.dia = str(dia).strip()
        self.modulos = [] 

    def agregarModulo(self, modulo):
        self.modulos.append(modulo)

    def __repr__(self):
        return f"<{self.dia}: {len(self.modulos)} módulos habilitados>"

class Salon:
    def __init__(self, idSalon, nombre):
        self.idSalon = int(idSalon)
        self.nombre = str(nombre).strip()

    def __repr__(self):
        return f"<Salón: {self.nombre}>"

class HorarioDeClase:
    def __init__(self, idHorarioDeClase, dia):
        self.idHorarioDeClase = int(idHorarioDeClase)
        self.dia = str(dia).strip()
        self.modulos = []

    def agregarModulo(self, modulo):
        self.modulos.append(modulo)

    def __repr__(self):
        return f"<{self.dia} | {len(self.modulos)} módulos>"

class Clase:
    def __init__(self, idClase, tipoDeClase, salon, trayecto, horarioDeClase):
        self.idClase = int(idClase)
        self.tipoDeClase = int(tipoDeClase)
        self.salon = salon
        self.trayecto = trayecto
        self.horarioDeClase = horarioDeClase

        # Los facilitadores se asignan durante la optimización.
        self.facilitador1 = None
        self.facilitador2 = None
        self.facilitadorComplementario = None
        self.profesorEducacionEspecial = None

    def __repr__(self):
        nombreTrayecto = self.trayecto.nombre if self.trayecto else "Sin Trayecto"
        nombreSalon = self.salon.nombre if self.salon else "Sin Salón"
        return f"<Clase ID: {self.idClase} | Tipo: {self.tipoDeClase} | {nombreTrayecto} | {nombreSalon} | {self.horarioDeClase.dia}>"
    
class OCH:
    """
    Configuración del algoritmo de Colonia de Hormigas (OCH).
    """
    def __init__(self, idOCH, numeroHormigas, feromonaInicial, evaporacionFeromona, 
                 feromonaGlobal, importanciaHeuristica, importanciaFeromona, 
                 grupoHormigas=1, premioFeromona=0.0):

        self.idOCH = int(idOCH)
        self.numeroHormigas = int(numeroHormigas)

        # Parámetros para Batches y Elitismo
        self.grupoHormigas = int(grupoHormigas)

        # Asegura que los parámetros sean flotantes.
        self.feromonaInicial = float(feromonaInicial)
        self.evaporacionFeromona = float(evaporacionFeromona)
        self.importanciaHeuristica = float(importanciaHeuristica)
        self.importanciaFeromona = float(importanciaFeromona)
        self.premioFeromona = float(premioFeromona)

        # Matriz de feromonas (diccionario para eficiencia).
        self.feromonaGlobal = feromonaGlobal if feromonaGlobal is not None else {}

    def __repr__(self):
        return (f"<OCH idOCH: {self.idOCH} | numeroHormigas: {self.numeroHormigas} | "
                f"evaporacionFeromona: {self.evaporacionFeromona}>")

class Gen:
    """
    Unidad de información (gen). Representa la asignación de una clase.
    """
    def __init__(self, idGen, idFacilitador1, idFacilitador2, idFacilitadorComplementario, 
                 idProfesorEducacionEspecial, evaluar, cromosoma):

        self.idGen = int(idGen)
        self.idFacilitador1 = int(idFacilitador1) if idFacilitador1 is not None else None
        self.idFacilitador2 = int(idFacilitador2) if idFacilitador2 is not None else None
        self.idFacilitadorComplementario = int(idFacilitadorComplementario) if idFacilitadorComplementario is not None else None
        self.idProfesorEducacionEspecial = int(idProfesorEducacionEspecial) if idProfesorEducacionEspecial is not None else None

        self.evaluar = bool(evaluar)

        # Referencia al objeto Cromosoma padre
        self.cromosoma = cromosoma

    def __repr__(self):
        return f"<Gen idGen: {self.idGen} | evaluar: {self.evaluar}>"

class Cromosoma:
    """
    Solución candidata (cromosoma). Es un conjunto de genes.
    """
    def __init__(self, idCromosoma, funcionAptitud, ordenCromosoma, poblacion):
        self.idCromosoma = int(idCromosoma)
        self.funcionAptitud = float(funcionAptitud)
        self.ordenCromosoma = int(ordenCromosoma)
        
        # Referencia al objeto Poblacion padre
        self.poblacion = poblacion

        # Colección de objetos Gen
        self.genes = []

    def agregarGen(self, gen):
        self.genes.append(gen)

    def __repr__(self):
        return f"<Cromosoma idCromosoma: {self.idCromosoma} | funcionAptitud: {self.funcionAptitud:.4f} | genes: {len(self.genes)}>"

class Poblacion:
    """
    Conjunto de cromosomas en una generación.
    """
    def __init__(self, idPoblacion, ordenPoblacion, corrida):
        self.idPoblacion = int(idPoblacion)
        self.ordenPoblacion = int(ordenPoblacion)

        # Referencia al objeto Corrida padre
        self.corrida = corrida

        # Colección de objetos Cromosoma
        self.cromosomas = []

    def agregarCromosoma(self, cromosoma):
        self.cromosomas.append(cromosoma)

    def __repr__(self):
        return f"<Poblacion idPoblacion: {self.idPoblacion} | ordenPoblacion: {self.ordenPoblacion} | cromosomas: {len(self.cromosomas)}>"

class Corrida:
    """
    Configuración y resultados de una ejecución del Algoritmo Genético.
    """
    def __init__(self, idCorrida, numeroIndividuos, numeroGeneraciones, horaInicio, horaFin,
                 puntosCruza, probabilidadMutacion, probabilidadMutacionFacilitador1,
                 probabilidadMutacionFacilitador2, probabilidadMutacionFacilitadorComplementario,
                 probabilidadMutacionProfEdEspecial):
        
        self.idCorrida = int(idCorrida)
        self.numeroIndividuos = int(numeroIndividuos)
        self.numeroGeneraciones = int(numeroGeneraciones)

        # Instancias de tipo datetime
        self.horaInicio = horaInicio
        self.horaFin = horaFin

        # Operadores genéticos
        self.puntosCruza = int(puntosCruza)
        self.probabilidadMutacion = float(probabilidadMutacion)
        self.probabilidadMutacionFacilitador1 = float(probabilidadMutacionFacilitador1)
        self.probabilidadMutacionFacilitador2 = float(probabilidadMutacionFacilitador2)
        self.probabilidadMutacionFacilitadorComplementario = float(probabilidadMutacionFacilitadorComplementario)
        self.probabilidadMutacionProfEdEspecial = float(probabilidadMutacionProfEdEspecial)

        # Colección de objetos Poblacion (historial evolutivo)
        self.poblacion = []

    def agregarPoblacion(self, objetoPoblacion):
        self.poblacion.append(objetoPoblacion)

    def __repr__(self):
        return (f"<Corrida idCorrida: {self.idCorrida} | numeroGeneraciones: {self.numeroGeneraciones} | "
                f"numeroIndividuos: {self.numeroIndividuos}>")

class Hormiga:
    """
    Agente individual (hormiga) que construye una solución.
    """
    def __init__(self, idHormiga, algoritmoOCH, poblacion):
        self.idHormiga = int(idHormiga)

        # Referencia a la instancia global de configuración del algoritmo (clase OCH)
        self.algoritmoOCH = algoritmoOCH

        # Solución construida por este agente en la iteración actual (clase Poblacion)
        self.poblacion = poblacion

    def __repr__(self):
        return f"<Hormiga idHormiga: {self.idHormiga}>"