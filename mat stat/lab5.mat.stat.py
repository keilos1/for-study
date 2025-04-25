import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.formula.api import ols

# Загрузка данных
data = pd.read_excel("iskhodnye.xlsx", sheet_name="Задание 5")

# Проверяем наличие нужных столбцов
required_columns = ['С', 'Ю', 'Ц', 'B']
missing_cols = [col for col in required_columns if col not in data.columns]
if missing_cols:
    raise ValueError(f"Не хватает столбцов: {missing_cols}")

# Преобразуем широкий формат в длинный (для ANOVA по регионам)
data_long = pd.melt(
    data,
    value_vars=['С', 'Ю', 'Ц'],
    var_name='Region',
    value_name='Y_value'
)

# Удаляем NaN и бесконечности
data_long = data_long.replace([np.inf, -np.inf], np.nan).dropna()

# =============================================
# ЗАДАЧА 5.1: ANOVA для регионов (С, Ю, Ц)
# =============================================
model_1way = ols('Y_value ~ C(Region)', data=data_long).fit()
anova_1way = sm.stats.anova_lm(model_1way, typ=2)

print("=" * 50)
print("РЕЗУЛЬТАТЫ ДЛЯ ЗАДАЧИ 5.1:")
print(anova_1way)
if anova_1way.loc["C(Region)", "PR(>F)"] < 0.05:
    print(f"\nВывод: Регион значимо влияет на Y (p={anova_1way.loc['C(Region)', 'PR(>F)']:.4f})")
else:
    print(f"\nВывод: Регион НЕ оказывает значимого влияния на Y (p={anova_1way.loc['C(Region)', 'PR(>F)']:.4f})")

# =============================================
# ЗАДАЧА 5.2: Двухфакторный ANOVA (Регион + B)
# =============================================
# Создаем объединенный датафрейм
combined_data = pd.DataFrame()
for region in ['С', 'Ю', 'Ц']:
    temp_df = pd.DataFrame({
        'Region': region,
        'Y': data[region],
        'B': data['B']
    })
    combined_data = pd.concat([combined_data, temp_df], ignore_index=True)

# Очистка данных
combined_data = combined_data.replace([np.inf, -np.inf], np.nan).dropna()

# Группируем B в 5 категорий для устойчивости анализа
combined_data['B_group'] = pd.cut(combined_data['B'], bins=5)

print("\n" + "=" * 50)
print("РЕЗУЛЬТАТЫ ДЛЯ ЗАДАЧИ 5.2:")

try:
    # Модель без взаимодействия
    model_main = ols('Y ~ C(Region) + C(B_group)', data=combined_data).fit()
    anova_main = sm.stats.anova_lm(model_main, typ=2)

    # Модель с взаимодействием
    model_interaction = ols('Y ~ C(Region) * C(B_group)', data=combined_data).fit()
    anova_interaction = sm.stats.anova_lm(model_interaction, typ=2)

    # Вывод результатов
    print("\nОсновные эффекты:")
    print(anova_main[['sum_sq', 'df', 'F', 'PR(>F)']])

    print("\nЭффекты взаимодействия:")
    print(anova_interaction[['sum_sq', 'df', 'F', 'PR(>F)']])

    # Анализ значимости
    print("\nВыводы:")

    # 1. Проверка значимости регионов
    region_p = anova_main.loc["C(Region)", "PR(>F)"]
    if region_p < 0.05:
        print(f"- Регион значимо влияет на Y (p={region_p:.4f})")
    else:
        print(f"- Регион НЕ оказывает значимого влияния на Y (p={region_p:.4f})")

    # 2. Проверка значимости фактора B
    b_p = anova_main.loc["C(B_group)", "PR(>F)"]
    if b_p < 0.05:
        print(f"- Фактор B значимо влияет на Y (p={b_p:.4f})")
    else:
        print(f"- Фактор B НЕ оказывает значимого влияния на Y (p={b_p:.4f})")

    # 3. Проверка взаимодействия
    if "C(Region):C(B_group)" in anova_interaction.index:
        interaction_p = anova_interaction.loc["C(Region):C(B_group)", "PR(>F)"]
        if interaction_p < 0.05:
            print(f"- Обнаружено значимое взаимодействие между регионом и фактором B (p={interaction_p:.4f})")
        else:
            print(f"- Взаимодействие между регионом и фактором B незначимо (p={interaction_p:.4f})")

except Exception as e:
    print(f"\nОшибка при выполнении ANOVA: {str(e)}")
