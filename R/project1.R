# Установка пакетов
packages <- c("readxl", "dplyr", "tidyr", "ggplot2", "lmtest", "sandwich")
for (pkg in packages) {
  if (!require(pkg, character.only = TRUE)) {
    install.packages(pkg)
    library(pkg, character.only = TRUE)
  }
}
rm(list = ls())
options(scipen = 999)
options(readr.show_col_types = FALSE)

file_apartments <- "G:/Учеба/Эконометрика/Количество построенных квартир.xlsx"
file_income <- "G:/Учеба/Эконометрика/Среднедушевые денежные доходы.xlsx"

# Загружаем данные
df_apartments_raw <- suppressMessages(
  read_excel(file_apartments, sheet = "chart", col_names = FALSE)
)
df_income_raw <- suppressMessages(
  read_excel(file_income, sheet = "chart(1)", col_names = FALSE)
)

# Извлекаем года
years <- as.numeric(unlist(df_apartments_raw[4:16, 1]))

# Извлекаем названия регионов
region_names_raw <- as.character(unlist(df_apartments_raw[2, 2:ncol(df_apartments_raw)]))

# Очищаем названия регионов
valid_regions <- !is.na(region_names_raw) & 
  region_names_raw != "NA" & 
  region_names_raw != "" & 
  !grepl("^[0-9]+$", region_names_raw)

region_names <- region_names_raw[valid_regions]
cat("\nНайдено регионов:", length(region_names), "\n")

# Создаем пустые списки
apartments_list <- list()
income_list <- list()

# Заполняем данными
for (i in 1:length(years)) {
  year <- years[i]
  row_apt <- i + 3
  row_inc <- i + 3
  
  for (j in 1:length(region_names)) {
    col_idx <- j + 1
    
    apt_value <- as.numeric(df_apartments_raw[row_apt, col_idx])
    inc_value <- as.numeric(df_income_raw[row_inc, col_idx])
    
    if (!is.na(apt_value) && !is.na(inc_value) && apt_value > 0 && inc_value > 0) {
      apartments_list <- append(apartments_list, list(
        data.frame(Year = year, Region = region_names[j], Apartments = apt_value)
      ))
      income_list <- append(income_list, list(
        data.frame(Year = year, Region = region_names[j], Income = inc_value)
      ))
    }
  }
}

# Объединяем данные
if (length(apartments_list) > 0) {
  apartments_long <- bind_rows(apartments_list)
  income_long <- bind_rows(income_list)
  df <- inner_join(apartments_long, income_long, by = c("Year", "Region"), relationship = "many-to-many")
  # Исключаем все строки, где в названии есть "федер" или "Федер"
  df <- df %>% 
    filter(!grepl("федер.*|Федер.*", Region))
  
  cat("\n РЕЗУЛЬТАТ \n")
  cat("Количество наблюдений:", nrow(df), "\n")
  cat("Количество регионов:", length(unique(df$Region)), "\n")
  
  # Строим график
  p1 <- ggplot(df, aes(x = Income, y = Apartments)) +
    geom_point(alpha = 0.3, size = 1, color = "blue") +
    geom_smooth(method = "lm", se = TRUE, color = "red") +
    labs(
      title = "Зависимость количества построенных квартир от доходов населения",
      subtitle = paste("Наблюдений:", nrow(df), "| Регионов:", length(unique(df$Region))),
      x = "Среднедушевые денежные доходы (руб.)",
      y = "Количество построенных квартир (единиц)"
    ) +
    theme_minimal()
  
  print(p1)
  
} else {
  cat("\nНЕТ ДАННЫХ! Проверьте структуру файлов.\n")
}

# Корреляционный анализ
correlation <- cor(df$Income, df$Apartments, use = "complete.obs")
cor_test <- cor.test(df$Income, df$Apartments)

cat("\nКоэффициент корреляции Пирсона: r =", round(correlation, 4))
cat("\nПроверка значимости: p-value =", format(cor_test$p.value, scientific = FALSE))
cat(sprintf("\nИнтерпретация: связь %s", 
            ifelse(abs(correlation) > 0.7, "сильная",
                   ifelse(abs(correlation) > 0.5, "умеренная", "слабая"))))
cat(sprintf("\nНаправление связи: %s", 
            ifelse(correlation > 0, "прямая", "обратная")))
