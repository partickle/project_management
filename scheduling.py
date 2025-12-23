#!/usr/bin/env python3
"""
Решение задачи планирования (Фаза 5)
Проект: Мобильная игра "Цифровой кузнечик"

Допущения:
- 1 рабочий день = 8 часов
- Команда: 1 PM, 1 BE, 1 FE (по одному человеку каждой роли)
- Длительность задачи = max(PM_hours, BE_hours, FE_hours) / 8 дней
- Потребность в ресурсе = 1, если роль задействована (часы > 0)
- Задачи внутри одного этапа могут выполняться параллельно,
  но зависят от завершения ключевых предшественников
"""

import random
from typing import List, Tuple, Callable
from utility import calculate_critical_times, ActivityListSampler, ActivityListDecoder, successors_by_predecessors

# Фиксируем seed для воспроизводимости
random.seed(42)

# =============================================================================
# ВХОДНЫЕ ДАННЫЕ ИЗ ОТЧЁТА
# =============================================================================

# Названия задач (индекс 0 - Start, индекс 23 - Finish - фиктивные)
TASK_NAMES = [
    "0. Start (фиктивная)",                          # 0
    "1. Анализ требований и юз-кейсов",              # 1
    "2. Проектирование архитектуры приложения",      # 2
    "3. Проектирование структуры БД (SQLite)",       # 3
    "4. Проектирование экранов",                     # 4
    "5. Настройка окружения для ведения разработки", # 5
    "6. Реализация логики игрового поля",            # 6
    "7. Реализация правил игры",                     # 7
    "8. Реализация логики игровых уровней",          # 8
    "9. CRUD уровней",                               # 9
    "10. Реализация логики сбора и агрегации статистики", # 10
    "11. CRUD статистики",                           # 11
    "12. Создание встроенных уровней",               # 12
    "13. Реализация алгоритма генерации уровней",    # 13
    "14. Реализация экрана правил игры",             # 14
    "15. Реализация экрана просмотра статистики",    # 15
    "16. Реализация экрана главного меню",           # 16
    "17. Реализация экрана настроек",                # 17
    "18. Реализация экрана выбора уровней",          # 18
    "19. Реализация экрана генерации уровня",        # 19
    "20. Реализация экрана игры",                    # 20
    "21. Тестирование игры",                         # 21
    "22. Публикация игры в стор",                    # 22
    "23. Finish (фиктивная)",                        # 23
]

# Принадлежность к этапам
STAGES = {
    1: [1, 2, 3, 4, 5],      # Этап 1: Инициация и проектирование
    2: [6, 7, 8, 9, 10, 11, 12, 13],  # Этап 2: Бэк часть
    3: [14, 15, 16, 17, 18, 19, 20],   # Этап 3: Фронт часть
    4: [21, 22],            # Этап 4: Финальная часть
}

# Трудозатраты (человеко-часы) из отчёта: [PM, BE, FE]
# Индекс 0 и 23 - фиктивные задачи (Start, Finish)
LABOR_HOURS = [
    [0, 0, 0],      # 0 - Start
    [16, 6, 6],     # 1 - Анализ требований
    [10, 6, 2],     # 2 - Проектирование архитектуры
    [8, 6, 0],      # 3 - Проектирование БД
    [4, 0, 8],      # 4 - Проектирование экранов
    [1, 8, 6],      # 5 - Настройка окружения
    [1, 8, 1],      # 6 - Логика игрового поля
    [1, 8, 0],      # 7 - Правила игры
    [1, 8, 1],      # 8 - Логика игровых уровней
    [0, 4, 0],      # 9 - CRUD уровней
    [1, 10, 0],     # 10 - Логика статистики
    [0, 4, 0],      # 11 - CRUD статистики
    [4, 4, 0],      # 12 - Создание встроенных уровней
    [4, 8, 0],      # 13 - Алгоритм генерации уровней
    [1, 0, 3],      # 14 - Экран правил
    [2, 1, 6],      # 15 - Экран статистики
    [1, 0, 6],      # 16 - Экран меню
    [0, 1, 6],      # 17 - Экран настроек
    [0, 1, 6],      # 18 - Экран выбора уровней
    [0, 2, 6],      # 19 - Экран генерации уровня
    [1, 2, 6],      # 20 - Экран игры
    [8, 8, 8],      # 21 - Тестирование
    [8, 4, 1],      # 22 - Публикация
    [0, 0, 0],      # 23 - Finish
]

