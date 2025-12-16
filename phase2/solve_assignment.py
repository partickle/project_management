#!/usr/bin/env python3
"""
Решение задачи распределения работ Фазы 3 
с использованием Pyomo (MILP оптимизация)

Команда: Путилин М., Овсянников А., Сапегин П.
Проект: "Цифровой кузнечик"
"""

from pyomo.environ import *
import json

# ==============================================================================
# ШАГ 1: WBS - Декомпозиция задач Фазы 3 на подзадачи
# ==============================================================================

wbs_tasks = {
    # Родительская задача MAG-15: Написать юз кейсы
    "MAG-15.1": {"name": "Сбор требований и изучение формата UC", "parent": "MAG-15"},
    "MAG-15.2": {"name": "Черновик 10+ Use Cases (основные сценарии)", "parent": "MAG-15"},
    "MAG-15.3": {"name": "Альтернативные и негативные сценарии", "parent": "MAG-15"},
    "MAG-15.4": {"name": "Ревью и финальные правки UC", "parent": "MAG-15"},
    
    # Родительская задача MAG-19: Оценка COSMIC
    "MAG-19.1": {"name": "Изучение методологии COSMIC", "parent": "MAG-19"},
    "MAG-19.2": {"name": "Таблица движений данных (E/X/R/W)", "parent": "MAG-19"},
    "MAG-19.3": {"name": "Подсчёт CFP и валидация результатов", "parent": "MAG-19"},
    
    # Родительская задача MAG-21: Оценка UCP
    "MAG-21.1": {"name": "Расчёт UAW и UUCW", "parent": "MAG-21"},
    "MAG-21.2": {"name": "Оценка TCF и EF факторов", "parent": "MAG-21"},
    "MAG-21.3": {"name": "Расчёт UCP и пересчёт в трудозатраты", "parent": "MAG-21"},
    
    # Родительская задача MAG-22: Экспертная оценка 
    "MAG-22.1": {"name": "Подготовка к покер-планированию", "parent": "MAG-22"},
    "MAG-22.2": {"name": "Проведение сессии оценки (Planning Poker)", "parent": "MAG-22"},
    "MAG-22.3": {"name": "Агрегация оценок и согласование результатов", "parent": "MAG-22"},
    
    # Родительская задача MAG-37: Выводы
    "MAG-37.1": {"name": "Сравнительный анализ методов оценки", "parent": "MAG-37"},
    "MAG-37.2": {"name": "Определение команды/сроков/тяжёлых фич", "parent": "MAG-37"},
    "MAG-37.3": {"name": "Написание итогового текста выводов", "parent": "MAG-37"},
    
    # Родительская задача MAG-42: Изучить 4 и 5 фазы
    "MAG-42.1": {"name": "Выжимка требований 4 и 5 фаз", "parent": "MAG-42"},
    "MAG-42.2": {"name": "Анализ рисков и связей между фазами", "parent": "MAG-42"},
    "MAG-42.3": {"name": "План действий на следующие фазы", "parent": "MAG-42"},
    
    # Организационные задачи
    "ORG-01": {"name": "Координационная встреча команды", "parent": "ORG"},
    "ORG-02": {"name": "Оформление итогового отчёта Фазы 3", "parent": "ORG"},
}

# ==============================================================================
# ШАГ 2: Экспертная оценка трудоёмкости (часы)
# Метод: упрощённый Planning Poker с 3-точечной оценкой → медиана
# ==============================================================================

# Оценки трудоёмкости в часах от каждого участника
effort_estimates = {
    # Задача: [Путилин, Овсянников, Сапегин]
    "MAG-15.1": [2, 2, 2],
    "MAG-15.2": [4, 5, 4],
    "MAG-15.3": [3, 3, 2],
    "MAG-15.4": [2, 2, 2],
    
    "MAG-19.1": [2, 2, 2],
    "MAG-19.2": [3, 4, 3],
    "MAG-19.3": [2, 2, 2],
    
    "MAG-21.1": [2, 2, 2],
    "MAG-21.2": [2, 3, 2],
    "MAG-21.3": [2, 2, 2],
    
    "MAG-22.1": [1, 2, 1],
    "MAG-22.2": [3, 3, 3],  # Совместная работа
    "MAG-22.3": [2, 2, 2],
    
    "MAG-37.1": [2, 2, 2],
    "MAG-37.2": [2, 2, 2],
    "MAG-37.3": [3, 3, 3],
    
    "MAG-42.1": [2, 2, 2],
    "MAG-42.2": [2, 2, 2],
    "MAG-42.3": [2, 2, 2],
    
    "ORG-01": [1, 1, 1],
    "ORG-02": [3, 3, 3],
}

