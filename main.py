import os, platform
import pulp
import time
import pandas as pd
import pprint

pp = pprint.PrettyPrinter()
if os.name == 'posix' and platform.system() == 'Linux':
    CPLEX_PATH = '/opt/ibm/ILOG/CPLEX_Studio_Community2212/cplex/bin/x86-64_linux/cplex'
elif os.name == 'nt' and platform.system() == 'Windows':
    CPLEX_PATH = '/opt/ibm/ILOG/CPLEX_Studio_Community2212/cplex/bin/x86-64_linux/cplex'
else:
    raise Exception('Unkown OS')

def menu_optimization(platos, ingredientes, nutrientes, restricciones, presupuesto, composicion):
    """
    Modelo de optimización para la planificación de menús hospitalarios con composición variable.

    Argumentos:
        platos (dict): Información de cada plato con sus costos y proporciones de nutrientes.
        ingredientes (dict): Disponibilidad y costos de los ingredientes.
        nutrientes (dict): Requerimientos mínimos y máximos de nutrientes.
        restricciones (dict): Restricciones de frecuencia y culturales.
        presupuesto (float): Presupuesto máximo semanal para los menús.
        composicion (dict): Requisitos de composición para cada comida.

    Retorna:
        dict: Resultados del modelo, incluyendo costos, asignaciones, y validación nutricional.
    """
    # Crear el problema de optimización
    prob = pulp.LpProblem("Menu_Optimization", pulp.LpMinimize)

    # Variables de decisión
    comidas = ['desayuno', 'almuerzo', 'cena']
    dias = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
    x = pulp.LpVariable.dicts("Plato", [(i, c, d) for i in platos for c in comidas for d in dias], cat="Binary")

    # Función objetivo: Minimizar el costo total
    prob += pulp.lpSum(platos[i]['costo'] * x[(i, c, d)] for i in platos for c in comidas for d in dias), "Costo_Total"

    # Restricciones de composición variable
    for c in comidas:
        for d in dias:
            for tipo, cantidad in composicion[c].items():
                prob += (pulp.lpSum(x[(i, c, d)] for i in platos if platos[i]['tipo'] == tipo) == cantidad,
                        f"Composicion_{tipo}_{c}_{d}")

    # Restricciones de frecuencia de platos
    for i in platos:
        prob += (pulp.lpSum(x[(i, c, d)] for c in comidas for d in dias) <= restricciones['frecuencia'][i],
                f"Frecuencia_{i}")

    # Restricciones de requerimientos nutricionales por comida
    # for c in comidas:
    #     for d in dias:
    #         prob += (pulp.lpSum(platos[i]['nutrientes']['calorias'] * x[(i, c, d)] for i in platos) >= nutrientes[c]['min_calorias'],
    #                 f"MinCalorias_{c}_{d}")
    #         prob += (pulp.lpSum(platos[i]['nutrientes']['calorias'] * x[(i, c, d)] for i in platos) <= nutrientes[c]['max_calorias'],
    #                 f"MaxCalorias_{c}_{d}")

    # Restricciones de nutrientes por día
    for d in dias:
        prob += (pulp.lpSum(platos[i]['nutrientes']['calorias'] * x[(i, c, d)] for i in platos for c in comidas) >= nutrientes['dia']['min_calorias'],
                f"MinCaloriasDia_{d}")
        prob += (pulp.lpSum(platos[i]['nutrientes']['calorias'] * x[(i, c, d)] for i in platos for c in comidas) <= nutrientes['dia']['max_calorias'],
                f"MaxCaloriasDia_{d}")

    # Restricción de presupuesto
    prob += (pulp.lpSum(platos[i]['costo'] * x[(i, c, d)] for i in platos for c in comidas for d in dias) <= presupuesto,
            "Presupuesto")

    # Resolver el problema
    start_time = time.time()
    prob.solve(pulp.CPLEX(path=CPLEX_PATH, msg=True))
    end_time = time.time()

    # Verificar el estado del modelo
    if prob.status != 1:
        print(f"Modelo infactible o no resuelto. Estado: {pulp.LpStatus[prob.status]}")
        prob.writeLP("debug_model.lp")  # Exportar el modelo para análisis
        return {
            'status': pulp.LpStatus[prob.status],
            'costo_total': None,
            'platos_seleccionados': {},
            'tiempo_computacional': end_time - start_time,
            'mensaje': "El modelo no encontró solución factible. Verifique las restricciones y parámetros."
        }

    # Resultados
    resultados = {
        'status': pulp.LpStatus[prob.status],
        'costo_total': pulp.value(prob.objective),
        'platos_seleccionados': {
            (i, c, d): x[(i, c, d)].varValue for i in platos for c in comidas for d in dias if x[(i, c, d)].varValue > 0.5
        },
        'tiempo_computacional': end_time - start_time
    }

    return resultados

