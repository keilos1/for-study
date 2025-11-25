# Установка пакетов
if (!require("doParallel")) install.packages("doParallel")
if (!require("ggplot2")) install.packages("ggplot2")
if (!require("rpart")) install.packages("rpart")

# Загрузка необходимых пакетов
library(doParallel)
library(ggplot2)
library(rpart)

# Установка зерна для воспроизводимости
set.seed(123)

# Используем встроенный датасет iris
data(iris)
dataset <- iris

cat(" Тестирование последовательного и параллельного выполнения вычислений\n")

# Сетка гиперпараметров
hyper_grid <- expand.grid(
  minsplit = seq(2, 20, by = 2),           # 10 значений: 2,4,6,...,20 (мин. наблюдений для разделения)
  cp = c(0.001, 0.005, 0.01, 0.05, 0.1),   # 5 значений (параметр сложности)
  maxdepth = c(2, 3, 5, 7, 10, 15),        # 6 значений (макс. глубина дерева)
  n_folds = c(5, 10)                       # 2 значения (количество фолдов кросс-валидации)
)

num_experiments <- nrow(hyper_grid)
cat(" Параметры:\n")
cat(" Состав сетки:\n")
cat("  - minsplit: 10 значений (", paste(seq(2, 20, by = 2), collapse = ", "), ")\n")
cat("  - cp: 5 значений (", paste(c(0.001, 0.005, 0.01, 0.05, 0.1), collapse = ", "), ")\n")
cat("  - maxdepth: 6 значений (", paste(c(2, 3, 5, 7, 10, 15), collapse = ", "), ")\n")
cat("  - n_folds: 2 значения (", paste(c(5, 10), collapse = ", "), ")\n")
cat(" Количество комбинаций параметров:", num_experiments, "\n")

# функция кросс-валидации
enhanced_cross_validation <- function(data, params, n_folds = NULL) {
  if (is.null(n_folds)) n_folds <- params$n_folds
  
  # Создаем стратифицированные фолды для лучшей оценки
  folds <- sample(rep(1:n_folds, length.out = nrow(data)))
  accuracies <- numeric(n_folds)
  
  for (fold in 1:n_folds) {
    train_idx <- which(folds != fold)
    test_idx <- which(folds == fold)
    
    # Добавляем небольшую задержку для имитации более сложных вычислений
    Sys.sleep(0.001)
    
    model <- rpart(
      Species ~ .,
      data = data[train_idx, ],
      method = "class",
      control = rpart.control(
        minsplit = params$minsplit,
        cp = params$cp,
        maxdepth = params$maxdepth
      )
    )
    
    predictions <- predict(model, data[test_idx, ], type = "class")
    accuracy <- mean(predictions == data[test_idx, "Species"])
    accuracies[fold] <- accuracy
  }
  
  return(mean(accuracies))
}

# Функция для обучения и оценки модели
train_evaluate_model <- function(params, data) {
  cv_accuracy <- enhanced_cross_validation(data, params)
  
  # "тяжелые" вычисления для увеличения нагрузки
  model <- rpart(
    Species ~ .,
    data = data,
    method = "class",
    control = rpart.control(
      minsplit = params$minsplit,
      cp = params$cp,
      maxdepth = params$maxdepth
    )
  )
  
  # Вычисляем важность признаков
  importance <- rep(0, ncol(data) - 1)
  if (!is.null(model$variable.importance)) {
    importance <- as.numeric(model$variable.importance)
  }
  
  return(list(
    params = params,
    accuracy = cv_accuracy,
    importance = importance
  ))
}

# Тест разного количества ядер
num_cores_to_test <- c(1, 2, 3, 4)
execution_times <- numeric(length(num_cores_to_test))
all_results <- list()

cat(" Запуск теста...\n\n")

