# Sistema Híbrido de Optimización de Horarios Académicos

**Trabajo Final de Carrera (TFC)** para la obtención del título de Ingeniero en Informática.

---

- **Titulo:** Optimización de la planificación de horarios y recursos en la Escuela de Robótica de Misiones mediante algoritmos genéticos y de colonia de hormigas.
- **Autores:** Gomez, Jonathan Matias & Onufrijczuk, Juan Marcos.
- **Director:** Esp. Ing. Berger, Javier.
- **Codirector:** Mgtr. Ing. Pedrazzini, Liliana.
- **Carrera:** Ingeniería en Informática (Plan 2017).
- **Universidad:** Universidad Gastón Dachary (UGD).
- **Año:** 2026.

---

## Resumen

Este proyecto aborda el complejo problema de la planificación y asignación automática de horarios académicos. El objetivo principal es desarrollar una herramienta de software capaz de generar una grilla horaria óptima, asignando facilitadores a las distintas clases y trayectos educativos, mientras se satisface un conjunto extenso y heterogéneo de restricciones operativas, contractuales y pedagógicas.

Para resolver este problema de optimización combinatoria (NP-hard), se ha implementado un **algoritmo metaheurístico híbrido** que sinergiza dos técnicas de Inteligencia Artificial:

1.  **Optimización por Colonia de Hormigas (OCH):** Utilizada en la fase inicial para construir un conjunto de soluciones (población inicial) de alta calidad. Los agentes (hormigas) construyen soluciones de forma heurística, depositando feromonas para guiar a futuras hormigas hacia las mejores decisiones de asignación.
2.  **Algoritmo Genético (AG):** Empleado para evolucionar y refinar la población inicial generada por OCH. A través de operadores genéticos como la selección, cruza y mutación, el AG explora el espacio de soluciones de manera eficiente para converger hacia un óptimo global o cercano a él.

El sistema está desarrollado en Python y cuenta con una interfaz gráfica de usuario (IGU) construida con Tkinter para facilitar la carga de datos, la configuración de parámetros y la visualización de resultados.

## Descripción del Problema

La asignación manual de horarios en instituciones educativas es una tarea ardua, propensa a errores y que consume una cantidad significativa de tiempo. El planificador debe considerar simultáneamente múltiples variables, tales como:

- Disponibilidad horaria de cada facilitador.
- Competencias y especializaciones para cada curso o trayecto.
- Carga horaria máxima estipulada en los contratos.
- Reglas pedagógicas sobre la conformación de parejas docentes.
- Requisitos específicos para ciertos tipos de clases (ej. Sprints, clases con apoyo de un profesor de educación special).
- Evitar conflictos de horario para un mismo facilitador o salón.

La automatización de este proceso no solo reduce la carga administrativa, sino que también permite encontrar soluciones de mayor calidad, más justas y eficientes.

## Arquitectura de la Solución

El sistema se estructura en los siguientes módulos principales:

1.  **Gestor de Datos:** Responsable de la carga, validación y estructuración de los datos de entrada desde archivos CSV. Convierte los datos en un modelo de objetos para su manipulación.
2.  **Motor de Optimización Híbrido:**
    - **Fase 1 (OCH):** Genera una población inicial de cromosomas (soluciones). Cada hormiga construye un horario completo aplicando filtros y una función de atractivo que combina una heurística (preferencia por facilitadores con menos carga) y el rastro de feromonas.
    - **Fase 2 (AG):** Toma la población inicial y la somete a un ciclo evolutivo.
      - **Evaluación:** Cada cromosoma es evaluado mediante una **función de aptitud** que cuantifica la calidad de la solución, penalizando el incumplimiento de las restricciones.
      - **Selección:** Se seleccionan los mejores individuos para la siguiente generación mediante una combinación de elitismo, torneo y ruleta.
      - **Cruza:** Se combinan los genes de los individuos seleccionados para generar nueva descendencia.
      - **Mutación:** Se introducen cambios aleatorios en los cromosomas para mantener la diversidad genética y evitar el estancamiento en óptimos locales.