# Итоговая трудоёмкость: медиана оценок
effort = {task: sorted(estimates)[1] for task, estimates in effort_estimates.items()}

# ==============================================================================
# ШАГ 3: Матрица предпочтений для подзадач
# Базовые предпочтения из отчёта + наследование для подзадач
# ==============================================================================

# Исходные предпочтения верхнего уровня (из отчёта)
base_prefs = {
    # Задача: [Путилин, Овсянников, Сапегин]
    "MAG-15": [5, 3, 9],
    "MAG-19": [6, 5, 6],
    "MAG-21": [6, 5, 6],
    "MAG-22": [10, 6, 2],
    "MAG-37": [8, 9, 6],
    "MAG-42": [8, 9, 8],
    "ORG": [6, 7, 6],  # Организационные задачи - усреднённое
}

# Предпочтения для подзадач (наследуем от родительских с небольшими вариациями)
pref = {}
for task, info in wbs_tasks.items():
    parent = info["parent"]
    base = base_prefs[parent]
    # Небольшая вариация для разнообразия
    if task.endswith(".1"):  # Подготовительные задачи
        pref[task] = [max(0, b-1) for b in base]
    elif task.endswith(".3"):  # Завершающие задачи
        pref[task] = [min(10, b+1) for b in base]
    else:
        pref[task] = base.copy()
    
    # Специфические корректировки
    if "ORG" in task:
        pref[task] = [6, 7, 6]

# Корректировки на основе специфики задач
pref["MAG-22.2"] = [10, 7, 4]  # Совместная сессия - выше у всех
pref["ORG-02"] = [5, 8, 5]    # Оформление - Овсянников ответственный за Фазу 2

# ==============================================================================
# ШАГ 4 и 5: Модель оптимизации и решение (линейная версия)
# ==============================================================================

# Исполнители
workers = ["Путилин М.", "Овсянников А.", "Сапегин П."]
worker_indices = {w: i for i, w in enumerate(workers)}

tasks = list(wbs_tasks.keys())

# Создаём модель Pyomo
model = ConcreteModel("TaskAssignment")

# Множества
model.N = Set(initialize=workers, doc="Исполнители")
model.T = Set(initialize=tasks, doc="Задачи")

# Параметры
model.effort = Param(model.T, initialize=effort, doc="Трудоёмкость задач (часы)")
model.pref = Param(model.N, model.T, initialize=lambda m, n, t: pref[t][worker_indices[n]], doc="Предпочтения")

# Переменные
model.x = Var(model.N, model.T, domain=Binary, doc="Назначение задачи исполнителю")
model.maxLoad = Var(domain=NonNegativeReals, doc="Максимальная нагрузка")

# Границы для нормировки
total_effort = sum(effort.values())
Lmin = total_effort / len(workers)  # Идеальная равная нагрузка
Lmax = total_effort
Pmin = min(min(v) for v in pref.values())
Pmax = max(max(v) for v in pref.values())
maxTotalPref = sum(max(pref[t]) for t in tasks)  # Верхняя граница суммарного предпочтения

# Ограничения
def assign_constraint(m, t):
    """Каждая задача назначена ровно одному исполнителю"""
    return sum(m.x[n, t] for n in m.N) == 1
model.AssignConstr = Constraint(model.T, rule=assign_constraint)

def max_load_constraint(m, n):
    """Определение максимальной нагрузки"""
    return sum(m.effort[t] * m.x[n, t] for t in m.T) <= m.maxLoad
model.MaxLoadConstr = Constraint(model.N, rule=max_load_constraint)

def min_tasks_constraint(m, n):
    """Каждому исполнителю минимум 5 задач (для справедливости)"""
    return sum(m.x[n, t] for t in m.T) >= 5
model.MinTasksConstr = Constraint(model.N, rule=min_tasks_constraint)