cat(sprintf("\nВывод: %s", 
            ifelse(cor_test$p.value < 0.05, 
                   "корреляция статистически значима", 
                   "корреляция не значима")))

# Статистика по данным
cat("\n\nСтатистика по доходам:\n")
print(summary(df$Income))
cat("\nСтатистика по квартирам:\n")
print(summary(df$Apartments))

# ЗАДАНИЕ 2: ПОСТРОЕНИЕ МОДЕЛЕЙ ДЛЯ ПРОГНОЗА
cat("\n\n ЗАДАНИЕ 2: ПОСТРОЕНИЕ МОДЕЛЕЙ\n")

# Функция для расчета ошибки аппроксимации
calc_approximation_error <- function(actual, predicted) {
  mean(abs((actual - predicted) / actual), na.rm = TRUE) * 100
}

# 5.1 ЛИНЕЙНАЯ МОДЕЛЬ
model_linear <- lm(Apartments ~ Income, data = df)
df$pred_linear <- predict(model_linear)

# 5.2 ГИПЕРБОЛИЧЕСКАЯ МОДЕЛЬ (y = a + b/x)
df <- df %>% filter(Income > 0)
df$Income_inv <- 1 / df$Income
model_hyperbolic <- lm(Apartments ~ Income_inv, data = df)
df$pred_hyperbolic <- predict(model_hyperbolic)

# 5.3 СТЕПЕННАЯ МОДЕЛЬ (ln(y) = ln(a) + b*ln(x))
df$log_Apartments <- log(df$Apartments)
df$log_Income <- log(df$Income)
model_power <- lm(log_Apartments ~ log_Income, data = df)
df$pred_power <- exp(predict(model_power))

# 5.4 ПОКАЗАТЕЛЬНАЯ МОДЕЛЬ (ln(y) = ln(a) + b*x)
model_exponential <- lm(log_Apartments ~ Income, data = df)
df$pred_exponential <- exp(predict(model_exponential))

# 5.5 ЛОГАРИФМИЧЕСКАЯ МОДЕЛЬ (y = a + b*ln(x))
model_logarithmic <- lm(Apartments ~ log_Income, data = df)
df$pred_logarithmic <- predict(model_logarithmic)

# Сравнение моделей
model_comparison <- data.frame(
  Модель = c("Линейная", "Гиперболическая", "Степенная", 
             "Показательная", "Логарифмическая"),
  R2 = c(
    summary(model_linear)$r.squared,
    summary(model_hyperbolic)$r.squared,
    summary(model_power)$r.squared,
    summary(model_exponential)$r.squared,
    summary(model_logarithmic)$r.squared
  ),
  R2_adj = c(
    summary(model_linear)$adj.r.squared,
    summary(model_hyperbolic)$adj.r.squared,
    summary(model_power)$adj.r.squared,
    summary(model_exponential)$adj.r.squared,
    summary(model_logarithmic)$adj.r.squared
  ),
  A_error = c(
    calc_approximation_error(df$Apartments, df$pred_linear),
    calc_approximation_error(df$Apartments, df$pred_hyperbolic),
    calc_approximation_error(df$Apartments, df$pred_power),
    calc_approximation_error(df$Apartments, df$pred_exponential),
    calc_approximation_error(df$Apartments, df$pred_logarithmic)
  )
)

cat("\nСравнение моделей:\n")
print(model_comparison %>% arrange(desc(R2)))

# Выбираем лучшую модель
best_model_name <- model_comparison$Модель[which.max(model_comparison$R2)]
cat(sprintf("\n\nЛучшая модель: %s", best_model_name))
cat(sprintf("\nКоэффициент детерминации R2 = %.4f", max(model_comparison$R2)))
cat(sprintf("\nОшибка аппроксимации A = %.2f%%", 
            model_comparison$A_error[which.max(model_comparison$R2)]))

# Подробный анализ лучшей модели
if (best_model_name == "Линейная") {
  best_model <- model_linear
} else if (best_model_name == "Гиперболическая") {
  best_model <- model_hyperbolic
} else if (best_model_name == "Степенная") {
  best_model <- model_power
} else if (best_model_name == "Показательная") {
  best_model <- model_exponential
} else {
  best_model <- model_logarithmic
}

cat("\n\nДетальный анализ лучшей модели:\n")
summary(best_model)