3.  **Módulo de Restricciones:** Contiene la implementación vectorizada (usando NumPy) de todas las reglas del negocio. La evaluación se realiza de forma masiva sobre toda la población para mayor eficiencia.
4.  **Interfaz Gráfica (GUI):** Permite al usuario interactuar con el sistema, cargar archivos, configurar los parámetros de los algoritmos y visualizar los resultados, incluyendo un gráfico de la evolución de la aptitud y la opción de exportar el horario final.

### Restricciones Implementadas

La función de aptitud penaliza las siguientes violaciones:

- **FR1 (Choques de horario):** Un facilitador no puede estar en dos lugares al mismo tiempo.
- **FR2 (Disponibilidad horaria):** Las asignaciones deben respetar la disponibilidad declarada por el facilitador.
- **FR3 (Horas semanales):** La carga horaria asignada no debe exceder las horas de contrato del facilitador.
- **FR4 (Liderazgo en Sprints):** Un facilitador necesita experiencia previa en un trayecto para impartir un "Sprint" de ese mismo trayecto.
- **FR5 (Límite de Sprints):** Un facilitador no puede ser asignado a más de un número determinado de Sprints.
- **FR6 (PEE obligatorio):** Las clases que lo requieren deben tener un Profesor de Educación Especial asignado.
- **FR7 (Compatibilidad de parejas):** Se evitan parejas pedagógicas con perfiles incompatibles (ej. dos técnicos en una clase que requiere un técnico y un pedagogo).
- **FR8 (Competencia en trayecto):** El facilitador debe ser competente para el trayecto que se le asigna.

## Tecnologías Utilizadas

- **Lenguaje:** Python 3.x
- **Librerías Principales:**
  - **NumPy:** Para cálculos matriciales y vectorización de las operaciones, fundamental para el rendimiento del Algoritmo Genético.
  - **Pandas:** Para la lectura y manipulación eficiente de los archivos de datos CSV.
  - **Tkinter:** Para la construcción de la interfaz gráfica de usuario.
  - **Matplotlib:** Para la visualización de datos y la generación del gráfico de evolución.

## Instalación y Puesta en Marcha

1.  **Prerrequisitos:**
    - Tener instalado Python 3.8 o superior.
    - Se recomienda el uso de un entorno virtual (`venv`).

2.  **Clonar el Repositorio (Ejemplo):**

    ```bash
    git clone https://github.com/usuario/tfc-optimizador-horarios.git
    cd tfc-optimizador-horarios
    ```

3.  **Crear y Activar Entorno Virtual (Recomendado):**

    ```bash
    python -m venv venv
    # En Windows
    .\venv\Scripts\activate
    # En macOS/Linux
    source venv/bin/activate
    ```

4.  **Instalar Dependencias:**
    El archivo `requirements.txt` contiene todas las librerías necesarias.
    ```bash
    pip install -r requirements.txt
    ```

## Guía de Uso

1.  **Ejecutar la Aplicación:**

    ```bash
    python main.py
    ```

2.  **Pantalla de Carga:**
    - Haga clic en cada botón para cargar los archivos CSV correspondientes. El sistema requiere 5 archivos:
      - `facilitadores.csv`: Datos personales y contractuales de los facilitadores.
      - `trayectos.csv`: Catálogo de cursos y trayectos ofrecidos.
      - `facilitadores - trayectos.csv`: Matriz de competencias (qué facilitador puede dar qué trayecto).
      - `disponiblidad horaria.csv`: Grilla de disponibilidad de cada facilitador.
      - `horas clases.csv`: La demanda de clases a cubrir, con sus horarios y salones.
    - Un ícono "✅" confirmará la carga exitosa de cada archivo.
    - Una vez cargados todos los archivos, presione **"Siguiente →"**.

3.  **Pantalla del Algoritmo:**
    - Ajuste los parámetros de OCH y AG según sea necesario. Los valores por defecto están configurados para un buen rendimiento general.
    - Presione **"Ejecutar Algoritmo"** para iniciar el proceso de optimización.
    - El gráfico de la izquierda mostrará la evolución de la aptitud de la población en tiempo real. Los datos de la ejecución se actualizarán a la derecha.

4.  **Resultados:**
    - Al finalizar el proceso, se mostrará un resumen con la aptitud final y el tiempo total.
    - Presione **"Exportar Horarios"** para guardar la mejor solución encontrada en un nuevo archivo CSV.

---
