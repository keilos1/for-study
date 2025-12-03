import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import BaggingClassifier, RandomForestClassifier, StackingClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, classification_report, confusion_matrix, ConfusionMatrixDisplay
import lightgbm as lgb
import xgboost as xgb
import warnings
warnings.filterwarnings('ignore')

# Загрузка данных (первые 50 000 записей)
df = pd.read_csv('creditcard.csv').head(50000)

# Разделение на признаки и целевую переменную
X = df.drop('Class', axis=1)
y = df['Class']

# Разделение на train/test
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)

print(f"Размер train: {X_train.shape}")
print(f"Размер test: {X_test.shape}")
print(f"Доля мошеннических в train: {y_train.mean():.4f}")
print(f"Доля мошеннических в test: {y_test.mean():.4f}")

# Задание 1: Сравнение моделей
print("\nЗадание 1: Сравнение моделей\n")

dt = DecisionTreeClassifier(random_state=42, class_weight='balanced')
dt.fit(X_train, y_train)
y_pred_dt = dt.predict(X_test)
f1_dt = f1_score(y_test, y_pred_dt, average='macro')

bagging = BaggingClassifier(
    estimator=DecisionTreeClassifier(random_state=42, class_weight='balanced'),
    n_estimators=50,
    random_state=42,
    n_jobs=-1
)
bagging.fit(X_train, y_train)
y_pred_bag = bagging.predict(X_test)
f1_bag = f1_score(y_test, y_pred_bag, average='macro')

rf_base = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
    class_weight='balanced',
    n_jobs=-1
)
rf_base.fit(X_train, y_train)
y_pred_rf_base = rf_base.predict(X_test)
f1_rf_base = f1_score(y_test, y_pred_rf_base, average='macro')

results_task1 = pd.DataFrame({
    'Модель': ['Decision Tree', 'Bagging Trees', 'Random Forest'],
    'macro F1': [f1_dt, f1_bag, f1_rf_base]
})
print(results_task1.sort_values('macro F1', ascending=False).to_string(index=False))

# Задание 2: Оптимизация Random Forest
print("\nЗадание 2: Оптимизация Random Forest\n")

param_grid = {
    'n_estimators': [100, 150],
    'max_depth': [10, 15, None],
    'min_samples_split': [5, 10],
    'min_samples_leaf': [2, 4],
    'max_features': ['sqrt', 'log2']
}

grid_search = GridSearchCV(
    RandomForestClassifier(random_state=42, class_weight='balanced', n_jobs=-1),
    param_grid,
    cv=3,
    scoring='f1_macro',
    n_jobs=-1,
    verbose=1
)

grid_search.fit(X_train, y_train)

print(f"Лучшие параметры: {grid_search.best_params_}")
print(f"Лучший score на кросс-валидации: {grid_search.best_score_:.4f}")

best_rf = grid_search.best_estimator_
y_pred_best_rf = best_rf.predict(X_test)
f1_best_rf = f1_score(y_test, y_pred_best_rf, average='macro')
print(f"Оптимизированный Random Forest macro F1 на тесте: {f1_best_rf:.4f}")

print("\nClassification Report Random Forest (оптимизированный):")
print(classification_report(y_test, y_pred_best_rf, target_names=['Legit (0)', 'Fraud (1)']))

cm_rf = confusion_matrix(y_test, y_pred_best_rf)
print("\nМатрица ошибок для оптимизированного Random Forest:")
print(cm_rf)

# Задание 3: Ансамбли моделей
print("\nЗадание 3: Ансамбли моделей\n")

# a) LightGBM
print("\na) LightGBM Classifier")
scale_pos_weight = len(y_train[y_train==0]) / len(y_train[y_train==1])

lgb_model = lgb.LGBMClassifier(
    random_state=42,
    scale_pos_weight=scale_pos_weight,
    n_estimators=200,
    learning_rate=0.1,
    max_depth=10,
    verbosity=-1,
    n_jobs=-1
)
lgb_model.fit(X_train, y_train)
y_pred_lgb = lgb_model.predict(X_test)
f1_lgb = f1_score(y_test, y_pred_lgb, average='macro')
print(f"LightGBM macro F1: {f1_lgb:.4f}")