# =============================================================================
# ФОРМИРОВАНИЕ ЗАВИСИМОСТЕЙ ПРЕДШЕСТВОВАНИЯ
# =============================================================================
# Логика:
# - Start (0) -> все задачи этапа 1
# - Задачи этапа 1 -> Настройка окружения (5) -> Задачи этапов 2 и 3 (частично)
# - Проектирование архитектуры (2) и БД (3) -> Backend задачи
# - Проектирование экранов (4) -> Frontend задачи
# - Backend и Frontend задачи -> Тестирование (21)
# - Тестирование (21) -> Публикация (22) -> Finish (23)

predecessors = [
    [],              # 0 - Start (нет предшественников)
    [0],             # 1 - Анализ требований <- Start
    [1],             # 2 - Проект. архитектуры <- Анализ
    [1],             # 3 - Проект. БД <- Анализ
    [1],             # 4 - Проект. экранов <- Анализ
    [2, 3, 4],       # 5 - Настройка окружения <- Все проектирования
    [5, 2, 3],       # 6 - Логика поля <- Окружение, Архитектура, БД
    [6],             # 7 - Правила игры <- Логика поля
    [6],             # 8 - Логика уровней <- Логика поля
    [8],             # 9 - CRUD уровней <- Логика уровней
    [6],             # 10 - Логика статистики <- Логика поля
    [10],            # 11 - CRUD статистики <- Логика статистики
    [8, 9],          # 12 - Встроенные уровни <- Логика уровней, CRUD
    [8],             # 13 - Алгоритм генерации <- Логика уровней
    [5, 4],          # 14 - Экран правил <- Окружение, Проект. экранов
    [11, 5, 4],      # 15 - Экран статистики <- CRUD статистики, Окружение
    [5, 4],          # 16 - Экран меню <- Окружение, Проект. экранов
    [5, 4],          # 17 - Экран настроек <- Окружение, Проект. экранов
    [9, 5, 4],       # 18 - Экран выбора уровней <- CRUD уровней
    [13, 5, 4],      # 19 - Экран генерации <- Алгоритм генерации
    [7, 5, 4],       # 20 - Экран игры <- Правила игры
    [7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20], # 21 - Тестирование <- Все реализации
    [21],            # 22 - Публикация <- Тестирование
    [22],            # 23 - Finish <- Публикация
]

# =============================================================================
# ПРЕОБРАЗОВАНИЕ ТРУДОЗАТРАТ В ДЛИТЕЛЬНОСТИ И ПОТРЕБНОСТИ
# =============================================================================

