import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from scipy.stats import pearsonr, spearmanr, kendalltau, chi2_contingency
from statsmodels.stats.outliers_influence import variance_inflation_factor

data = pd.read_excel("iskhodnye.xlsx", sheet_name="Задание 4")
data_clean = data.replace([np.inf, -np.inf], np.nan).dropna()
X = data_clean[["X1", "X2", "X3", "X4", "X5"]]
Y = data_clean["Y"]

# 4.1 Корреляционный анализ
corr_matrix = X.corr()
print("Корреляционная матрица:\n")
print(corr_matrix.round(3))

p_values = pd.DataFrame(np.zeros((5, 5)), columns=X.columns, index=X.columns)
for col1 in X.columns:
    for col2 in X.columns:
        if col1 != col2:
            _, p_val = pearsonr(X[col1], X[col2])
            p_values.loc[col1, col2] = p_val

print("\nМатрица p-значений:\n")
print(p_values.round(3))

significant_pairs = []
for i in range(len(X.columns)):
    for j in range(i+1, len(X.columns)):
        col1, col2 = X.columns[i], X.columns[j]
        if p_values.loc[col1, col2] < 0.05:
            significant_pairs.append((col1, col2))
            plt.figure(figsize=(6, 4))
            plt.scatter(X[col1], X[col2], alpha=0.6)
            plt.xlabel(col1)
            plt.ylabel(col2)
            plt.title(f"Диаграмма рассеивания: {col1} vs {col2}")
            plt.grid(True)
            plt.show()

# 4.2 Анализ пары с максимальной корреляцией
max_corr = 0
pair = None
for col1 in X.columns:
    for col2 in X.columns:
        if col1 != col2 and abs(corr_matrix.loc[col1, col2]) > max_corr:
            max_corr = abs(corr_matrix.loc[col1, col2])
            pair = (col1, col2)

col1, col2 = pair
x1, x2 = X[col1], X[col2]

rho, p_spearman = spearmanr(x1, x2)
tau, p_kendall = kendalltau(x1, x2)
x1_binned = pd.qcut(x1, q=3, labels=False)
x2_binned = pd.qcut(x2, q=3, labels=False)
contingency_table = pd.crosstab(x1_binned, x2_binned)
chi2, p_chi2, _, _ = chi2_contingency(contingency_table)

print(f"\nПара с максимальной корреляцией: {pair}")
print(f"Коэффициент корреляции Пирсона: {max_corr:.3f}")
print(f"Коэффициент Спирмена: {rho:.3f} (p-value: {p_spearman:.3f})")
print(f"Коэффициент Кендалла: {tau:.3f} (p-value: {p_kendall:.3f})")
print(f"Критерий Хи-квадрат: p-value: {p_chi2:.3f}")

# 4.3 Линейная регрессия для каждого X
print("\nРезультаты линейной регрессии Y на каждый X:")
for col in X.columns:
    x = sm.add_constant(X[col])
    model = sm.OLS(Y, x).fit()
    print(f"\nY ~ {col}")
    print(f"R-squared: {model.rsquared:.3f}")
    print(f"Коэффициент: {model.params.iloc[1]:.3f}")
    print(f"P-value: {model.pvalues.iloc[1]:.3f}")
    print(f"Уравнение: Y = {model.params.iloc[0]:.3f} + {model.params.iloc[1]:.3f}*{col}")

# 4.4 Нелинейные регрессии
best_x = X.corrwith(Y).abs().idxmax()
x = X[best_x]
x_pos = x[x > 0]
y_pos = Y[x > 0]

print(f"\nЛучший предиктор для нелинейных моделей: {best_x}")

models = {
    "Линейная": ("Y", sm.add_constant(x_pos)),
    "Логарифмическая": ("Y", sm.add_constant(np.log(x_pos))),
    "Степенная": ("ln(Y)", sm.add_constant(np.log(x_pos))),
    "Показательная": ("ln(Y)", sm.add_constant(x_pos))
}

print(f"\nРезультаты нелинейной регрессии Y на {best_x}:")
for name, (y_label, x_data) in models.items():
    if "ln" in y_label:
        y_model = np.log(y_pos)
    else:
        y_model = y_pos
    
    model = sm.OLS(y_model, x_data).fit()
    
    print(f"\n{name} модель:")
    print(f"R-squared: {model.rsquared:.3f}")
    print("Коэффициенты:")
    for i, param in enumerate(model.params):
        if i == 0:
            print(f"  Intercept: {param:.3f}")
        else:
            print(f"  Slope: {param:.3f}")
    
    if name == "Степенная":
        print(f"Уравнение: ln(Y) = {model.params.iloc[0]:.3f} + {model.params.iloc[1]:.3f}*ln({best_x})")
    elif name == "Показательная":
        print(f"Уравнение: ln(Y) = {model.params.iloc[0]:.3f} + {model.params.iloc[1]:.3f}*{best_x}")
    else:
        print(f"Уравнение: {y_label} = {model.params.iloc[0]:.3f} + {model.params.iloc[1]:.3f}*{'ln('+best_x+')' if name == 'Логарифмическая' else best_x}")