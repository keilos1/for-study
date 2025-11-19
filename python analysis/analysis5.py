import numpy as np
import matplotlib.pyplot as plt
from scipy import integrate, interpolate
from scipy.integrate import solve_ivp
from sympy import symbols, solve, tan

print("РЕШЕНИЕ ЗАДАНИЙ\n")

print("ЗАДАНИЕ 1\n")

# 1.1 Первый интеграл - ПРАВИЛЬНОЕ решение
def f1(x):
    return 2 * np.tan(x) + 1

# Точка разрыва тангенса π/2 ≈ 1.5708
break_point = np.pi/2

print(f"Точка разрыва тангенса: x = π/2 ≈ {break_point:.4f}")

# Разбиваем интеграл на две части, избегая точки разрыва
result1_1, error1_1 = integrate.quad(f1, -1, break_point - 1e-10)
result1_2, error1_2 = integrate.quad(f1, break_point + 1e-10, 2)

result1 = result1_1 + result1_2
total_error = error1_1 + error1_2

print(f"1.1 ∫₋₁² (2tg(x) + 1) dx = {result1:.6f}")
print(f"   Оценка погрешности: {total_error:.2e}")
print(f"   (интеграл разбит на [-1, {break_point:.4f}) и ({break_point:.4f}, 2] для избежания разрыва)")

# 1.2 Двойной интеграл
def inner_integral(x):
    def f2(y):
        return x + y
    result, error = integrate.quad(f2, x**2, x)
    return result

result2, error2 = integrate.quad(inner_integral, 0, 1)
print(f"\n1.2 ∫₀¹ ∫ₓ²ˣ (x + y) dydx = {result2:.6f}")
print(f"   Оценка погрешности: {error2:.2e}")

print("\nЗАДАНИЕ 2\n")

def derivative(t, y):
    return 2 * t

# Решаем ОДУ с начальным условием y(0) = 1
solution = solve_ivp(derivative, [0, 3], [1], method='RK45', rtol=1e-4, atol=1e-6)

# Находим y(3)
y_3 = solution.y[0][-1]
print(f"y(3) = {y_3:.6f}")

# Аналитическое решение для проверки
analytic_solution = 3**2 + 1  # ∫2x dx = x² + C, при y(0)=1 => C=1
print(f"Аналитическое решение: y(3) = {analytic_solution}")
print(f"Погрешность: {abs(y_3 - analytic_solution):.2e}")

print("\nЗАДАНИЕ 3\n")

# Исходные точки
x_original = np.arange(0, 16)
f_original = -np.sin(2*x_original) + np.sqrt(x_original)
список1 = list(f_original)

print("Первые 10 значений списка1:")
for i in range(10):
    print(f"f({x_original[i]}) = {список1[i]:.4f}")

# Точки для интерполяции
x_interp = np.linspace(0, 15, 100)

# Линейная интерполяция
linear_interp = interpolate.interp1d(x_original, f_original, kind='linear')
f_linear = linear_interp(x_interp)

# Кубическая интерполяция
cubic_interp = interpolate.interp1d(x_original, f_original, kind='cubic')
f_cubic = cubic_interp(x_interp)

# Построение графиков
plt.figure(figsize=(12, 8))

plt.subplot(2, 1, 1)
plt.plot(x_original, f_original, 'bo', label='Исходные точки', markersize=6)
plt.plot(x_interp, f_linear, 'r-', label='Линейная интерполяция', linewidth=2)
plt.xlabel('x')
plt.ylabel('f(x)')
plt.title('Линейная интерполяция')
plt.legend()
plt.grid(True)

plt.subplot(2, 1, 2)
plt.plot(x_original, f_original, 'bo', label='Исходные точки', markersize=6)
plt.plot(x_interp, f_cubic, 'g-', label='Кубическая интерполяция', linewidth=2)
plt.xlabel('x')
plt.ylabel('f(x)')
plt.title('Кубическая интерполяция')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()

print("\nЗАДАНИЕ 4\n")

# Распределение случайной величины X (игральный кубик)
x_values = np.array([1, 2, 3, 4, 5, 6])
probabilities = np.array([1/6, 1/6, 1/6, 1/6, 1/6, 1/6])

# Математическое ожидание
mean = np.sum(x_values * probabilities)
print(f"Математическое ожидание E(X) = {mean}")

# Дисперсия
variance = np.sum((x_values - mean)**2 * probabilities)
print(f"Дисперсия D(X) = {variance:.4f}")

# Медиана (для дискретного распределения)
median = 3.5  # Среднее между 3 и 4
print(f"Медиана = {median}")

# Построение графиков
plt.figure(figsize=(12, 5))

# Функция распределения (CDF)
plt.subplot(1, 2, 1)
cdf = np.cumsum(probabilities)
plt.step(np.concatenate(([0], x_values, [7])),
         np.concatenate(([0], cdf, [1])),
         where='post', linewidth=2)
plt.xlabel('x')
plt.ylabel('F(x)')
plt.title('Функция распределения (CDF)')
plt.grid(True)
plt.xticks(x_values)

# Закон распределения (PMF)
plt.subplot(1, 2, 2)
plt.stem(x_values, probabilities, basefmt=' ')
plt.xlabel('x')
plt.ylabel('P(X = x)')
plt.title('Закон распределения (PMF)')
plt.grid(True)
plt.xticks(x_values)

plt.tight_layout()
plt.show()

print("\nЗАДАНИЕ 5\n")

# Определяем символы
x, y, z = symbols('x y z')

# Задаем систему уравнений
eq1 = x - y + z - 2
eq2 = 2*x - y + z - 3
eq3 = 3*x - 3*y + z

# Решаем систему
solution = solve((eq1, eq2, eq3), (x, y, z))

print("Решение системы уравнений:")
print(f"x = {solution[x]}")
print(f"y = {solution[y]}")
print(f"z = {solution[z]}")

# Проверка
print("\nПроверка:")
print(f"Уравнение 1: {x - y + z}. При подстановке: {solution[x] - solution[y] + solution[z]} (должно быть 2)")
print(f"Уравнение 2: {2*x - y + z}. При подстановке: {2*solution[x] - solution[y] + solution[z]} (должно быть 3)")
print(f"Уравнение 3: {3*x - 3*y + z}. При подстановке: {3*solution[x] - 3*solution[y] + solution[z]} (должно быть 0)")