def convert_to_rcpsp_data(labor_hours: List[List[int]], hours_per_day: int = 8):
    """
    Преобразование трудозатрат в длительности и ресурсные потребности.
    
    Допущения:
    - Ресурсы работают параллельно над одной задачей
    - Длительность = max(часов по ролям) / часов_в_день
    - Потребность = 1, если роль задействована
    """
    durations = []
    demands = []
    
    for hours in labor_hours:
        pm, be, fe = hours
        max_hours = max(pm, be, fe)
        
        # Длительность в днях (округляем вверх для ненулевых)
        if max_hours == 0:
            dur = 0
        else:
            dur = max(1, (max_hours + hours_per_day - 1) // hours_per_day)
        
        # Потребности: 1 если роль задействована, 0 иначе
        demand = [1 if pm > 0 else 0, 1 if be > 0 else 0, 1 if fe > 0 else 0]
        
        durations.append(dur)
        demands.append(demand)
    
    return durations, demands

# Доступность ресурсов: 1 PM, 1 BE, 1 FE
renewable_capacities = [1, 1, 1]

# Преобразуем данные
durations, renewable_demands = convert_to_rcpsp_data(LABOR_HOURS)

print("=" * 70)
print("ВХОДНЫЕ ДАННЫЕ RCPSP")
print("=" * 70)
print(f"\nЧисло задач: {len(durations)} (включая Start и Finish)")
print(f"Доступность ресурсов: PM={renewable_capacities[0]}, BE={renewable_capacities[1]}, FE={renewable_capacities[2]}")
print("\nДлительности (в рабочих днях):")
for i, (name, dur, demand) in enumerate(zip(TASK_NAMES, durations, renewable_demands)):
    if dur > 0 or i == 0 or i == len(durations)-1:
        print(f"  {i:2d}. {name[:45]:<45} | {dur:2d} дн | PM={demand[0]} BE={demand[1]} FE={demand[2]}")

# =============================================================================
# РАСЧЁТ КРИТИЧЕСКИХ ВРЕМЁН И МЕТРИК ДЛЯ ЭВРИСТИК
# =============================================================================

successors = successors_by_predecessors(predecessors)
earliest_start, latest_finish = calculate_critical_times(durations, predecessors, successors)

# Вычисление дополнительных метрик
n = len(durations)

# Поздние времена начала
latest_start = [latest_finish[i] - durations[i] + (durations[i] if durations[i] > 0 else 0) for i in range(n)]
# Корректировка: LSTi = LFTi - di, но для нашей логики LSTi = min(LSTj - dj для j в successors[i])
latest_start = [0] * n
for i in range(n-1, -1, -1):
    if i == n-1:
        latest_start[i] = earliest_start[i]
    elif successors[i]:
        latest_start[i] = min(latest_start[j] for j in successors[i]) - durations[i]
    else:
        latest_start[i] = earliest_start[i]

# Общий резерв (Total Slack)
total_slack = [latest_start[i] - earliest_start[i] for i in range(n)]

# Ранние времена окончания
earliest_finish = [earliest_start[i] + durations[i] for i in range(n)]

# Свободный резерв (Free Slack)
free_slack = [0] * n
for i in range(n):
    if successors[i]:
        free_slack[i] = min(earliest_start[j] for j in successors[i]) - earliest_finish[i]
    else:
        free_slack[i] = 0

# Суммарные затраты ресурсов
total_demands = [sum(renewable_demands[i]) for i in range(n)]

print("\n" + "=" * 70)
print("КРИТИЧЕСКИЕ ВРЕМЕНА")
print("=" * 70)
print(f"\nEarliest Start (ES): {earliest_start}")
print(f"Latest Finish (LF):  {latest_finish}")
print(f"Latest Start (LS):   {latest_start}")
print(f"Total Slack (SLK):   {total_slack}")
print(f"Free Slack (FREE):   {free_slack}")

# =============================================================================
# ОПРЕДЕЛЕНИЕ ЭВРИСТИК
# =============================================================================

def make_slk_rule():
    """SLK - по возрастанию общего резерва"""
    return lambda j: total_slack[j]

def make_free_rule():
    """FREE - по возрастанию свободного резерва"""
    return lambda j: free_slack[j]

def make_lst_rule():
    """LST - по возрастанию позднего времени начала"""
    return lambda j: latest_start[j]

def make_lft_rule():
    """LFT - по возрастанию позднего времени завершения"""
    return lambda j: latest_finish[j]

def make_lstlft_rule():
    """LSTLFT - по возрастанию суммы LS + LF"""
    return lambda j: latest_start[j] + latest_finish[j]

def make_grpw_rule():
    """GRPW - по убыванию суммарной длительности задачи и её прямых последователей"""
    def rule(j):
        succ_duration = sum(durations[s] for s in successors[j])
        return durations[j] + succ_duration
    return rule

def make_lpt_rule():
    """LPT - по убыванию длительности"""
    return lambda j: durations[j]

def make_mis_rule():
    """MIS - по убыванию числа прямых последователей"""
    return lambda j: len(successors[j])

def make_grd_rule():
    """GRD - по убыванию произведения длительности и суммарных затрат ресурсов"""
    return lambda j: durations[j] * total_demands[j]

def make_grwc_rule():
    """GRWC - по убыванию суммарных затрат ресурсов"""
    return lambda j: total_demands[j]

def make_gcrwc_rule():
    """GCRWC - по убыванию суммарных затрат ресурсов задачи и её прямых последователей"""
    def rule(j):
        succ_demands = sum(total_demands[s] for s in successors[j])
        return total_demands[j] + succ_demands
    return rule

def make_rot_rule():
    """ROT - по убыванию суммы отношений затрат ресурсов к запасам, делённой на длительность"""
    def rule(j):
        if durations[j] == 0:
            return 0
        ratio_sum = sum(
            renewable_demands[j][k] / renewable_capacities[k] if renewable_capacities[k] > 0 else 0
            for k in range(len(renewable_capacities))
        )
        return ratio_sum / durations[j]
    return rule

# Список эвристик с названиями и направлениями
HEURISTICS = [
    ("SLK", make_slk_rule(), "min"),
    ("FREE", make_free_rule(), "min"),
    ("LST", make_lst_rule(), "min"),
    ("LFT", make_lft_rule(), "min"),
    ("LSTLFT", make_lstlft_rule(), "min"),
    ("GRPW", make_grpw_rule(), "max"),
    ("LPT", make_lpt_rule(), "max"),
    ("MIS", make_mis_rule(), "max"),
    ("GRD", make_grd_rule(), "max"),
    ("GRWC", make_grwc_rule(), "max"),
    ("GCRWC", make_gcrwc_rule(), "max"),
    ("ROT", make_rot_rule(), "max"),
]

# =============================================================================
# ГЕНЕРАЦИЯ И ОЦЕНКА РЕШЕНИЙ
# =============================================================================

sampler = ActivityListSampler(predecessors, successors)
decoder = ActivityListDecoder()

def evaluate_solution(activity_list: List[int]) -> Tuple[List[int], int]:
    """Декодирует Activity List и возвращает расписание и makespan"""
    start_times = decoder.decode(activity_list, durations, predecessors, renewable_demands, renewable_capacities)
    finish_times = [start_times[i] + durations[i] for i in range(len(durations))]
    makespan = max(finish_times)
    return start_times, makespan

print("\n" + "=" * 70)
print("РЕЗУЛЬТАТЫ ЭВРИСТИК")
print("=" * 70)

heuristic_results = []

for name, rule, direction in HEURISTICS:
    if direction == "min":
        activity_list = sampler.generate_by_min_rule(rule)
    else:
        activity_list = sampler.generate_by_max_rule(rule)
    
    start_times, makespan = evaluate_solution(activity_list)
    heuristic_results.append((name, activity_list, start_times, makespan))
    print(f"\n{name:8s} (по {'возрастанию' if direction == 'min' else 'убыванию'}): makespan = {makespan} дней")
    # print(f"  Activity List: {activity_list}")

# =============================================================================
# СЛУЧАЙНЫЕ РЕШЕНИЯ
# =============================================================================

NUM_RANDOM = 5000
print(f"\n" + "=" * 70)
print(f"СЛУЧАЙНЫЕ РЕШЕНИЯ (N = {NUM_RANDOM})")
print("=" * 70)

random_makespans = []
best_random_makespan = float('inf')
best_random_solution = None
best_random_start_times = None

for i in range(NUM_RANDOM):
    activity_list = sampler.generate_random()
    start_times, makespan = evaluate_solution(activity_list)
    random_makespans.append(makespan)
    
    if makespan < best_random_makespan:
        best_random_makespan = makespan
        best_random_solution = activity_list
        best_random_start_times = start_times

print(f"\nЛучший makespan среди случайных: {best_random_makespan} дней")
print(f"Средний makespan: {sum(random_makespans)/len(random_makespans):.2f} дней")
print(f"Худший makespan: {max(random_makespans)} дней")

# =============================================================================
# ВЫБОР ЛУЧШЕГО РЕШЕНИЯ
# =============================================================================

print("\n" + "=" * 70)
print("СВОДКА РЕЗУЛЬТАТОВ")
print("=" * 70)

all_results = heuristic_results + [("RANDOM_BEST", best_random_solution, best_random_start_times, best_random_makespan)]

print(f"\n{'Метод':<12} | {'Makespan (дни)':<15}")
print("-" * 30)

sorted_results = sorted(all_results, key=lambda x: x[3])
for name, al, st, ms in sorted_results:
    marker = " *" if ms == sorted_results[0][3] else ""
    print(f"{name:<12} | {ms:<15}{marker}")

best_name, best_activity_list, best_start_times, best_makespan = sorted_results[0]
print(f"\n{'='*70}")
print(f"ЛУЧШЕЕ РЕШЕНИЕ: {best_name} с makespan = {best_makespan} рабочих дней")
print("="*70)

# =============================================================================
# ДЕТАЛЬНОЕ РАСПИСАНИЕ ЛУЧШЕГО РЕШЕНИЯ
# =============================================================================

print("\n" + "=" * 70)
print("ДЕТАЛЬНОЕ РАСПИСАНИЕ (ЛУЧШЕЕ РЕШЕНИЕ)")
print("=" * 70)

# Вычисляем finish times
finish_times = [best_start_times[i] + durations[i] for i in range(len(durations))]

print(f"\n{'№':<3} | {'Задача':<45} | {'Начало':<8} | {'Конец':<8} | {'Длит.':<6}")
print("-" * 80)

for i in range(len(durations)):
    if i == 0 or i == len(durations) - 1:
        continue  # Пропускаем фиктивные
    name = TASK_NAMES[i][:45]
    print(f"{i:<3} | {name:<45} | {best_start_times[i]:<8} | {finish_times[i]:<8} | {durations[i]:<6}")

# =============================================================================
# "НАТЯГИВАНИЕ" НА 8-ЧАСОВОЙ РАБОЧИЙ ГРАФИК
# =============================================================================

print("\n" + "=" * 70)
print("КАЛЕНДАРНЫЙ ПЛАН (8 часов/день, 5 дней/неделя)")
print("=" * 70)

# Преобразуем рабочие дни в недели
HOURS_PER_DAY = 8
DAYS_PER_WEEK = 5

print(f"\nОбщий срок проекта: {best_makespan} рабочих дней")
print(f"                    = {best_makespan / DAYS_PER_WEEK:.1f} рабочих недель")
print(f"                    = ~{best_makespan * HOURS_PER_DAY} часов")

# Сроки по этапам
print("\nСроки по этапам:")
for stage_num, task_indices in STAGES.items():
    stage_start = min(best_start_times[i] for i in task_indices)
    stage_finish = max(finish_times[i] for i in task_indices)
    stage_duration = stage_finish - stage_start
    print(f"  Этап {stage_num}: дни {stage_start:3d} - {stage_finish:3d} (длительность: {stage_duration} дн. = {stage_duration/DAYS_PER_WEEK:.1f} нед.)")

# Пример календарной даты
from datetime import date, timedelta

def add_working_days(start_date: date, working_days: int) -> date:
    """Добавляет рабочие дни к дате (пропуская выходные)"""
    current = start_date
    days_added = 0
    while days_added < working_days:
        current += timedelta(days=1)
        if current.weekday() < 5:  # Понедельник = 0, ..., Пятница = 4
            days_added += 1
    return current

# Условная дата начала проекта
PROJECT_START = date(2025, 1, 13)  # Понедельник

print(f"\nПример календарного плана (старт: {PROJECT_START.strftime('%d.%m.%Y')}):")
print(f"\n{'Этап':<10} | {'Начало':<12} | {'Конец':<12} | {'Рабочих дней':<12}")
print("-" * 50)

for stage_num, task_indices in STAGES.items():
    stage_start_day = min(best_start_times[i] for i in task_indices)
    stage_finish_day = max(finish_times[i] for i in task_indices)
    
    cal_start = add_working_days(PROJECT_START, stage_start_day - 1) if stage_start_day > 0 else PROJECT_START
    cal_finish = add_working_days(PROJECT_START, stage_finish_day - 1)
    
    print(f"Этап {stage_num:<5} | {cal_start.strftime('%d.%m.%Y'):<12} | {cal_finish.strftime('%d.%m.%Y'):<12} | {stage_finish_day - stage_start_day:<12}")

project_end = add_working_days(PROJECT_START, best_makespan - 1)
print(f"\nПлановое завершение проекта: {project_end.strftime('%d.%m.%Y')}")

# =============================================================================
# ВЫВОД ДАННЫХ ДЛЯ ОТЧЁТА
# =============================================================================

print("\n" + "=" * 70)
print("ДАННЫЕ ДЛЯ ОТЧЁТА")
print("=" * 70)

print("\n--- Зависимости предшествования (predecessors) ---")
print("Формат: номер_задачи: [предшественники]")
for i in range(len(predecessors)):
    if i > 0 and i < len(predecessors) - 1:
        pred_str = ", ".join(str(p) for p in predecessors[i]) if predecessors[i] else "—"
        print(f"  {i:2d}: [{pred_str}]")

print("\n--- Activity List (лучшее решение) ---")
print([i for i in best_activity_list if i != 0 and i != len(durations)-1])

print("\n--- Расписание для таблицы ---")
for i in range(1, len(durations) - 1):
    print(f"{i}\t{best_start_times[i]}\t{finish_times[i]}\t{durations[i]}")
