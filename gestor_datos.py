import pandas as pd
# IMPORTANTE: Se agregaron Salon, HorarioDeClase y Clase a las importaciones
from clases import (Facilitador, TipoFacilitador, Trayecto, TipoTrayecto, 
                    DisponibilidadTrayecto, DisponibilidadHoraria, ModuloDeHorario,
                    Salon, HorarioDeClase, Clase)

class GestorDatos:
    def __init__(self):
        self.lista_facilitadores = []
        self.lista_trayectos = []
        # --- NUEVAS LISTAS EN MEMORIA ---
        self.lista_salones = []
        self.lista_horarios_clases = []
        self.lista_clases = []

    def cargar_csv(self, clave, ruta_archivo):
        try:
            # ----------------------------------------------------
            # 1. CARGA DE FACILITADORES
            # ----------------------------------------------------
            if clave == "facilitadores":
                df = pd.read_csv(ruta_archivo)
                self.lista_facilitadores = []
                
                nombres_tipos = {
                    0: "Administrativo", 1: "Técnico", 2: "Pedagógico",
                    3: "Ambos", 4: "Profesor Educación Especial"
                }
                
                for indice, fila in df.iterrows():
                    valor_tipo = int(float(fila['Tipo de facilitador']))
                    nombre_tipo = nombres_tipos.get(valor_tipo, "Desconocido")
                    
                    obj_tipo = TipoFacilitador(id_tipo=valor_tipo, nombre=nombre_tipo)
                    
                    nuevo_facilitador = Facilitador(
                        nombre=fila['Nombre'], apellido=fila['Apellido'], dni=fila['DNI'],
                        id_facilitador=fila['ID'], cantidad_horas_cumplir=fila['Horas contrato'],
                        tipo_facilitador=obj_tipo
                    )
                    self.lista_facilitadores.append(nuevo_facilitador)
                
                print(f"\n✅ Éxito: Se cargaron {len(self.lista_facilitadores)} facilitadores en memoria.")
                print("-" * 50)
                for f in self.lista_facilitadores: print(f)
                print("-" * 50, "\n")
                
                return True, "Carga completada"

            # ----------------------------------------------------
            # 2. CARGA DE TRAYECTOS
            # ----------------------------------------------------
            elif clave == "trayectos":
                df = pd.read_csv(ruta_archivo)
                self.lista_trayectos = []
                
                ids_por_tipo = {
                    "Trayecto Tradicional": 1,
                    "Propuesta Educativa": 2
                }
                
                for indice, fila in df.iterrows():
                    nombre_tipo = str(fila['Tipo']).strip()
                    id_asignado = ids_por_tipo.get(nombre_tipo, 99)
                    
                    obj_tipo_trayecto = TipoTrayecto(id_tipo=id_asignado, nombre=nombre_tipo)
                    
                    nuevo_trayecto = Trayecto(
                        id_trayecto=fila['ID'],
                        nombre=fila['Trayecto'],
                        nivel=fila['Nivel'],
                        tipo_trayecto=obj_tipo_trayecto
                    )
                    self.lista_trayectos.append(nuevo_trayecto)

                print(f"\n✅ Éxito: Se cargaron {len(self.lista_trayectos)} trayectos en memoria.")
                print("-" * 50)
                for t in self.lista_trayectos: print(t)
                print("-" * 50, "\n")

                return True, "Carga completada"

            # ----------------------------------------------------
            # 3. CARGA DE FACILITADORES - TRAYECTOS (Matriz)
            # ----------------------------------------------------
            elif clave == "fac_trayectos":
                if not self.lista_facilitadores or not self.lista_trayectos:
                    return False, "Debes cargar Facilitadores y Trayectos antes de este archivo."

                df = pd.read_csv(ruta_archivo)
                vinculaciones_hechas = 0
                
                for indice, fila in df.iterrows():
                    id_fac = int(fila['ID'])
                    
                    facilitador = next((f for f in self.lista_facilitadores if f.id_facilitador == id_fac), None)
                    
                    if facilitador:
                        nueva_disponibilidad = DisponibilidadTrayecto(id_disponibilidad_trayecto=id_fac)
                        
                        for nombre_columna in df.columns[1:]:
                            valor_celda = str(fila[nombre_columna]).strip().upper()
                            
                            if valor_celda == "SI":
                                id_trayecto = int(nombre_columna)
                                trayecto = next((t for t in self.lista_trayectos if t.id_trayecto == id_trayecto), None)
                                
                                if trayecto:
                                    nueva_disponibilidad.agregar_trayecto(trayecto)
                                    vinculaciones_hechas += 1
                        
                        facilitador.disponibilidad_trayecto = nueva_disponibilidad

                print(f"\n✅ Éxito: Se crearon las disponibilidades con {vinculaciones_hechas} vinculaciones en total.")
                print("-" * 50)
                for f in self.lista_facilitadores[:2]:
                    if f.disponibilidad_trayecto:
                        nombres_trayectos = [t.nombre for t in f.disponibilidad_trayecto.trayectos]
                        print(f"{f.nombre} {f.apellido} domina {len(nombres_trayectos)} trayectos: {nombres_trayectos[:3]}...")
                print("-" * 50, "\n")

                return True, "Carga completada"

            # ----------------------------------------------------
            # 4. CARGA DE DISPONIBILIDAD HORARIA (Horas a Módulos)
            # ----------------------------------------------------
            elif clave == "disponibilidad":
                if not self.lista_facilitadores:
                    return False, "Debes cargar Facilitadores antes de su disponibilidad."

                df = pd.read_csv(ruta_archivo)
                
                # Mapa traductor: Convierte la hora de Excel en los 4 módulos correspondientes
                mapa_horas = {
                    '8:00': [1,2,3,4],       '9:00': [5,6,7,8],       '10:00': [9,10,11,12],
                    '11:00': [13,14,15,16],  '12:00': [17,18,19,20],  '13:00': [21,22,23,24],
                    '14:00': [25,26,27,28],  '15:00': [29,30,31,32],  '16:00': [33,34,35,36],
                    '17:00': [37,38,39,40],  '18:00': [41,42,43,44],  '19:00': [45,46,47,48],
                    '20:00': [49,50,51,52]
                }
                
                dias_semana = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes']
                modulos_creados = 0
                
                for indice, fila in df.iterrows():
                    id_fac = int(fila['Facilitador'])
                    hora_str = str(fila['Hora']).strip()
                    
                    modulos_de_la_hora = mapa_horas.get(hora_str, [])
                    facilitador = next((f for f in self.lista_facilitadores if f.id_facilitador == id_fac), None)
                    
                    if facilitador:
                        for dia in dias_semana:
                            valor_celda = str(fila[dia]).strip().upper()
                            
                            if valor_celda == "SI":
                                # 1. Buscamos si el facilitador YA tiene creado el objeto para este día
                                disp_del_dia = next((d for d in facilitador.disponibilidades_horarias if d.dia == dia), None)
                                
                                # 2. Si no existe, creamos el objeto DisponibilidadHoraria
                                if not disp_del_dia:
                                    id_disp = len(facilitador.disponibilidades_horarias) + 1
                                    disp_del_dia = DisponibilidadHoraria(id_disponibilidad_horaria=id_disp, dia=dia)
                                    facilitador.agregar_disponibilidad_dia(disp_del_dia)
                                
                                # 3. Por cada número de módulo, creamos el objeto y lo guardamos
                                for num_mod in modulos_de_la_hora:
                                    nuevo_modulo = ModuloDeHorario(id_modulo_de_horario=num_mod, numero_modulo=num_mod)
                                    disp_del_dia.agregar_modulo(nuevo_modulo)
                                    modulos_creados += 1

                print(f"\n✅ Éxito: Se crearon {modulos_creados} módulos de 15 min de disponibilidad en total.")
                print("-" * 50)
                if self.lista_facilitadores:
                    f_prueba = self.lista_facilitadores[0]
                    print(f"Detalle de {f_prueba.nombre} {f_prueba.apellido}:")
                    for d in f_prueba.disponibilidades_horarias:
                        print(f" - {d.dia}: Tiene {len(d.modulos)} módulos habilitados.")
                print("-" * 50, "\n")

                return True, "Carga completada"

            # ----------------------------------------------------
            # 5. CARGA DE HORARIOS DE CLASES
            # ----------------------------------------------------
            elif clave == "horarios_clases":
                if not self.lista_trayectos:
                    return False, "Debes cargar Trayectos antes de los Horarios de Clases."

                df = pd.read_csv(ruta_archivo)
                self.lista_clases = []

                # Función rápida para convertir HH:MM a número de módulo de 15 min (8:00 = 1)
                def hora_a_modulo(hora_str):
                    if pd.isna(hora_str) or type(hora_str) != str: return 0
                    partes = str(hora_str).strip().split(':')
                    if len(partes) != 2: return 0
                    hora, minutos = int(partes[0]), int(partes[1])
                    return (hora - 8) * 4 + (minutos // 15) + 1

                for indice, fila in df.iterrows():
                    # --- 1. PROCESAR SALÓN ---
                    nombre_salon = str(fila['Salon']).strip()
                    if nombre_salon.lower() == "nan": nombre_salon = "SIN ASIGNAR"
                    
                    salon = next((s for s in self.lista_salones if s.nombre == nombre_salon), None)
                    if not salon:
                        id_salon = len(self.lista_salones) + 1
                        salon = Salon(id_salon=id_salon, nombre=nombre_salon)
                        self.lista_salones.append(salon)

                    # --- 2. PROCESAR HORARIO Y MÓDULOS ---
                    dia = str(fila['Dia']).strip()
                    hora_inicio = str(fila['Hora Inicio']).strip()
                    hora_fin = str(fila['Hora Fin']).strip()
                    
                    start_mod = hora_a_modulo(hora_inicio)
                    end_mod = hora_a_modulo(hora_fin)
                    
                    id_horario = len(self.lista_horarios_clases) + 1
                    horario_clase = HorarioDeClase(id_horario_de_clase=id_horario, dia=dia)
                    
                    # Generamos los módulos intermedios
                    if start_mod > 0 and end_mod > start_mod:
                        for num_mod in range(start_mod, end_mod):
                            nuevo_modulo = ModuloDeHorario(id_modulo_de_horario=num_mod, numero_modulo=num_mod)
                            horario_clase.agregar_modulo(nuevo_modulo)
                            
                    self.lista_horarios_clases.append(horario_clase)

                    # --- 3. PROCESAR TRAYECTO ---
                    nombre_trayecto = str(fila['Trayecto']).strip()
                    nivel_trayecto = str(fila['Nivel']).strip()
                    
                    # Buscamos el trayecto cargado en memoria
                    trayecto = next((t for t in self.lista_trayectos if t.nombre == nombre_trayecto and t.nivel == nivel_trayecto), None)
                    if not trayecto:
                        # Fallback por si hay ligeras variaciones de nombre/nivel
                        trayecto = next((t for t in self.lista_trayectos if t.nombre == nombre_trayecto), None)

                    # --- 4. TIPO DE CLASE (Cálculo lógico) ---
                    tipo_str = str(fila['Tipo']).strip().upper()
                    necesita_prof_especial = str(fila['Prof Educacion Especial']).strip().upper() == "SI"
                    
                    trayectos_tpt = ["TECNOKIDS", "PEQUEBOT", "TRENDKIDS"]
                    nombre_trayecto_upper = nombre_trayecto.upper()
                    
                    if tipo_str == "SPRINT":
                        tipo_clase = 5
                    elif nombre_trayecto_upper in trayectos_tpt:
                        tipo_clase = 2 if necesita_prof_especial else 1
                    else:
                        tipo_clase = 4 if necesita_prof_especial else 3

                    # --- 5. CREAR LA CLASE ---
                    id_clase = len(self.lista_clases) + 1
                    nueva_clase = Clase(
                        id_clase=id_clase,
                        tipo_de_clase=tipo_clase,
                        salon=salon,
                        trayecto=trayecto,
                        horario_de_clase=horario_clase
                    )
                    self.lista_clases.append(nueva_clase)

                print(f"\n✅ Éxito: Se cargaron {len(self.lista_clases)} clases en memoria.")
                print("-" * 50)
                for c in self.lista_clases[:4]:
                    print(c)
                    print(f"   -> Módulos que abarca: {[m.numero_modulo for m in c.horario_de_clase.modulos]}")
                print("... y más ...")
                print("-" * 50, "\n")

                return True, "Carga completada"

            # Si la clave no coincide con ninguna
            return False, "Clave de archivo no reconocida."
            
        except Exception as e:
            return False, f"Error al leer el archivo: {e}"

    def estan_datos_listos(self):
        # Exigimos los 5 archivos para avanzar
        return (len(self.lista_facilitadores) > 0 and 
                len(self.lista_trayectos) > 0 and 
                any(f.disponibilidad_trayecto is not None for f in self.lista_facilitadores) and
                any(len(f.disponibilidades_horarias) > 0 for f in self.lista_facilitadores) and
                len(self.lista_clases) > 0) # <-- Agregado requisito de las clases

    def tiene_datos(self, clave):
        if clave == "facilitadores":
            return len(self.lista_facilitadores) > 0
        elif clave == "trayectos":
            return len(self.lista_trayectos) > 0
        elif clave == "fac_trayectos":
            return any(f.disponibilidad_trayecto is not None for f in self.lista_facilitadores)
        elif clave == "disponibilidad":
            return any(len(f.disponibilidades_horarias) > 0 for f in self.lista_facilitadores)
        elif clave == "horarios_clases": # <-- Agregado para pintar el check ✅
            return len(self.lista_clases) > 0
            
        return False