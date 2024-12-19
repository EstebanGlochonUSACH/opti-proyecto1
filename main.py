import os, platform, json, sys
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
datos = json.load(open(sys.argv[1], 'r'))

# Llamar a la función con datos de prueba
resultados = menu_optimization(
    datos["platos"],
    datos["ingredientes"],
    datos["nutrientes"],
    datos["restricciones"],
    datos["presupuesto"],
    datos["composicion"]
)
print('')
pp.pprint(resultados)
