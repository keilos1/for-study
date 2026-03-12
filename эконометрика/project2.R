# Установка пакетов
packages <- c("readxl", "dplyr", "tidyr", "ggplot2", "lmtest", "sandwich", "car")
for (pkg in packages) {
  if (!require(pkg, character.only = TRUE)) {
    install.packages(pkg)
    library(pkg, character.only = TRUE)
  }
}
rm(list = ls())
options(scipen = 999)
options(readr.show_col_types = FALSE)

# Пути к файлам
file_apartments <- "G:/Учеба/Эконометрика/Количество построенных квартир.xlsx"
file_income <- "G:/Учеба/Эконометрика/Среднедушевые денежные доходы.xlsx"
file_features <- "G:/Учеба/Эконометрика/region_features.csv"

# Загружаем данные
df_apartments_raw <- suppressMessages(
  read_excel(file_apartments, sheet = "chart", col_names = FALSE)
)
df_income_raw <- suppressMessages(
  read_excel(file_income, sheet = "chart(1)", col_names = FALSE)
)
df_features <- read.csv(file_features, fileEncoding = "UTF-8", stringsAsFactors = FALSE)

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
cat("\nНайдено регионов в файле с квартирами:", length(region_names), "\n")

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

# Объединяем данные по квартирам и доходам
if (length(apartments_list) > 0) {
  apartments_long <- bind_rows(apartments_list)
  income_long <- bind_rows(income_list)
  df <- inner_join(apartments_long, income_long, by = c("Year", "Region"), relationship = "many-to-many")
  
  # Исключаем строки с федеральными округами в названии
  df <- df %>% 
    filter(!grepl("федер.*|Федер.*|ф\\.\\.\\.", Region))
  
  cat("\nОсновной датафрейм создан")
  cat("\nКоличество наблюдений:", nrow(df))
  cat("\nКоличество регионов:", length(unique(df$Region)), "\n")
}

cat("\n\n ДОБАВЛЕНИЕ НОВЫХ ФАКТОРОВ \n")

# Объединяем данные
df_full <- df %>%
  left_join(df_features, by = "Region")

# Проверяем, все ли регионы соединились
missing_after_join <- df_full %>%
  filter(is.na(Federal_District)) %>%
  pull(Region) %>%
  unique()

if (length(missing_after_join) > 0) {
  cat("\n\nРегионы, которые не соединились (проблема с названиями):\n")
  print(missing_after_join)
} else {
  cat("\n\nВсе регионы успешно соединились!\n")
}

# Удаляем строки с пропущенными значениями
df_full <- df_full %>% filter(!is.na(Federal_District))

cat("\nИтоговая размерность данных:", nrow(df_full), "наблюдений,", ncol(df_full), "переменных")
cat("\nФакторы для анализа:", paste(c("Income", "Population", "Latitude", "Distance_to_Moscow", "Federal_District"), collapse = ", "))

cat("\n\n 1. МНОЖЕСТВЕННАЯ РЕГРЕССИЯ \n")

# Строим модель с автоматическим созданием фиктивных переменных
# as.factor() преобразует Federal_District в набор dummy-переменных
model_multiple <- lm(Apartments ~ Income + Population + Latitude + Distance_to_Moscow + 
                       as.factor(Federal_District), 
                     data = df_full)

cat("\nРезультаты множественной регрессии:\n")
print(summary(model_multiple))

# Проверка на мультиколлинеарность
cat("\nПроверка на мультиколлинеарность (VIF > 10 - проблема):\n")
tryCatch({
  vif_values <- vif(model_multiple)
  print(vif_values)
}, error = function(e) {
  cat("Не удалось рассчитать VIF (возможно из-за фиктивных переменных)\n")
})

cat("\n\n 2. РЕГРЕССИЯ В СТАНДАРТИЗОВАННОМ ВИДЕ \n")

# Функция для стандартизации
standardize <- function(x) {
  return((x - mean(x, na.rm = TRUE)) / sd(x, na.rm = TRUE))
}