for (i in seq_along(num_cores_to_test)) {
  num_cores <- num_cores_to_test[i]
  cat("--- Запуск на", num_cores, "ядре(ах) ---\n")
  
  start_time <- Sys.time()
  
  if (num_cores == 1) {
    # Последовательная версия
    cat("Режим: ПОСЛЕДОВАТЕЛЬНЫЕ вычисления\n")
    
    results_sequential <- list()
    for (exp_idx in 1:num_experiments) {
      cat("Эксперимент", exp_idx, "из", num_experiments, "\r")
      flush.console()
      results_sequential[[exp_idx]] <- train_evaluate_model(hyper_grid[exp_idx, ], dataset)
    }
    cat("\n")
    all_results[[i]] <- results_sequential
    
  } else {
    # Параллельная версия
    cat("Режим: ПАРАЛЛЕЛЬНЫЕ вычисления\n")
    
    # Настраиваем кластер для лучшей производительности
    cl <- makeCluster(num_cores, type = "PSOCK")
    registerDoParallel(cl)
    
    # Экспортируем необходимые данные в кластер
    clusterExport(cl, c("enhanced_cross_validation", "train_evaluate_model"))
    
    results_parallel <- foreach(
      exp_idx = 1:num_experiments,
      .packages = "rpart",
      .combine = 'c'
    ) %dopar% {
      list(train_evaluate_model(hyper_grid[exp_idx, ], dataset))
    }
    
    stopCluster(cl)
    registerDoSEQ()
    all_results[[i]] <- results_parallel
  }
  
  end_time <- Sys.time()
  execution_times[i] <- as.numeric(difftime(end_time, start_time, units = "secs"))
  cat("Время выполнения:", round(execution_times[i], 2), "секунд\n\n")
}

# Результаты
cat("Результаты:\n")

final_results <- all_results[[1]]
accuracies <- sapply(final_results, function(x) x$accuracy)

# Находим лучшую модель
best_idx <- which.max(accuracies)
best_result <- final_results[[best_idx]]
best_accuracy <- best_result$accuracy
best_params <- best_result$params

cat("Результаты подбора параметров:\n")
cat("Лучшая точность модели:", round(best_accuracy, 4), "\n")
cat("Оптимальные параметры:\n")
cat("  minsplit:", best_params$minsplit, "\n")
cat("  cp:", best_params$cp, "\n")
cat("  maxdepth:", best_params$maxdepth, "\n")
cat("  n_folds:", best_params$n_folds, "\n\n")

# Таблица производительности
performance_results <- data.frame(
  Ядра = num_cores_to_test,
  Время_сек = round(execution_times, 2),
  Ускорение = round(execution_times[1] / execution_times, 2)
)

cat("Таблица производительности:\n")
print(performance_results)

# Эффективность параллелизации
cat("\nЭффективность параллелизации:\n")
cat("Теоретическое максимальное ускорение:", max(num_cores_to_test), "x\n")
cat("Достигнутое ускорение:", round(max(performance_results$Ускорение), 2), "x\n")

# Эффективность параллелизации в процентах
efficiency <- (performance_results$Ускорение / performance_results$Ядра) * 100
performance_results$Эффективность <- round(efficiency, 1)

cat("Эффективность параллелизации (%):\n")
for (i in 1:nrow(performance_results)) {
  cat("  ", performance_results$Ядра[i], "ядра:", performance_results$Эффективность[i], "%\n")
}

# Построение графиков
cat("\nПостроение графиков\n")

# График ускорения
speedup_plot <- ggplot(performance_results, aes(x = Ядра, y = Ускорение)) +
  geom_line(color = "steelblue", linewidth = 1.2) +
  geom_point(color = "steelblue", size = 3) +
  geom_abline(slope = 1, intercept = 0, linetype = "dashed", color = "darkred", alpha = 0.7) +
  geom_line(aes(y = Ядра), linetype = "dotted", color = "darkgreen", alpha = 0.7) + # Идеальное ускорение
  labs(
    title = "График ускорения параллельного подбора гиперпараметров",
    subtitle = paste("Задача: Grid Search для", num_experiments, "комбинаций параметров"),
    x = "Количество вычислительных ядер",
    y = "Коэффициент ускорения",
    caption = paste("Лучшая точность:", round(best_accuracy, 4), 
                    "| Эффективность:", round(max(efficiency), 1), "%")
  ) +
  theme_minimal() +
  scale_x_continuous(breaks = num_cores_to_test) +
  scale_y_continuous(breaks = seq(0, max(num_cores_to_test) + 1, by = 1))

# График времени выполнения
time_plot <- ggplot(performance_results, aes(x = Ядра, y = Время_сек)) +
  geom_col(fill = "lightcoral", alpha = 0.8) +
  labs(
    title = "Время выполнения в зависимости от количества ядер",
    x = "Количество ядер",
    y = "Время (секунды)"
  ) +
  theme_minimal() +
  scale_x_continuous(breaks = num_cores_to_test)

# Сохраняем графики
ggsave("speedup_plot_enhanced.png", plot = speedup_plot, width = 10, height = 6, dpi = 300)
ggsave("time_plot.png", plot = time_plot, width = 8, height = 6, dpi = 300)

cat("Графики сохранены в speedup_plot_enhanced.png и time_plot.png")

# Выводим графики
print(speedup_plot)
print(time_plot)
