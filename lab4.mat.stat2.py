# Импорт необходимых библиотек
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.graphics.gofplots import qqplot

# Настройка отображения
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
plt.style.use('seaborn')
plt.rcParams['figure.figsize'] = (10, 6)

# 1. Загрузка и очистка данных
print("1. ЗАГРУЗКА И ОЧИСТКА ДАННЫХ")
data = pd.read_excel('ishodnye.xlsx', sheet_name='Задание 4')

# Очистка данных
def clean_data(df):
    # Замена бесконечностей на NaN
    df = df.replace([np.inf, -np.inf], np.nan)
    # Удаление строк с пропусками
    df = df.dropna()
    return df

data_clean = clean_data(data)
print(f"\nИсходное количество строк: {len(data)}")
print(f"Количество строк после очистки: {len(data_clean)}")
print("\nПервые 5 строк очищенных данных:")
print(data_clean.head())

# 2. Корреляционный анализ
print("\n2. КОРРЕЛЯЦИОННЫЙ АНАЛИЗ")
X = data_clean[['X1', 'X2', 'X3', 'X4', 'X5']]

# Корреляционная матрица Пирсона
corr_matrix = X.corr(method='pearson')
print("\nКорреляционная матрица (Пирсон):")
print(corr_matrix)

# Визуализация корреляционной матрицы
plt.figure()
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1, center=0)
plt.title('Корреляционная матрица Пирсона для X1-X5')
plt.show()

# Расчет p-values и диаграммы рассеивания для значимых пар
print("\nДиаграммы рассеивания для значимых пар (p < 0.05):")
p_values = np.zeros((5, 5))
for i in range(5):
    for j in range(5):
        if i != j:
            corr, pval = stats.pearsonr(X.iloc[:, i], X.iloc[:, j])
            p_values[i, j] = pval
            if pval < 0.05 and i < j:
                plt.figure()
                sns.scatterplot(x=X.iloc[:, i], y=X.iloc[:, j])
                plt.title(f'{X.columns[i]} vs {X.columns[j]} (r = {corr:.2f}, p = {pval:.3f})')
                plt.show()

# 3. Анализ пары с наибольшей корреляцией
print("\n3. АНАЛИЗ ПАРЫ С НАИБОЛЬШЕЙ КОРРЕЛЯЦИЕЙ")
max_corr = 0
pair = (0, 1)
for i in range(5):
    for j in range(i+1, 5):
        if abs(corr_matrix.iloc[i, j]) > max_corr:
            max_corr = abs(corr_matrix.iloc[i, j])
            pair = (i, j)

x1, x2 = X.columns[pair[0]], X.columns[pair[1]]
print(f"\nПара с наибольшей корреляцией: {x1} и {x2} (r = {max_corr:.3f})")

# Проверка гипотез о независимости
print("\nРезультаты тестов:")
spearman = stats.spearmanr(X[x1], X[x2])
print(f"Спирмен: rho = {spearman.correlation:.3f}, p = {spearman.pvalue:.4f}")

kendall = stats.kendalltau(X[x1], X[x2])
print(f"Кендалл: tau = {kendall.correlation:.3f}, p = {kendall.pvalue:.4f}")

# Хи-квадрат тест
bins = 5
x1_cat = pd.cut(X[x1], bins=bins, labels=False)
x2_cat = pd.cut(X[x2], bins=bins, labels=False)
contingency_table = pd.crosstab(x1_cat, x2_cat)
chi2, p, _, _ = stats.chi2_contingency(contingency_table)
print(f"Хи-квадрат: χ² = {chi2:.3f}, p = {p:.4f}")

# 4. Линейная регрессия Y на X1-X5
print("\n4. ЛИНЕЙНАЯ РЕГРЕССИЯ Y на X1-X5")
X_lin = sm.add_constant(X)
model_lin = sm.OLS(data_clean['Y'], X_lin).fit()
print(model_lin.summary())

