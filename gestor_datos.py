import pandas as pd
from clases import (Facilitador, TipoFacilitador, Trayecto, TipoTrayecto, 
                    DisponibilidadTrayecto, DisponibilidadHoraria, ModuloDeHorario,
                    Salon, HorarioDeClase, Clase)

class GestorDatos:
    def __init__(self):
        # Inicialización de colecciones en memoria
        self.listaFacilitadores = []
        self.listaTrayectos = []
        self.listaSalones = []
        self.listaHorariosClases = []
        self.listaClases = []

    def cargarCsv(self, clave, rutaArchivo):
        """
        Procesa la lectura de archivos CSV según la clave proporcionada
        y genera las instancias correspondientes en memoria aplicando camelCase.
        """
        try:
            # ----------------------------------------------------
            # Carga de Facilitadores
            # ----------------------------------------------------
            if clave == "facilitadores":
                df = pd.read_csv(rutaArchivo)
                self.listaFacilitadores = []
                
                nombresTipos = {
                    0: "Administrativo", 1: "Técnico", 2: "Pedagógico",
                    3: "Ambos", 4: "Profesor Educación Especial"
                }
                
                for indice, fila in df.iterrows():
                    valorTipo = int(float(fila['Tipo de facilitador']))
                    nombreTipo = nombresTipos.get(valorTipo, "Desconocido")
                    
                    objTipo = TipoFacilitador(idTipo=valorTipo, nombre=nombreTipo)
                    
                    nuevoFacilitador = Facilitador(
                        nombre=fila['Nombre'], 
                        apellido=fila['Apellido'], 
                        dni=fila['DNI'],
                        idFacilitador=fila['ID'], 
                        cantidadHorasCumplir=fila['Horas contrato'],
                        tipoFacilitador=objTipo
                    )
                    self.listaFacilitadores.append(nuevoFacilitador)
                
                print(f"Sistema: Cargados {len(self.listaFacilitadores)} facilitadores en memoria.")
                return True, "Carga completada"

            # ----------------------------------------------------
            # Carga de Trayectos
            # ----------------------------------------------------
            elif clave == "trayectos":
                df = pd.read_csv(rutaArchivo)
                self.listaTrayectos = []
                
                idsPorTipo = {
                    "Trayecto Tradicional": 1,
                    "Propuesta Educativa": 2
                }
                
                for indice, fila in df.iterrows():
                    nombreTipo = str(fila['Tipo']).strip()
                    idAsignado = idsPorTipo.get(nombreTipo, 99)
                    
                    objTipoTrayecto = TipoTrayecto(idTipo=idAsignado, nombre=nombreTipo)
                    
                    nuevoTrayecto = Trayecto(
                        idTrayecto=fila['ID'],
                        nombre=fila['Trayecto'],
                        nivel=fila['Nivel'],
                        tipoTrayecto=objTipoTrayecto
                    )
                    self.listaTrayectos.append(nuevoTrayecto)

                print(f"Sistema: Cargados {len(self.listaTrayectos)} trayectos en memoria.")
                return True, "Carga completada"

            # ----------------------------------------------------
            # Carga de Matriz Facilitadores - Trayectos
            # ----------------------------------------------------
            elif clave == "fac_trayectos":
                if not self.listaFacilitadores or not self.listaTrayectos:
                    return False, "Requisito faltante: Cargar Facilitadores y Trayectos previamente."

                df = pd.read_csv(rutaArchivo)
                vinculacionesHechas = 0
                
                for indice, fila in df.iterrows():
                    idFac = int(fila['ID'])
                    facilitador = next((f for f in self.listaFacilitadores if f.idFacilitador == idFac), None)
                    
                    if facilitador:
                        nuevaDisponibilidad = DisponibilidadTrayecto(idDisponibilidadTrayecto=idFac)
                        
                        # Iteración sobre las columnas de trayectos omitiendo la primera (ID)
                        for nombreColumna in df.columns[1:]:
                            valorCelda = str(fila[nombreColumna]).strip().upper()
                            
                            if valorCelda == "SI":
                                idTrayecto = int(nombreColumna)
                                trayecto = next((t for t in self.listaTrayectos if t.idTrayecto == idTrayecto), None)
                                
                                if trayecto:
                                    nuevaDisponibilidad.agregarTrayecto(trayecto)
                                    vinculacionesHechas += 1
                        
                        facilitador.disponibilidadTrayecto = nuevaDisponibilidad

                print(f"Sistema: Creadas {vinculacionesHechas} vinculaciones Facilitador-Trayecto.")
                return True, "Carga completada"

            # ----------------------------------------------------
            # Carga de Disponibilidad Horaria
            # ----------------------------------------------------
            elif clave == "disponibilidad":
                if not self.listaFacilitadores:
                    return False, "Requisito faltante: Cargar Facilitadores previamente."

                df = pd.read_csv(rutaArchivo)
                
                # Mapeo de horas de formato string a módulos discretos de 15 minutos
                mapaHoras = {
                    '8:00': [1,2,3,4],       '9:00': [5,6,7,8],       '10:00': [9,10,11,12],
                    '11:00': [13,14,15,16],  '12:00': [17,18,19,20],  '13:00': [21,22,23,24],
                    '14:00': [25,26,27,28],  '15:00': [29,30,31,32],  '16:00': [33,34,35,36],
                    '17:00': [37,38,39,40],  '18:00': [41,42,43,44],  '19:00': [45,46,47,48],
                    '20:00': [49,50,51,52]
                }
                
                diasSemana = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes']
                modulosCreados = 0
                
                for indice, fila in df.iterrows():
                    idFac = int(fila['Facilitador'])
                    horaStr = str(fila['Hora']).strip()
                    
                    modulosDeLaHora = mapaHoras.get(horaStr, [])
                    facilitador = next((f for f in self.listaFacilitadores if f.idFacilitador == idFac), None)
                    
                    if facilitador:
                        for dia in diasSemana:
                            valorCelda = str(fila[dia]).strip().upper()
                            
                            if valorCelda == "SI":
                                dispDelDia = next((d for d in facilitador.disponibilidadesHorarias if d.dia == dia), None)
                                
                                if not dispDelDia:
                                    idDisp = len(facilitador.disponibilidadesHorarias) + 1
                                    dispDelDia = DisponibilidadHoraria(idDisponibilidadHoraria=idDisp, dia=dia)
                                    facilitador.agregarDisponibilidadDia(dispDelDia)
                                
                                for numMod in modulosDeLaHora:
                                    nuevoModulo = ModuloDeHorario(idModuloDeHorario=numMod, numeroModulo=numMod)
                                    dispDelDia.agregarModulo(nuevoModulo)
                                    modulosCreados += 1

                print(f"Sistema: Creados {modulosCreados} módulos de disponibilidad horaria.")
                return True, "Carga completada"

            # ----------------------------------------------------
            # Carga de Horarios de Clases
            # ----------------------------------------------------
            elif clave == "horarios_clases":
                if not self.listaTrayectos:
                    return False, "Requisito faltante: Cargar Trayectos previamente."

                df = pd.read_csv(rutaArchivo)
                self.listaClases = []

                def horaAModulo(horaStr):
                    """Convierte formato HH:MM a índice de módulo (1-52)."""
                    if pd.isna(horaStr) or type(horaStr) != str: return 0
                    partes = str(horaStr).strip().split(':')
                    if len(partes) != 2: return 0
                    hora, minutos = int(partes[0]), int(partes[1])
                    return (hora - 8) * 4 + (minutos // 15) + 1

                for indice, fila in df.iterrows():
                    # Procesamiento de Salón
                    nombreSalon = str(fila['Salon']).strip()
                    if nombreSalon.lower() == "nan": nombreSalon = "SIN ASIGNAR"
                    
                    salon = next((s for s in self.listaSalones if s.nombre == nombreSalon), None)
                    if not salon:
                        idSalon = len(self.listaSalones) + 1
                        salon = Salon(idSalon=idSalon, nombre=nombreSalon)
                        self.listaSalones.append(salon)

                    # Procesamiento de Horario
                    dia = str(fila['Dia']).strip()
                    horaInicio = str(fila['Hora Inicio']).strip()
                    horaFin = str(fila['Hora Fin']).strip()
                    
                    startMod = horaAModulo(horaInicio)
                    endMod = horaAModulo(horaFin)
                    
                    idHorario = len(self.listaHorariosClases) + 1
                    horarioClase = HorarioDeClase(idHorarioDeClase=idHorario, dia=dia)
                    
                    if startMod > 0 and endMod > startMod:
                        for numMod in range(startMod, endMod):
                            nuevoModulo = ModuloDeHorario(idModuloDeHorario=numMod, numeroModulo=numMod)
                            horarioClase.agregarModulo(nuevoModulo)
                            
                    self.listaHorariosClases.append(horarioClase)

                    # Procesamiento de Trayecto
                    nombreTrayecto = str(fila['Trayecto']).strip()
                    nivelTrayecto = str(fila['Nivel']).strip()
                    
                    trayecto = next((t for t in self.listaTrayectos if t.nombre == nombreTrayecto and t.nivel == nivelTrayecto), None)
                    if not trayecto:
                        trayecto = next((t for t in self.listaTrayectos if t.nombre == nombreTrayecto), None)

                    # Cálculo del tipo de clase (1 a 5) basado en los requisitos del TFC
                    tipoStr = str(fila['Tipo']).strip().upper()
                    necesitaProfEspecial = str(fila['Prof Educacion Especial']).strip().upper() == "SI"
                    
                    trayectosTpt = ["TECNOKIDS", "PEQUEBOT", "TRENDKIDS"]
                    nombreTrayectoUpper = nombreTrayecto.upper()
                    
                    if tipoStr == "SPRINT":
                        tipoClase = 5
                    elif nombreTrayectoUpper in trayectosTpt:
                        tipoClase = 2 if necesitaProfEspecial else 1
                    else:
                        tipoClase = 4 if necesitaProfEspecial else 3

                    # Instanciación de la Clase
                    idClase = len(self.listaClases) + 1
                    nuevaClase = Clase(
                        idClase=idClase,
                        tipoDeClase=tipoClase,
                        salon=salon,
                        trayecto=trayecto,
                        horarioDeClase=horarioClase
                    )
                    self.listaClases.append(nuevaClase)

                print(f"Sistema: Cargadas {len(self.listaClases)} clases en memoria.")
                return True, "Carga completada"

            return False, "Error: Clave de archivo no reconocida por el sistema."
            
        except Exception as e:
            return False, f"Error durante la lectura del archivo: {e}"

    def estanDatosListos(self):
        """Verifica que todos los conjuntos de datos necesarios estén cargados."""
        return (len(self.listaFacilitadores) > 0 and 
                len(self.listaTrayectos) > 0 and 
                any(f.disponibilidadTrayecto is not None for f in self.listaFacilitadores) and
                any(len(f.disponibilidadesHorarias) > 0 for f in self.listaFacilitadores) and
                len(self.listaClases) > 0)

    def tieneDatos(self, clave):
        """Devuelve el estado de carga de una entidad específica."""
        if clave == "facilitadores":
            return len(self.listaFacilitadores) > 0
        elif clave == "trayectos":
            return len(self.listaTrayectos) > 0
        elif clave == "fac_trayectos":
            return any(f.disponibilidadTrayecto is not None for f in self.listaFacilitadores)
        elif clave == "disponibilidad":
            return any(len(f.disponibilidadesHorarias) > 0 for f in self.listaFacilitadores)
        elif clave == "horarios_clases":
            return len(self.listaClases) > 0
            
        return False