import pandas as pd
from pulp import *


def load_data_from_excel(file_path):
    """Загружает данные из Excel файла"""
    xls = pd.ExcelFile(file_path)

    # Загрузка параметров
    params = pd.read_excel(xls, 'Параметры')
    alpha1 = params[params['Параметр'] == 'alpha1']['Доля древесины'].values[0]
    alpha2 = params[params['Параметр'] == 'alpha2']['Доля древесины'].values[0]

    # Проверка корректности параметров
    if not (abs((alpha1 + alpha2) - 1) < 1e-6):
        raise ValueError("Сумма долей α1 и α2 должна равняться 1")

    # Загрузка данных ЛЗП
    lzp_df = pd.read_excel(xls, 'ЛЗП')
    b = lzp_df['Максимальный объем заготовок'].tolist()
    r = lzp_df['Траты на изготовление ед.'].tolist()
    m = len(b)

    # Рассчитываем максимальные объёмы по типам древесины для каждого ЛЗП
    b_hardwood = []
    b_softwood = []
    for bi in b:
        if alpha1 == 0.5:  # Если alpha1 равно 0.5
            if bi % 2 == 1:  # Если нечётное количество
                hw = math.ceil(alpha1 * bi)
                sw = math.floor(alpha2 * bi)
            else:  # Если чётное количество
                hw = int(alpha1 * bi)
                sw = int(alpha2 * bi)
        else:
            hw = round(alpha1 * bi)
            sw = round(alpha2 * bi)

        b_hardwood.append(hw)
        b_softwood.append(sw)

    # Загрузка данных ЛПП
    lpp_df = pd.read_excel(xls, 'ЛПП')
    d1 = lpp_df['Потребность в лиственной древесине'].tolist()
    d2 = lpp_df['Потребность в хвойной древесине'].tolist()
    n = len(d1)

    # Загрузка матрицы транспортных расходов
    transport_df = pd.read_excel(xls, 'Транспортные расходы', index_col=0)
    c = transport_df.values.tolist()

    return {
        'm': m,  # Кол-во ЛЗП
        'n': n,  # Кол-во ЛПП
        'alpha1': alpha1,  # Доля лиственных деревьев
        'alpha2': alpha2,  # Доля хвойных деревьев
        'c': c,  # Матрица стоимостей перевозок
        'b': b,  # Макс. объемы заготовки по ЛЗП
        'b_hardwood': b_hardwood,  # Лимит лиственных по ЛЗП
        'b_softwood': b_softwood,  # Лимит хвойных по ЛЗП
        'r': r,  # Себестоимость заготовки по ЛЗП
        'd1': d1,  # Потребность в лиственных по ЛПП
        'd2': d2  # Потребность в хвойных по ЛПП
    }


# Загрузка данных из Excel
try:
    data = load_data_from_excel('transport_data.xlsx')
except Exception as e:
    print(f"Ошибка при загрузке данных: {e}")
    exit()

# Создаем задачу
prob = LpProblem("Timber_Transportation", LpMinimize)

# Переменные
x = []
y = []
for i in range(data['m']):
    x_row = []
    y_row = []
    for j in range(data['n']):
        x_ij = LpVariable(f"x_{i}_{j}", lowBound=0, cat='Integer')  # Целые деревья
        y_ij = LpVariable(f"y_{i}_{j}", lowBound=0, cat='Integer')  # Целые деревья
        x_row.append(x_ij)
        y_row.append(y_ij)
    x.append(x_row)
    y.append(y_row)

# Целевая функция: сумма (c_ij + r_i) * (x_ij + y_ij)
prob += lpSum(
    (data['c'][i][j] + data['r'][i]) * (x[i][j] + y[i][j])
    for i in range(data['m']) for j in range(data['n'])
)

# Ограничения:
# 1. Общий объём лиственной древесины от ЛЗП i не превышает alpha1*b_i
for i in range(data['m']):
    prob += lpSum(x[i][j] for j in range(data['n'])) <= data['b_hardwood'][i]

# 2. Общий объём хвойной древесины от ЛЗП i не превышает alpha2*b_i
for i in range(data['m']):
    prob += lpSum(y[i][j] for j in range(data['n'])) <= data['b_softwood'][i]

# 3. Потребности в лиственной древесине
for j in range(data['n']):
    prob += lpSum(x[i][j] for i in range(data['m'])) == data['d1'][j]

# 4. Потребности в хвойной древесине
for j in range(data['n']):
    prob += lpSum(y[i][j] for i in range(data['m'])) == data['d2'][j]

# Решаем
prob.solve()

# Вывод решения
print("\nСтатус решения:", LpStatus[prob.status])
print("Общие затраты:", value(prob.objective))

# Суммарная доставленная древесина по типам
total_hardwood = sum(value(x[i][j]) for i in range(data['m']) for j in range(data['n']))
total_softwood = sum(value(y[i][j]) for i in range(data['m']) for j in range(data['n']))

print("\nОптимальные объемы перевозок:")
for i in range(data['m']):
    for j in range(data['n']):
        if value(x[i][j]) > 0 or value(y[i][j]) > 0:
            print(f"ЛЗП {i+1} -> ЛПП {j+1}: "
                  f"Лиственная: {value(x[i][j])} деревьев, "
                  f"Хвойная: {value(y[i][j])} деревьев")

print("\nИтого доставлено:")
print(f"Лиственная древесина: {total_hardwood} деревьев")
print(f"Хвойная древесина: {total_softwood} деревьев")
print(f"Всего деревьев перевезено: {total_hardwood + total_softwood}")

# Проверка использования мощностей ЛЗП
print("\nИспользование мощностей ЛЗП:")
for i in range(data['m']):
    used_hardwood = sum(value(x[i][j]) for j in range(data['n']))
    used_softwood = sum(value(y[i][j]) for j in range(data['n']))
    print(f"ЛЗП {i+1}: Лиственная {used_hardwood}/{data['b_hardwood'][i]} "
          f"({used_hardwood/data['b_hardwood'][i]*100:.1f}%), "
          f"Хвойная {used_softwood}/{data['b_softwood'][i]} "
          f"({used_softwood/data['b_softwood'][i]*100:.1f}%)")