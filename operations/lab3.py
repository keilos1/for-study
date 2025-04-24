from pulp import *
import pandas as pd
import numpy as np


def load_data_from_excel(file_path):
    """Загружает данные из Excel файла"""
    # Чтение данных из Excel
    df = pd.read_excel(file_path, sheet_name='transport', header=None)

    # Извлечение данных
    supply = [df.iloc[1, 6], df.iloc[2, 6], df.iloc[3, 6]]  # Запасы
    demand = [df.iloc[4, 1], df.iloc[4, 2], df.iloc[4, 3],  # Потребности
                  df.iloc[4, 4], df.iloc[4, 5]]

    # Матрица стоимостей
    cost = np.array([
        [df.iloc[1, 1], df.iloc[1, 2], df.iloc[1, 3], df.iloc[1, 4], df.iloc[1, 5]],
        [df.iloc[2, 1], df.iloc[2, 2], df.iloc[2, 3], df.iloc[2, 4], df.iloc[2, 5]],
        [df.iloc[3, 1], df.iloc[3, 2], df.iloc[3, 3], df.iloc[3, 4], df.iloc[3, 5]]
    ])

    # Фиксированное количество груза из A2 в B1
    fixed_N = df.iloc[6, 1] if not pd.isna(df.iloc[6, 1]) else 60

    return supply, demand, cost, fixed_N


def solve_transportation(N, supply, demand, cost):
    """Решает транспортную задачу для заданного N"""
    prob = LpProblem(f"Transportation_N_{N}", LpMinimize)
    x = LpVariable.dicts("x", [(i, j) for i in range(3) for j in range(5)], lowBound=0)

    # Целевая функция - минимизация стоимости
    prob += lpSum([cost[i][j] * x[(i, j)] for i in range(3) for j in range(5)])

    # Ограничения по запасам
    for i in range(3):
        prob += lpSum([x[(i, j)] for j in range(5)]) == supply[i]

    # Ограничения по потребностям
    for j in range(5):
        prob += lpSum([x[(i, j)] for i in range(3)]) == demand[j]

    # Дополнительные условия
    prob += x[(0, 1)] == 0  # Запрет A1->B2
    prob += x[(1, 4)] == 0  # Запрет A2->B5
    prob += x[(1, 0)] == N  # Фиксированная перевозка A2->B1

    prob.solve(PULP_CBC_CMD(msg=False))

    if LpStatus[prob.status] == 'Optimal':
        # Возвращаем стоимость и матрицу перевозок
        solution = np.zeros((3, 5))
        for i in range(3):
            for j in range(5):
                solution[i, j] = value(x[(i, j)])
        return value(prob.objective), solution
    return None, None


def main():
    # Загрузка данных
    supply, demand, cost, fixed_N = load_data_from_excel('transport.xlsx')

    print("Успешно загружены данные:")
    print(f"Запасы: A1={supply[0]}, A2={supply[1]}, A3={supply[2]}")
    print(f"Потребности: B1={demand[0]}, B2={demand[1]}, B3={demand[2]}, B4={demand[3]}, B5={demand[4]}")
    print(f"\nФиксированная перевозка A2->B1: {fixed_N}")

    # Решение задачи для заданного N из файла
    total_cost, solution = solve_transportation(fixed_N, supply, demand, cost)

    if total_cost is not None:
        print("\nОптимальное решение:")
        print(f"Общая стоимость перевозок: {total_cost:.2f}")
        print("\nМатрица перевозок:")
        print("     B1  B2  B3  B4  B5")
        for i in range(3):
            print(f"A{i + 1}: {[int(solution[i, j]) for j in range(5)]}")
    else:
        print("Не удалось найти оптимальное решение.")


if __name__ == "__main__":
    main()