# Стандартизируем количественные переменные
df_std <- df_full %>%
  mutate(
    Apartments_std = standardize(Apartments),
    Income_std = standardize(Income),
    Population_std = standardize(Population),
    Latitude_std = standardize(Latitude),
    Distance_std = standardize(Distance_to_Moscow)
  )

# Строим регрессию на стандартизованных переменных
# Для сравнения силы влияния оставляем все переменные (без константы)
model_std <- lm(Apartments_std ~ Income_std + Population_std + Latitude_std + Distance_std +
                  as.factor(Federal_District) - 1,  # -1 чтобы убрать intercept
                data = df_std)

cat("\nРегрессия в стандартизованном виде (бета-коэффициенты):\n")
summary_std <- summary(model_std)
print(summary_std)

# Сравнение силы влияния количественных факторов
cat("\nСравнение силы влияния количественных факторов (по модулю):\n")
beta_coefs <- coef(model_std)[c("Income_std", "Population_std", "Latitude_std", "Distance_std")]
beta_coefs <- abs(beta_coefs[!is.na(beta_coefs)])
beta_coefs <- sort(beta_coefs, decreasing = TRUE)
print(beta_coefs)

cat("\n\n 3. ПРОГНОЗ ДЛЯ РЕСПУБЛИКИ КАРЕЛИЯ \n")

# Находим данные по Карелии
karelia_data <- df_full %>% filter(grepl("Карелия", Region))

if (nrow(karelia_data) > 0) {
  cat("\nДанные по Республике Карелия:\n")
  print(karelia_data %>% select(Year, Income, Population, Latitude, 
                                Distance_to_Moscow, Federal_District, Apartments))
  
  # Делаем прогноз по всем годам для Карелии
  karelia_data$predicted <- predict(model_multiple, newdata = karelia_data)
  
  # Расчет ошибок прогноза
  karelia_data <- karelia_data %>%
    mutate(
      error = Apartments - predicted,
      rel_error = abs(error) / Apartments * 100
    )
  
  cat("\nПрогноз для Республики Карелия (множественная регрессия):\n")
  print(karelia_data %>% 
          select(Year, Apartments, predicted, error, rel_error) %>%
          mutate(across(where(is.numeric), round, 2)))
  
  # Средняя ошибка прогноза
  mean_error <- mean(karelia_data$rel_error, na.rm = TRUE)
  cat(sprintf("\nСредняя относительная ошибка прогноза: %.2f%%", mean_error))
  
  # Для сравнения - простая линейная модель (только доходы)
  model_simple <- lm(Apartments ~ Income, data = df_full)
  karelia_data$predicted_simple <- predict(model_simple, newdata = karelia_data)
  
  karelia_data <- karelia_data %>%
    mutate(
      error_simple = Apartments - predicted_simple,
      rel_error_simple = abs(error_simple) / Apartments * 100
    )
  
  mean_error_simple <- mean(karelia_data$rel_error_simple, na.rm = TRUE)
  cat(sprintf("\nСредняя ошибка простой модели (только доходы): %.2f%%", mean_error_simple))
  
  # Визуализация
  p_compare <- ggplot(karelia_data, aes(x = Year)) +
    geom_line(aes(y = Apartments, color = "Фактические"), size = 1.2) +
    geom_line(aes(y = predicted, color = "Множественная регрессия"), size = 1.2, linetype = "dashed") +
    geom_line(aes(y = predicted_simple, color = "Простая регрессия"), size = 1.2, linetype = "dotted") +
    scale_color_manual(values = c("Фактические" = "blue", 
                                  "Множественная регрессия" = "red",
                                  "Простая регрессия" = "green")) +
    labs(
      title = "Республика Карелия: сравнение моделей",
      subtitle = sprintf("Ошибка: множественная = %.2f%%, простая = %.2f%%", 
                         mean_error, mean_error_simple),
      x = "Год",
      y = "Количество построенных квартир",
      color = ""
    ) +
    theme_minimal() +
    theme(legend.position = "bottom")
  
  print(p_compare)
  
} else {
  cat("\nДанные по Республике Карелия не найдены!")
}