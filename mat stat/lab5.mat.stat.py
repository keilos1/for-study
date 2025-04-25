import pandas as pd
import statsmodels.api as sm
from statsmodels.formula.api import ols
from scipy import stats

# Загрузка данных
data = pd.read_excel("iskhodnye.xlsx", sheet_name="Задание 5")

# =============================================
# ЗАДАЧА 5.1: Проверка влияния региона (фактор A) на Y
# =============================================

# Проверяем, есть ли столбец 'Y' в данных
if 'Y' not in data.columns:
    raise ValueError("Столбец 'Y' не найден в данных. Проверьте названия столбцов.")

# Создаем DataFrame для ANOVA (преобразуем в длинный формат, если нужно)
# Предполагаем, что данные могут быть в двух форматах:
# 1) Отдельные столбцы для каждого региона ('С', 'Ю', 'Ц') и общий 'Y'
# 2) Один столбец 'Region' с метками и столбец 'Y'

if all(region in data.columns for region in ['С', 'Ю', 'Ц']):
    # Если данные в широком формате (отдельные столбцы для регионов)
    data_long = pd.melt(data,
                       value_vars=['С', 'Ю', 'Ц'],
                       var_name='Region',
                       value_name='Y_value')
    # Для ANOVA используем Y_value вместо Y
    model_1way = ols('Y_value ~ C(Region)', data=data_long).fit()
else:
    # Если данные уже в длинном формате
    if 'Region' not in data.columns:
        raise ValueError("Не найден столбец 'Region' или столбцы регионов ('С', 'Ю', 'Ц')")
    model_1way = ols('Y ~ C(Region)', data=data).fit()

anova_1way = sm.stats.anova_lm(model_1way, typ=2)

print("="*50)
print("РЕЗУЛЬТАТЫ ДЛЯ ЗАДАЧИ 5.1:")
print("Однофакторный ANOVA (влияние региона на Y):")
print(anova_1way)

# Проверка значимости
if anova_1way["PR(>F)"][0] < 0.05:
    print("\nВывод: Регион значимо влияет на Y (p = {:.4f})".format(anova_1way["PR(>F)"][0]))
else:
    print("\nВывод: Регион НЕ влияет значимо на Y (p = {:.4f})".format(anova_1way["PR(>F)"][0]))

# =============================================
# ЗАДАЧА 5.2: Проверка влияния региона (A) и фактора B на Y
# =============================================

# Проверяем наличие столбца B
if 'B' not in data.columns:
    raise ValueError("Столбец 'B' не найден в данных. Проверьте названия столбцов.")

# Для двухфакторного ANOVA используем исходный DataFrame
# (предполагаем, что он содержит 'Region' или можем создать его)
# Создаем объединенный датафрейм
regions = []
y_values = []
b_values = []

for region_col in ['С', 'Ю', 'Ц']:
    regions.extend([region_col] * len(data))
    y_values.extend(data[region_col].values)
    b_values.extend(data['B'].values)

combined_data = pd.DataFrame({
    'Region': regions,
    'Y': y_values,
    'B': b_values
}).dropna()

# Двухфакторный ANOVA без взаимодействия
model_2way = ols('Y ~ C(Region) + C(B)', data=combined_data).fit()
anova_2way = sm.stats.anova_lm(model_2way, typ=2)

# Двухфакторный ANOVA с взаимодействием
model_interaction = ols('Y ~ C(Region) * C(B)', data=combined_data).fit()
anova_interaction = sm.stats.anova_lm(model_interaction, typ=2)

print("\n" + "="*50)
print("РЕЗУЛЬТАТЫ ДЛЯ ЗАДАЧИ 5.2:")
print("\nДвухфакторный ANOVA без взаимодействия:")
print(anova_2way)
print("\nДвухфакторный ANOVA с взаимодействием:")
print(anova_interaction)

# Проверка значимости взаимодействия
interaction_p = anova_interaction["PR(>F)"][2]
if interaction_p < 0.05:
    print("\nВывод: Взаимодействие региона и фактора B значимо (p = {:.4f})".format(interaction_p))
    print("Рекомендуется использовать модель с взаимодействием.")
else:
    print("\nВывод: Взаимодействие региона и фактора B НЕзначимо (p = {:.4f})".format(interaction_p))
    print("Можно использовать модель без взаимодействия.")