# Целевая функция: линейная свёртка
# Минимизируем maxLoad и максимизируем суммарное предпочтение
# f1 = (maxLoad - Lmin) / (Lmax - Lmin)  [0..1] - хотим минимизировать
# f2 = totalPref / maxTotalPref [0..1] - хотим максимизировать, значит минимизируем (1 - f2)
alpha = 0.5  # вес для баланса нагрузки
beta = 0.5   # вес для предпочтений

def objective_rule(m):
    f1 = (m.maxLoad - Lmin) / (Lmax - Lmin + 1e-6)
    total_pref = sum(m.pref[n, t] * m.x[n, t] for n in m.N for t in m.T)
    f2 = 1 - total_pref / (maxTotalPref + 1e-6)  # инвертируем для минимизации
    return alpha * f1 + beta * f2

model.Obj = Objective(rule=objective_rule, sense=minimize)

# Решение
solver = SolverFactory('glpk')
results = solver.solve(model, tee=False)

# ==============================================================================
# Извлечение и вывод результатов
# ==============================================================================

print("=" * 70)
print("РЕЗУЛЬТАТЫ РЕШЕНИЯ ЗАДАЧИ РАСПРЕДЕЛЕНИЯ РАБОТ")
print("=" * 70)

# Назначения
assignments = {}
for n in model.N:
    assignments[n] = []
    for t in model.T:
        if value(model.x[n, t]) > 0.5:
            assignments[n].append(t)

# Метрики по исполнителям
print("\n### Сводка по исполнителям ###\n")
worker_stats = {}
for n in model.N:
    load_val = sum(effort[t] for t in assignments[n])
    if assignments[n]:
        avg_pref = sum(pref[t][worker_indices[n]] for t in assignments[n]) / len(assignments[n])
        total_pref_n = sum(pref[t][worker_indices[n]] for t in assignments[n])
    else:
        avg_pref = 0
        total_pref_n = 0
    worker_stats[n] = {
        "tasks": assignments[n],
        "load": load_val,
        "avg_pref": round(avg_pref, 2),
        "total_pref": total_pref_n,
        "count": len(assignments[n])
    }
    print(f"{n}:")
    print(f"  Задач: {len(assignments[n])}")
    print(f"  Нагрузка: {load_val} часов")
    print(f"  Среднее предпочтение: {avg_pref:.2f}")
    print(f"  Суммарное предпочтение: {total_pref_n}")
    print()

print("\n### Детальное распределение ###\n")
print(f"{'Задача':<12} {'Название':<50} {'Исполнитель':<16} {'Часы':>6} {'Пред.':>6}")
print("-" * 95)
for t in tasks:
    for n in model.N:
        if value(model.x[n, t]) > 0.5:
            print(f"{t:<12} {wbs_tasks[t]['name']:<50} {n:<16} {effort[t]:>6} {pref[t][worker_indices[n]]:>6}")
            break

print("\n### Метрики оптимизации ###\n")
print(f"Максимальная нагрузка: {value(model.maxLoad):.1f} часов")
total_pref_all = sum(pref[t][worker_indices[n]] for n in model.N for t in tasks if value(model.x[n, t]) > 0.5)
print(f"Суммарное предпочтение (всего): {total_pref_all}")
print(f"Идеальная равная нагрузка (Lmin): {Lmin:.1f} часов")
print(f"Общая трудоёмкость: {total_effort} часов")

# Минимальное среднее предпочтение (для отчёта)
min_avg_pref = min(worker_stats[n]["avg_pref"] for n in workers)
print(f"Минимальное среднее предпочтение среди исполнителей: {min_avg_pref:.2f}")

# Сохранение результатов для отчёта
results_data = {
    "assignments": {n: assignments[n] for n in model.N},
    "worker_stats": {n: worker_stats[n] for n in workers},
    "effort": effort,
    "pref": pref,
    "wbs_tasks": wbs_tasks,
    "effort_estimates": effort_estimates,
    "base_prefs": base_prefs,
    "workers": workers,
    "maxLoad": value(model.maxLoad),
    "minAvgPref": min_avg_pref,
    "totalPref": total_pref_all,
    "Lmin": Lmin,
    "total_effort": total_effort,
    "alpha": alpha,
    "beta": beta,
}

with open('/home/claude/work/optimization_results.json', 'w', encoding='utf-8') as f:
    json.dump(results_data, f, ensure_ascii=False, indent=2)

print("\n✓ Результаты сохранены в optimization_results.json")
