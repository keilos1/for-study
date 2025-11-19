import pandas as pd
import numpy as np


def series_data(name, index):
    # Создаем список всех целых положительных нечетных чисел меньших 1000
    odd_numbers = [i for i in range(1, 1000, 2)]

    # Создаем Series с индексами, начинающимися с 1
    s = pd.Series(odd_numbers, index=range(1, len(odd_numbers) + 1))
    s.name = name

    # Применяем преобразования начиная с заданного индекса
    for i in range(index, len(s) + 1):
        if i % 2 == 1:  # нечетный индекс
            s.iloc[i - 1] = s.iloc[i - 1] * 5
        else:  # четный индекс
            s.iloc[i - 1] = s.iloc[i - 1] + 7

    # Возвращаем наибольшее из чисел с индексами index, index+1, index+7
    indices_to_check = [index, index + 1, index + 7]
    values = [s.loc[i] for i in indices_to_check]

    return max(values)


def frame_data(values, indices):
    # Создаем DataFrame из values с индексами indices
    df = pd.DataFrame(values, index=indices)

    # Сортируем DataFrame по убыванию значения индекса
    df_sorted = df.sort_index(ascending=False)

    # Возвращаем значение последнего элемента второй строки после сортировки
    # Вторая строка имеет индекс 1 (так как индексация с 0)
    return df_sorted.iloc[1, -1]


def sellers(n):
    # Чтение CSV файла в DataFrame
    df = pd.read_csv('tranzaktions.csv', sep='\t')

    # Фильтрация данных для продавца с номером n
    seller_data = df[df['Продавец'] == f'seller_{n}']

    # Сумма вырученных средств продавца n
    sum_n = seller_data['Цена (млн)'].sum()

    # Среднее значение вырученных средств продавца n (округленное до целого)
    avg_n = round(seller_data['Цена (млн)'].mean())

    # Среднее значение вырученных средств продавца n для автомобилей >= 2 млн
    avg2_n = round(seller_data[seller_data['Цена (млн)'] >= 2]['Цена (млн)'].mean())

    # Возвращаем сумму всех значений
    return sum_n + avg_n + avg2_n


def analyze_transaction_data():
    # Исходные данные
    transaction = [120, -31, '20.1', 12.3, 'bank', 12, -4, -7, 150, 'mr.', 23, 32, 21]

    # Создаем Series с индексами от 10 до 22
    t = pd.Series(transaction, index=range(10, 23))

    print("Исходный Series t:")
    print(f't\n')

    # Получаем только целые числа элементы
    integer_elements = []
    for value in t:
        try:
            # Пробуем преобразовать в целое число
            int_value = int(float(value))
            # Проверяем, что после преобразования в float и обратно значение не изменилось
            if int_value == float(value):
                integer_elements.append(int_value)
        except (ValueError, TypeError):
            # Пропускаем элементы, которые нельзя преобразовать в число
            continue

    # Создаем новый Series только с целыми числами
    t_integers = pd.Series(integer_elements)

    print("Только целые числа:")
    print(f't_integers\n')

    # Вычисляем несмещенную выборочную дисперсию
    variance = t_integers.var(ddof=1)

    # Вычисляем среднее значение
    mean = t_integers.mean()

    print(f"Несмещенная выборочная дисперсия: {variance:.2f}")
    print(f"Среднее значение: {mean:.2f}")

    return t, t_integers, variance, mean