# Анализ мультиколлинеарности
print("\nПроверка на мультиколлинеарность (VIF):")
vif_data = pd.DataFrame()
vif_data["Переменная"] = X_lin.columns
vif_data["VIF"] = [variance_inflation_factor(X_lin.values, i) for i in range(X_lin.shape[1])]
print(vif_data)

# График предсказанных vs наблюдаемых значений
plt.figure()
plt.scatter(data_clean['Y'], model_lin.predict(X_lin), alpha=0.6)
plt.plot([data_clean['Y'].min(), data_clean['Y'].max()], 
         [data_clean['Y'].min(), data_clean['Y'].max()], 'r--')
plt.xlabel('Наблюдаемые Y')
plt.ylabel('Предсказанные Y')
plt.title('Линейная модель: предсказанные vs наблюдаемые')
plt.show()

# Анализ остатков
residuals = model_lin.resid
print("\nАнализ остатков:")
print(f"Среднее: {residuals.mean():.4f}")
print(f"Стандартное отклонение: {residuals.std():.4f}")

plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
sns.histplot(residuals, kde=True, bins=20)
plt.title('Распределение остатков')

plt.subplot(1, 2, 2)
qqplot(residuals, line='s', ax=plt.gca())
plt.title('Q-Q plot остатков')
plt.tight_layout()
plt.show()

# 5. Нелинейные регрессии
print("\n5. НЕЛИНЕЙНЫЕ РЕГРЕССИИ")

# Логарифмическая модель
print("\nЛогарифмическая модель (линеаризация X):")
X_log = X.apply(lambda x: np.log(x + 1e-9))  # Добавляем малое значение для избежания log(0)
X_log = sm.add_constant(X_log)
model_log = sm.OLS(data_clean['Y'], X_log).fit()
print(model_log.summary())

# Степенная модель
print("\nСтепенная модель (линеаризация X и Y):")
X_pow = X.apply(lambda x: np.log(x + 1e-9))
y_pow = np.log(data_clean['Y'] + 1e-9)
X_pow = sm.add_constant(X_pow)
model_pow = sm.OLS(y_pow, X_pow).fit()
print(model_pow.summary())

# Коэффициенты степенной модели в исходной форме
print("\nКоэффициенты степенной модели (Y = a * X1^b1 * X2^b2 * ...):")
print(f"a = {np.exp(model_pow.params['const']):.4f}")
for col in ['X1', 'X2', 'X3', 'X4', 'X5']:
    print(f"{col}: {model_pow.params[col]:.4f}")

# Показательная модель
print("\nПоказательная модель (линеаризация Y):")
X_exp = sm.add_constant(X)
y_exp = np.log(data_clean['Y'] + 1e-9)
model_exp = sm.OLS(y_exp, X_exp).fit()
print(model_exp.summary())

# Коэффициенты показательной модели в исходной форме
print("\nКоэффициенты показательной модели (Y = a * exp(b1*X1 + b2*X2 + ...)):")
print(f"a = {np.exp(model_exp.params['const']):.4f}")
for col in ['X1', 'X2', 'X3', 'X4', 'X5']:
    print(f"{col}: {model_exp.params[col]:.4f}")

# 6. Сравнение моделей
print("\n6. СРАВНЕНИЕ МОДЕЛЕЙ")
models = {
    'Линейная': model_lin,
    'Логарифмическая': model_log,
    'Степенная': model_pow,
    'Показательная': model_exp
}

comparison = pd.DataFrame({
    'Модель': models.keys(),
    'R²': [m.rsquared for m in models.values()],
    'Adj. R²': [m.rsquared_adj for m in models.values()],
    'AIC': [m.aic for m in models.values()],
    'BIC': [m.bic for m in models.values()],
    'Кол-во наблюдений': [m.nobs for m in models.values()]
})

print("\nСравнение моделей:")
print(comparison.to_string(index=False))

# Визуализация сравнения R²
plt.figure()
sns.barplot(x='Модель', y='R²', data=comparison)
plt.title('Сравнение R² для разных моделей')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
