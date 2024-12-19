import pulp
import time
import pandas as pd

def menu_optimization(platos, ingredientes, nutrientes, restricciones, presupuesto):
    """
    Modelo de optimización para la planificación de menús hospitalarios.

    Argumentos:
        platos (dict): Información de cada plato con sus costos y proporciones de nutrientes.
        ingredientes (dict): Disponibilidad y costos de los ingredientes.
        nutrientes (dict): Requerimientos mínimos y máximos de nutrientes.
        restricciones (dict): Restricciones de frecuencia, variedad y cultura.
        presupuesto (float): Presupuesto máximo semanal para los menús.

    Retorna:
        dict: Resultados del modelo, incluyendo costos, asignaciones, y validación nutricional.
    """
    # Crear el problema de optimización
    prob = pulp.LpProblem("Menu_Optimization", pulp.LpMinimize)

    # Variables de decisión
    x = pulp.LpVariable.dicts("Plato", platos.keys(), cat="Binary")

    # Función objetivo: Minimizar el costo total
    prob += pulp.lpSum(platos[i]['costo'] * x[i] for i in platos), "Costo_Total"

    # Restricciones de composición de colaciones
    if 'composicion' in restricciones:
        for tipo, minimo in restricciones['composicion'].items():
            prob += (pulp.lpSum(x[i] for i in platos if platos[i].get('tipo') == tipo) >= minimo,
                    f"Composicion_Minima_{tipo}")

    # Restricciones de frecuencia de platos
    if 'frecuencia' in restricciones:
        for plato, freq in restricciones['frecuencia'].items():
            prob += (x[plato] <= freq, f"Frecuencia_{plato}")

    # Restricciones de requerimientos nutricionales
    for nutriente, (min_val, max_val) in nutrientes.items():
        prob += (pulp.lpSum(platos[i]['nutrientes'][nutriente] * x[i] for i in platos) >= min_val,
                f"Requerimiento_Minimo_{nutriente}")
        prob += (pulp.lpSum(platos[i]['nutrientes'][nutriente] * x[i] for i in platos) <= max_val,
                f"Requerimiento_Maximo_{nutriente}")

    # Restricción de presupuesto
    prob += (pulp.lpSum(platos[i]['costo'] * x[i] for i in platos) <= presupuesto, "Presupuesto")

    # Restricciones culturales y gastronómicas
    if 'culturales' in restricciones:
        for cultural_restriction, value in restricciones['culturales'].items():
            prob += (pulp.lpSum(x[i] for i in value['platos']) >= value['min'],
                    f"Restriccion_Cultural_{cultural_restriction}")

    # Resolver el problema
    start_time = time.time()
    prob.solve(pulp.CPLEX(path="/opt/ibm/ILOG/CPLEX_Studio_Community2212/cplex/bin/x86-64_linux/cplex", msg=True))
    end_time = time.time()

    # Verificar el estado del modelo
    if prob.status != 1:
        print(f"Modelo infactible o no resuelto. Estado: {pulp.LpStatus[prob.status]}")
        prob.writeLP("debug_model.lp")  # Exportar el modelo para análisis
        return {
            'status': pulp.LpStatus[prob.status],
            'costo_total': None,
            'platos_seleccionados': {},
            'nutrientes_cubiertos': {},
            'tiempo_computacional': end_time - start_time,
            'mensaje': "El modelo no encontró solución factible. Verifique las restricciones y parámetros."
        }

    # Resultados
    resultados = {
        'status': pulp.LpStatus[prob.status],
        'costo_total': pulp.value(prob.objective),
        'platos_seleccionados': {i: x[i].varValue for i in platos if x[i].varValue and x[i].varValue > 0.5},
        'nutrientes_cubiertos': {
            nutriente: sum(platos[i]['nutrientes'][nutriente] * x[i].varValue for i in platos)
            for nutriente in nutrientes
        },
        'tiempo_computacional': end_time - start_time
    }

    return resultados

# Definir las 10 instancias de ejemplos
instancias = [
    {
        'id': 1,
        'platos': {
            'Plato1': {'costo': 550, 'nutrientes': {'calorias': 320, 'proteinas': 25}, 'ingredientes': {'arroz': 120, 'pollo': 80}, 'tipo': 'principal'},
            'Plato2': {'costo': 400, 'nutrientes': {'calorias': 280, 'proteinas': 15}, 'ingredientes': {'pasta': 90, 'queso': 50}, 'tipo': 'entrada'},
            'Plato3': {'costo': 450, 'nutrientes': {'calorias': 300, 'proteinas': 18}, 'ingredientes': {'lentejas': 100, 'zanahoria': 40}, 'tipo': 'postre'}
        },
        'ingredientes': {'arroz': 600, 'pollo': 400, 'pasta': 500, 'queso': 300, 'lentejas': 400, 'zanahoria': 200},
        'nutrientes': {'calorias': (2100, 2600), 'proteinas': (70, 110)},
        'restricciones': {
            'frecuencia': {'Plato1': 2, 'Plato2': 3, 'Plato3': 2},
            'composicion': {'principal': 1, 'entrada': 1, 'postre': 1}
        },
        'presupuesto': 7000
    },
    {
        'id': 2,
        'platos': {
            'Plato4': {'costo': 600, 'nutrientes': {'calorias': 400, 'proteinas': 30}, 'ingredientes': {'pollo': 150, 'papas': 100}, 'tipo': 'principal'},
            'Plato5': {'costo': 500, 'nutrientes': {'calorias': 350, 'proteinas': 20}, 'ingredientes': {'arroz': 100, 'verduras': 50}, 'tipo': 'entrada'},
            'Plato6': {'costo': 450, 'nutrientes': {'calorias': 300, 'proteinas': 25}, 'ingredientes': {'quinoa': 90, 'zapallo': 40}, 'tipo': 'postre'}
        },
        'ingredientes': {'pollo': 500, 'papas': 300, 'arroz': 400, 'verduras': 200, 'quinoa': 300, 'zapallo': 150},
        'nutrientes': {'calorias': (2200, 2700), 'proteinas': (80, 120)},
        'restricciones': {
            'frecuencia': {'Plato4': 3, 'Plato5': 2, 'Plato6': 2},
            'composicion': {'principal': 1, 'entrada': 1, 'postre': 1}
        },
        'presupuesto': 7500
    }
]

# Ejecutar todas las instancias y recolectar resultados
resultados_totales = []
for instancia in instancias:
    resultados = menu_optimization(
        platos=instancia['platos'],
        ingredientes=instancia['ingredientes'],
        nutrientes=instancia['nutrientes'],
        restricciones=instancia['restricciones'],
        presupuesto=instancia['presupuesto']
    )
    resultados['instancia_id'] = instancia['id']
    resultados_totales.append(resultados)

# Generar un DataFrame con los resultados
df_resultados = pd.DataFrame([
    {
        'Instancia': r['instancia_id'],
        'Costo Total': r['costo_total'],
        'Tiempo Computacional (s)': r['tiempo_computacional'],
        'Platos Seleccionados': r['platos_seleccionados'],
        'Nutrientes Cubiertos': r['nutrientes_cubiertos'],
        'Mensaje': r.get('mensaje', 'Solución encontrada correctamente')
    }
    for r in resultados_totales
])

# Mostrar resultados
print(df_resultados)