def analyze_normal_distribution():
    # Генерация 200 значений нормально распределенной случайной величины
    np.random.seed(42)
    s = pd.Series(np.random.normal(0, 1, 200))

    print("1. Первые 10 значений исходной Series s:")
    print(s.head(10))
    print(f"   Среднее: {s.mean():.4f}, Стандартное отклонение: {s.std():.4f}\n")


    # Возведение каждого значения s во 2 степень и увеличение индексов на 2
    s = s ** 2
    s.index = s.index + 2

    print("2. Первые 10 значений после преобразования (значения², индексы+2):")
    print(f'{s.head(10)}\n')

    # Количество значений s, которые больше 2
    count_greater_than_2 = (s > 2).sum()
    print(f"3. Количество значений s > 2: {count_greater_than_2}\n")

    # Сумма элементов, строго меньших 2 и имеющих нечётные индексы
    odd_indices_less_than_2 = s[(s < 2) & (s.index % 2 == 1)]
    sum_odd_indices_less_than_2 = odd_indices_less_than_2.sum()

    print(f"4. Сумма элементов < 2 с нечётными индексами: {sum_odd_indices_less_than_2:.4f}")
    print(f"   Количество таких элементов: {len(odd_indices_less_than_2)}")

    return s, count_greater_than_2, sum_odd_indices_less_than_2


def analyze_credit_card_data():
    # 1. Чтение данных
    df = pd.read_csv('CreditCardTransaction.csv')

    print("1. Данные успешно загружены")
    print(f"Размер исходной таблицы: {df.shape}")
    print(f"Колонки: {df.columns.tolist()}\n")

    # 2. Создание выборки
    np.random.seed(12)
    dfs = df.sample(n=10000, random_state=12)

    print("2. Выборка создана")
    print(f"Размер выборки: {dfs.shape}\n")

    # 3. Количество вхождений каждого департамента и топ-3
    department_counts = dfs['Department'].value_counts()
    top_3_departments = department_counts.nlargest(3)

    print("3. Топ-3 департамента по частоте:")
    print(f'{top_3_departments}\n')

    # 4. Фильтрация данных за январь или февраль 2022 года
    jan_feb_2022 = dfs[(dfs['Year'] == 2022) & (dfs['Month'].isin([1, 2]))]

    print("4. Данные за январь-февраль 2022:")
    print(f"Количество транзакций: {len(jan_feb_2022)}\n")

    # 5. Медиана сумм транзакций
    median_amount = jan_feb_2022['TrnxAmount'].median()

    print(f"5. Медиана сумм транзакций за январь-февраль 2022: {median_amount:.2f}\n")

    # 6. Добавление нового столбца
    dfs['Median_Difference'] = abs(median_amount) - abs(dfs['TrnxAmount'])

    print("6. Новый столбец 'Median_Difference' добавлен")
    print("Первые 5 строк с новым столбцом:")
    print(f'{dfs[['TrnxAmount', 'Median_Difference']].head()}\n')

    # Дополнительная информация
    print("=== ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ ===")
    print(f"Общее количество департаментов: {len(department_counts)}")
    print(f"Минимальная сумма транзакции: {dfs['TrnxAmount'].min():.2f}")
    print(f"Максимальная сумма транзакции: {dfs['TrnxAmount'].max():.2f}")
    print(f"Средняя сумма транзакции: {dfs['TrnxAmount'].mean():.2f}")

    return dfs, top_3_departments, median_amount, jan_feb_2022


# 1
print("Задание 1\n")
print(series_data('Название серии', 22))  # 285
print(series_data('Название серии', 32))  # 385

# 2
print("\nЗадание 2\n")
print(frame_data([[1,11,21], [1,2,3], [-1,-2,-3]], ['V','E','F']))  # -3
print(frame_data([[111,111,31,41,51,116], [141,15,61,6,717,160], [77,82,91,324,314,10]], ['Z','E','F']))  # 10

# 3
print("\nЗадание 3\n")
sel_n = sellers(2)
print(f"sel_n для n=2: {sel_n}") # 15.7

# 4
print("\nЗадание 4\n")
t_series, integers_series, var_result, mean_result = analyze_transaction_data()

# 5
print("\nЗадание 5\n")
s_result, count_result, sum_result = analyze_normal_distribution()

# 6
print("\nЗадание 6\n")
dfs_result, top_departments, median, jan_feb_data = analyze_credit_card_data()