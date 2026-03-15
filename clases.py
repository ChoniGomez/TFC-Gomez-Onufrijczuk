
class Persona:
    def __init__(self, nombre, apellido, dni):
        self.nombre = str(nombre).strip()
        self.apellido = str(apellido).strip()
        self.dni = str(dni).strip()

# NUEVA CLASE: TipoFacilitador
class TipoFacilitador:
    def __init__(self, id_tipo, nombre):
        self.id_tipo = int(id_tipo)
        self.nombre = str(nombre)

class Facilitador(Persona):
    def __init__(self, nombre, apellido, dni, id_facilitador, cantidad_horas_cumplir, tipo_facilitador):
        super().__init__(nombre, apellido, dni)
        self.id_facilitador = int(id_facilitador)
        self.cantidad_horas_cumplir = int(cantidad_horas_cumplir)
        self.tipo_facilitador = tipo_facilitador 
        self.disponibilidad_trayecto = None 
        
        # NUEVO: Lista de objetos DisponibilidadHoraria (uno por cada día de la semana)
        self.disponibilidades_horarias = [] 

    # Agregamos un método limpio para añadir la disponibilidad del día
    def agregar_disponibilidad_dia(self, disponibilidad_dia):
        self.disponibilidades_horarias.append(disponibilidad_dia)

    def __repr__(self):
        # Actualizamos el print para ver cuántos días tiene cargados
        cantidad = len(self.disponibilidad_trayecto.trayectos) if self.disponibilidad_trayecto else 0
        return f"<Facilitador: {self.nombre} | Horas: {self.cantidad_horas_cumplir} | Trayectos: {cantidad} | Días Disp: {len(self.disponibilidades_horarias)}>"
    
class TipoTrayecto:
    def __init__(self, id_tipo, nombre):
        self.id_tipo = int(id_tipo)
        self.nombre = str(nombre).strip()

class Trayecto:
    def __init__(self, id_trayecto, nombre, nivel, tipo_trayecto):
        self.id_trayecto = int(id_trayecto)
        self.nombre = str(nombre).strip()
        self.nivel = str(nivel).strip()  # "Básico" o "Avanzado"
        
        # Aquí guardamos el OBJETO de la clase TipoTrayecto
        self.tipo_trayecto = tipo_trayecto

    def __repr__(self):
        return f"<Trayecto ID: {self.id_trayecto} | {self.nombre} ({self.nivel}) | Tipo: {self.tipo_trayecto.nombre}>"

class DisponibilidadTrayecto:
    def __init__(self, id_disponibilidad_trayecto):
        self.id_disponibilidad_trayecto = int(id_disponibilidad_trayecto)
        # Aquí guardaremos la lista de objetos Trayecto
        self.trayectos = [] 

    def agregar_trayecto(self, trayecto):
        self.trayectos.append(trayecto)

    def __repr__(self):
        return f"<Disponibilidad ID: {self.id_disponibilidad_trayecto} | Total trayectos: {len(self.trayectos)}>"
    
class ModuloDeHorario:
    def __init__(self, id_modulo_de_horario, numero_modulo):
        self.id_modulo_de_horario = int(id_modulo_de_horario)
        self.numero_modulo = int(numero_modulo)

    def __repr__(self):
        # Muestra algo como [M12] en la consola
        return f"[M{self.numero_modulo}]"

class DisponibilidadHoraria:
    def __init__(self, id_disponibilidad_horaria, dia):
        self.id_disponibilidad_horaria = int(id_disponibilidad_horaria)
        self.dia = str(dia).strip()
        # Aquí guardaremos los módulos (ej: del 1 al 4 para las 8:00)
        self.modulos = [] 

    def agregar_modulo(self, modulo):
        self.modulos.append(modulo)

    def __repr__(self):
        return f"<{self.dia}: {len(self.modulos)} módulos habilitados>"

# --- clases.py (Agrega esto al final) ---

class Salon:
    def __init__(self, id_salon, nombre):
        self.id_salon = int(id_salon)
        self.nombre = str(nombre).strip()

    def __repr__(self):
        return f"<Salón: {self.nombre}>"


class HorarioDeClase:
    def __init__(self, id_horario_de_clase, dia):
        self.id_horario_de_clase = int(id_horario_de_clase)
        self.dia = str(dia).strip()
        self.modulos = []  # Lista de objetos ModuloDeHorario

    def agregar_modulo(self, modulo):
        self.modulos.append(modulo)

    def __repr__(self):
        # Muestra algo como <Lunes | 6 módulos>
        return f"<{self.dia} | {len(self.modulos)} módulos>"


class Clase:
    def __init__(self, id_clase, tipo_de_clase, salon, trayecto, horario_de_clase):
        self.id_clase = int(id_clase)
        self.tipo_de_clase = int(tipo_de_clase)
        self.salon = salon
        self.trayecto = trayecto
        self.horario_de_clase = horario_de_clase
        
        # Facilitadores que se asignarán después con tu Algoritmo (Hormigas)
        self.facilitador_1 = None
        self.facilitador_2 = None
        self.facilitador_complementario = None
        self.profesor_educacion_especial = None

    def __repr__(self):
        nombre_trayecto = self.trayecto.nombre if self.trayecto else "Sin Trayecto"
        nombre_salon = self.salon.nombre if self.salon else "Sin Salón"
        return f"<Clase ID: {self.id_clase} | Tipo: {self.tipo_de_clase} | {nombre_trayecto} | {nombre_salon} | {self.horario_de_clase.dia}>"