print("\nClassification Report LightGBM:")
print(classification_report(y_test, y_pred_lgb, target_names=['Legit (0)', 'Fraud (1)']))

cm_lgb = confusion_matrix(y_test, y_pred_lgb)
print("Матрица ошибок LightGBM:")
print(cm_lgb)

# б) Стекинг с тремя моделями
print("\nб) Stacking Classifier")

# 1) Оптимизированный Random Forest (с задания 2)
# 2) XGBoost
xgb_model = xgb.XGBClassifier(
    random_state=42,
    scale_pos_weight=scale_pos_weight,
    n_estimators=200,
    max_depth=10,
    learning_rate=0.1,
    eval_metric='logloss',
    n_jobs=-1
)

# 3) GradientBoosting
gb_model = GradientBoostingClassifier(
    n_estimators=200,
    max_depth=10,
    learning_rate=0.1,
    random_state=42,
    subsample=0.8
)

stacking = StackingClassifier(
    estimators=[
        ('rf', best_rf),
        ('xgb', xgb_model),
        ('gb', gb_model)
    ],
    final_estimator=LogisticRegression(random_state=42, max_iter=1000),
    cv=3,
    n_jobs=-1
)

stacking.fit(X_train, y_train)
y_pred_stack = stacking.predict(X_test)
f1_stack = f1_score(y_test, y_pred_stack, average='macro')
print(f"Stacking Classifier macro F1: {f1_stack:.4f}")

print("\nClassification Report Stacking:")
print(classification_report(y_test, y_pred_stack, target_names=['Legit (0)', 'Fraud (1)']))

cm_stack = confusion_matrix(y_test, y_pred_stack)
print("Матрица ошибок Stacking:")
print(cm_stack)

# Визуализация
print("\nСравнение моделей\n")

all_results = pd.DataFrame({
    'Модель': ['Decision Tree', 'Bagging Trees', 'Random Forest (баз)',
               'Random Forest (оптим)', 'LightGBM', 'Stacking'],
    'macro F1': [f1_dt, f1_bag, f1_rf_base, f1_best_rf, f1_lgb, f1_stack]
})

print("\nРезультаты всех моделей:")
print(all_results.sort_values('macro F1', ascending=False).to_string(index=False))

# График сравнения моделей
plt.figure(figsize=(10, 6))
sorted_results = all_results.sort_values('macro F1')
colors = ['lightblue', 'lightblue', 'lightblue', 'lightgreen', 'orange', 'red']
bars = plt.barh(range(len(sorted_results)), sorted_results['macro F1'], color=colors)
plt.yticks(range(len(sorted_results)), sorted_results['Модель'])
plt.xlabel('macro F1 Score')
plt.title('Сравнение моделей по метрике macro F1')
plt.xlim(0, 1)

for bar in bars:
    width = bar.get_width()
    plt.text(width + 0.005, bar.get_y() + bar.get_height()/2,
             f'{width:.4f}', ha='left', va='center', fontweight='bold')

plt.tight_layout()
plt.show()

# Матрицы ошибок для ключевых моделей
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
models_to_plot = [
    ('Random Forest (оптим)', y_pred_best_rf, f1_best_rf),
    ('LightGBM', y_pred_lgb, f1_lgb),
    ('Stacking', y_pred_stack, f1_stack)
]

for idx, (name, y_pred, f1_score_val) in enumerate(models_to_plot):
    cm = confusion_matrix(y_test, y_pred)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['Legit', 'Fraud'])
    disp.plot(ax=axes[idx], cmap='Blues', colorbar=False)
    axes[idx].set_title(f'{name}\nMacro F1: {f1_score_val:.4f}')

plt.suptitle('Матрицы ошибок для лучших моделей', fontsize=12, y=1.05)
plt.tight_layout()
plt.show()

# Итоги
print("\nИтоги\n")

best_model_idx = all_results['macro F1'].idxmax()
best_model_name = all_results.loc[best_model_idx, 'Модель']
best_model_f1 = all_results.loc[best_model_idx, 'macro F1']

print(f"Лучшая модель: {best_model_name}")
print(f"Macro F1 score: {best_model_f1:.4f}")
print(f"\nStacking улучшил результат на {((best_model_f1/f1_best_rf)-1)*100:.1f}% относительно оптимизированного Random Forest")