# Ejemplo de uso
platos = {
    'Entrada1': {'costo': 300, 'nutrientes': {'calorias': 100, 'proteinas': 5}, 'ingredientes': {'lechuga': 20, 'zanahoria': 10}, 'tipo': 'entrada'},
    'Entrada2': {'costo': 350, 'nutrientes': {'calorias': 120, 'proteinas': 6}, 'ingredientes': {'palta': 15, 'tomate': 25}, 'tipo': 'entrada'},
    'Principal1': {'costo': 800, 'nutrientes': {'calorias': 600, 'proteinas': 35}, 'ingredientes': {'pollo': 150, 'arroz': 100}, 'tipo': 'principal'},
    'Principal2': {'costo': 750, 'nutrientes': {'calorias': 550, 'proteinas': 30}, 'ingredientes': {'carne': 200, 'papas': 150}, 'tipo': 'principal'},
    'Acomp1': {'costo': 200, 'nutrientes': {'calorias': 150, 'proteinas': 3}, 'ingredientes': {'pure': 100}, 'tipo': 'acompanamiento'},
    'Acomp2': {'costo': 220, 'nutrientes': {'calorias': 180, 'proteinas': 4}, 'ingredientes': {'ensalada': 80}, 'tipo': 'acompanamiento'},
    'Postre1': {'costo': 150, 'nutrientes': {'calorias': 100, 'proteinas': 2}, 'ingredientes': {'manzana': 50}, 'tipo': 'postre'},
    'Postre2': {'costo': 180, 'nutrientes': {'calorias': 120, 'proteinas': 3}, 'ingredientes': {'pera': 60}, 'tipo': 'postre'}
}

ingredientes = {
    'lechuga': 500, 'zanahoria': 300, 'palta': 200, 'tomate': 400,
    'pollo': 1000, 'arroz': 700, 'carne': 800, 'papas': 600,
    'pure': 500, 'ensalada': 400, 'manzana': 300, 'pera': 200
}

datos_composicion = {
    'desayuno': {'entrada': 0, 'principal': 1, 'postre': 1, 'acompanamiento': 0},
    'almuerzo': {'entrada': 1, 'principal': 1, 'postre': 1, 'acompanamiento': 1},
    'cena': {'entrada': 0, 'principal': 1, 'postre': 1, 'acompanamiento': 0}
}

datos_nutrientes = {
    # 'desayuno': {'min_calorias': 300, 'max_calorias': 400},
    # 'almuerzo': {'min_calorias': 800, 'max_calorias': 1000},
    # 'cena': {'min_calorias': 600, 'max_calorias': 700},
    'dia': {'min_calorias': 2200, 'max_calorias': 2700}
}

datos_restricciones = {
    'frecuencia': {
        'Entrada1': 11, 'Entrada2': 11,
        'Principal1': 11, 'Principal2': 11,
        'Acomp1': 11, 'Acomp2': 11,
        'Postre1': 11, 'Postre2': 11
    }
}

presupuesto = 5000000

# Llamar a la función con datos de prueba
resultados = menu_optimization(platos, ingredientes, datos_nutrientes, datos_restricciones, presupuesto, datos_composicion)
pp.pprint(resultados)
