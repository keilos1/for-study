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

# Создаем правильный объединенный датафрейм
combined_data = pd.DataFrame()

# Для каждого региона добавляем соответствующие значения Y и B
for region in ['С', 'Ю', 'Ц']:
    # Создаем временный датафрейм для текущего региона
    temp_df = pd.DataFrame({
        'Region': region,
        'Y': data[region],  # Значения Y для текущего региона
        'B': data['B']      # Соответствующие значения B
    })
    
    # Объединяем с основным датафреймом
    combined_data = pd.concat([combined_data, temp_df], ignore_index=True)

# Очистка данных:
# 1. Заменяем бесконечности на NaN
combined_data = combined_data.replace([np.inf, -np.inf], np.nan)
# 2. Удаляем строки с пропущенными значениями
combined_data = combined_data.dropna()
# 3. Проверяем, что остались данные
if combined_data.empty:
    raise ValueError("После очистки не осталось данных для анализа")

# Преобразуем категориальные переменные
combined_data['Region'] = combined_data['Region'].astype('category')
combined_data['B'] = combined_data['B'].astype('category')

# Двухфакторный ANOVA с проверкой ошибок
try:
    # Модель без взаимодействия
    model_2way = ols('Y ~ C(Region) + C(B)', data=combined_data).fit()
    anova_2way = sm.stats.anova_lm(model_2way, typ=2)
    
    # Модель с взаимодействием
    model_interaction = ols('Y ~ C(Region) * C(B)', data=combined_data).fit()
    anova_interaction = sm.stats.anova_lm(model_interaction, typ=2)
    
    print("\n" + "="*50)
    print("РЕЗУЛЬТАТЫ ДЛЯ ЗАДАЧИ 5.2:")
    print("\nДвухфакторный ANOVA без взаимодействия:")
    print(anova_2way)
    print("\nДвухфакторный ANOVA с взаимодействием:")
    print(anova_interaction)

    # Проверка значимости взаимодействия
    if "C(Region):C(B)" in anova_interaction.index:
        interaction_p = anova_interaction.loc["C(Region):C(B)", "PR(>F)"]
        print("\nВывод:", 
              "Взаимодействие значимо (p = {:.4f})".format(interaction_p) if interaction_p < 0.05 
              else "Взаимодействие незначимо (p = {:.4f})".format(interaction_p))

except Exception as e:
    print("\nОшибка при выполнении ANOVA:", str(e))
    print("\nДанные для отладки:")
    print("Размер combined_data:", combined_data.shape)
    print("Пропущенные значения:", combined_data.isna().sum())
    print("Уникальные значения Region:", combined_data['Region'].unique())
    print("Уникальные значения B:", combined_data['B'].unique())
    raise