# 6. ЗАДАНИЕ 3: ПРОГНОЗ ДЛЯ РЕСПУБЛИКИ КАРЕЛИЯ ----
cat("\n\n========== ЗАДАНИЕ 3: ПРОГНОЗ ДЛЯ РЕСПУБЛИКИ КАРЕЛИЯ ==========\n")

# Выбираем данные по Карелии
karelia_data <- df %>% filter(grepl("Карелия", Region))

if (nrow(karelia_data) > 0) {
  cat("\nДанные по Республике Карелия:\n")
  print(karelia_data %>% select(Year, Income, Apartments))
  
  # Делаем прогноз по всем годам для Карелии
  karelia_data$predicted <- NA
  
  for (i in 1:nrow(karelia_data)) {
    if (best_model_name == "Линейная") {
      karelia_data$predicted[i] <- predict(best_model, 
                                           newdata = data.frame(Income = karelia_data$Income[i]))
    } else if (best_model_name == "Гиперболическая") {
      karelia_data$predicted[i] <- predict(best_model, 
                                           newdata = data.frame(Income_inv = 1/karelia_data$Income[i]))
    } else if (best_model_name == "Степенная") {
      karelia_data$predicted[i] <- exp(predict(best_model, 
                                               newdata = data.frame(log_Income = log(karelia_data$Income[i]))))
    } else if (best_model_name == "Показательная") {
      karelia_data$predicted[i] <- exp(predict(best_model, 
                                               newdata = data.frame(Income = karelia_data$Income[i])))
    } else {
      karelia_data$predicted[i] <- predict(best_model, 
                                           newdata = data.frame(log_Income = log(karelia_data$Income[i])))
    }
  }
  
  # Расчет ошибок прогноза
  karelia_data <- karelia_data %>%
    mutate(
      error = Apartments - predicted,
      rel_error = abs(error) / Apartments * 100
    )
  
  cat("\nПрогноз для Республики Карелия:\n")
  print(karelia_data %>% 
          select(Year, Income, Apartments, predicted, error, rel_error) %>%
          mutate(across(where(is.numeric), round, 2)))
  
  # Средняя ошибка прогноза
  mean_error <- mean(karelia_data$rel_error, na.rm = TRUE)
  cat(sprintf("\nСредняя относительная ошибка прогноза: %.2f%%", mean_error))
  
  # Визуализация фактических и прогнозных значений
  p2 <- ggplot(karelia_data, aes(x = Year)) +
    geom_line(aes(y = Apartments, color = "Фактические"), size = 1.2) +
    geom_line(aes(y = predicted, color = "Прогнозные"), size = 1.2, linetype = "dashed") +
    scale_color_manual(values = c("Фактические" = "blue", "Прогнозные" = "red")) +
    scale_x_continuous(breaks = seq(min(karelia_data$Year), max(karelia_data$Year), by = 1)) +
    labs(
      title = "Республика Карелия: фактические и прогнозные значения",
      x = "Год",
      y = "Количество построенных квартир",
      color = ""
    ) +
    theme_minimal() +
    theme(
      plot.title = element_text(hjust = 0.5, size = 14, face = "bold"),
      legend.position = "bottom"
    )
  
  print(p2)
  
  # Оценка влияния фактора
  if (best_model_name == "Линейная") {
    coef_income <- coef(best_model)["Income"]
    cat(sprintf("\n\nОценка влияния фактора:"))
    cat(sprintf("\nПри увеличении среднедушевых доходов на 1 рубль,"))
    cat(sprintf("\nколичество построенных квартир изменяется в среднем на %.4f ед.", coef_income))
    cat(sprintf("\n(в расчете на 1000 руб. дохода: %.2f ед.)", coef_income * 1000))
  } else if (best_model_name == "Степенная") {
    elasticity <- coef(best_model)["log_Income"]
    cat(sprintf("\n\nОценка влияния фактора:"))
    cat(sprintf("\nКоэффициент эластичности: %.4f", elasticity))
    cat(sprintf("\nПри увеличении доходов на 1%%, количество квартир"))
    cat(sprintf("\nизменяется в среднем на %.4f%%", elasticity))
  }
  
} else {
  cat("\nДанные по Республике Карелия не найдены в таблице.")
  cat("\nДоступные регионы, содержащие 'Карелия':")
  print(unique(grep("Карелия", df$Region, value = TRUE, ignore.case = TRUE)))
}