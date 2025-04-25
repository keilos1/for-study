import pandas as pd
import statsmodels.api as sm
from statsmodels.formula.api import ols
from scipy import stats
import numpy as np

# Загрузка данных
data = pd.read_excel("iskhodnye.xlsx", sheet_name="Задание 5")

# =============================================
# ЗАДАЧА 5.1: Влияние региона (A) на Y
# =============================================

# Преобразуем в длинный формат (С, Ю, Ц -> Region/Y)
data_long = pd.melt(data,
                    value_vars=['С', 'Ю', 'Ц'],
                    var_name='Region',
                    value_name='Y_value')

# Удаляем пропущенные значения
data_long = data_long.dropna()
print(data_long)
# Однофакторный ANOVA
model_1way = ols('Y_value ~ C(Region)', data=data_long).fit()
anova_1way = sm.stats.anova_lm(model_1way, typ=2)

print("=" * 50)
print("РЕЗУЛЬТАТЫ ДЛЯ ЗАДАЧИ 5.1:")
print(anova_1way)
print("\nВывод:", "Регион значимо влияет на Y" if anova_1way["PR(>F)"][0] < 0.05
else "Регион НЕ влияет на Y", f"(p = {anova_1way['PR(>F)'][0]:.4f})")

# =============================================
# ЗАДАЧА 5.2: Влияние A (регион) и B на Y
# =============================================

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
print(combined_data)
# Двухфакторный ANOVA
formula = 'Y ~ C(Region) + C(B)'  # Без взаимодействия
# formula = 'Y ~ C(Region) * C(B)'  # С взаимодействием

try:
    model = ols(formula, data=combined_data).fit()
    anova = sm.stats.anova_lm(model, typ=2)

    print("\n" + "=" * 50)
    print("РЕЗУЛЬТАТЫ ДЛЯ ЗАДАЧИ 5.2:")
    print(anova)

    if "C(Region):C(B)" in anova.index:
        interaction_p = anova.loc["C(Region):C(B)", "PR(>F)"]
        print("\nВзаимодействие:", "значимо" if interaction_p < 0.05
        else "незначимо", f"(p = {interaction_p:.4f})")

except Exception as e:
    print("\nОшибка в ANOVA:", str(e))
    print("Проверьте данные на пропущенные значения или выбросы")
