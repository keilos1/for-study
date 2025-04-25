import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.formula.api import ols


def load_and_clean_data():
    """Загрузка и очистка данных из файла"""
    try:
        # Загрузка данных
        df = pd.read_excel('iskhodnye.xlsx', sheet_name='Задание 5')
        print(f"Загружено строк: {len(df)}")

        # Проверка необходимых столбцов
        required_cols = ['С', 'Ю', 'Ц', 'Y', 'B']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"Отсутствуют необходимые столбцы. Найдены: {df.columns.tolist()}")

        # Глубокая очистка данных
        df_clean = df.replace([np.inf, -np.inf], np.nan).dropna()
        df_clean = df_clean[(df_clean.select_dtypes(include=[np.number]) != 0).all(axis=1)]

        print(f"Строк после очистки: {len(df_clean)}")
        return df_clean

    except Exception as e:
        print(f"Ошибка загрузки данных: {str(e)}")
        return None


def task_5_1(df):
    """Анализ для задачи 5.1 с защитой от ошибок"""
    try:
        # Подготовка данных
        df_melted = pd.melt(df, id_vars=['Y', 'B'],
                            value_vars=['С', 'Ю', 'Ц'],
                            var_name='Region', value_name='Value').dropna()

        if len(df_melted) < 10:
            raise ValueError("Недостаточно данных после преобразования")

        # ANOVA анализ
        model = ols('Y ~ C(Region)', data=df_melted).fit()
        anova_table = sm.stats.anova_lm(model, typ=2)

        print("\n=== Задача 5.1 ===")
        print("Результаты дисперсионного анализа:")
        print(anova_table)

        if 'C(Region)' in anova_table.index:
            p_value = anova_table.loc['C(Region)', 'PR(>F)']
            print(
                f"\nВывод: Влияние региона на Y {'значимо' if p_value < 0.05 else 'не значимо'} (p-value={p_value:.4f})")
        else:
            print("Не удалось определить значимость региона")

    except Exception as e:
        print(f"Ошибка в задаче 5.1: {str(e)}")


def task_5_2(df):
    """Анализ для задачи 5.2 с защитой от ошибок"""
    try:
        # Подготовка данных
        df_melted = pd.melt(df, id_vars=['Y', 'B'],
                            value_vars=['С', 'Ю', 'Ц'],
                            var_name='Region', value_name='Value').dropna()

        if len(df_melted) < 10:
            raise ValueError("Недостаточно данных после преобразования")

        # Преобразование B в категориальный при необходимости
        if df_melted['B'].nunique() < 5:
            df_melted['B'] = df_melted['B'].astype('category')

        print("\n=== Задача 5.2 ===")

        # Модель с взаимодействием
        model_with_int = ols('Y ~ C(Region) * C(B)', data=df_melted).fit()
        anova_with_int = sm.stats.anova_lm(model_with_int, typ=2)
        print("Результаты двухфакторного ANOVA с взаимодействием:")
        print(anova_with_int)

        # Проверка значимости
        if all(term in anova_with_int.index for term in ['C(Region)', 'C(B)', 'C(Region):C(B)']):
            print("\nАнализ значимости:")
            p_region = anova_with_int.loc['C(Region)', 'PR(>F)']
            p_b = anova_with_int.loc['C(B)', 'PR(>F)']
            p_inter = anova_with_int.loc['C(Region):C(B)', 'PR(>F)']

            print(f"Регион: {'значим' if p_region < 0.05 else 'не значим'} (p={p_region:.4f})")
            print(f"Фактор B: {'значим' if p_b < 0.05 else 'не значим'} (p={p_b:.4f})")
            print(f"Взаимодействие: {'значимо' if p_inter < 0.05 else 'не значимо'} (p={p_inter:.4f})")

            # Упрощенная модель при незначимом взаимодействии
            if p_inter > 0.05:
                print("\nУпрощенная модель без взаимодействия:")
                model_simple = ols('Y ~ C(Region) + C(B)', data=df_melted).fit()
                print(sm.stats.anova_lm(model_simple, typ=2))
        else:
            print("Не удалось проанализировать значимость факторов")

    except Exception as e:
        print(f"Ошибка в задаче 5.2: {str(e)}")


def main():
    # Загрузка и очистка данных
    df = load_and_clean_data()
    if df is None:
        return

    # Выполнение анализа
    task_5_1(df)
    task_5_2(df)


if __name__ == "__main__":
    main()