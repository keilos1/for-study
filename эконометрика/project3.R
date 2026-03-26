# Подключаем необходимые библиотеки
library(readxl)   # для чтения Excel
library(forecast) # для ARIMA и прогнозирования
library(ggplot2)  # для графики

# Чтение данных
# Указываем путь к файлу
file_path <- "G:/Учеба/Эконометрика/monthly-housing-starts-construct-p-1.xls"

# В столбцах: A — дата (Month), B — значения (Contract)
data_raw <- suppressMessages(
  read_excel(file_path, sheet = 1, skip = 1, col_names = FALSE))

# Присваиваем имена столбцам
colnames(data_raw) <- c("Month", "Contracts")

# Преобразуем Month в дату
data_raw$Month <- as.Date(data_raw$Month, format = "%Y-%m")

# Удаляем возможные пропуски
data_clean <- na.omit(data_raw)

# Создаём временной ряд
ts_data <- ts(data_clean$Contracts, start = c(1983, 1), frequency = 12)

# Визуализация исходного ряда
print(autoplot(ts_data) + 
  labs(title = "Monthly Housing Starts (Jan 1983 – Oct 1989)",
       y = "Contracts", x = "Year"))

# Построение модели ARIMA
# Используем auto.arima для выбора лучшей модели
fit <- auto.arima(ts_data, seasonal = TRUE, stepwise = FALSE, approximation = FALSE)

# Вывод информации о подобранной модели
summary(fit)

# Прогноз на 3 шага вперёд
forecast_result <- forecast(fit, h = 3)

# Вывод прогнозных значений
print(forecast_result)

# График прогноза
extended_ts <- ts(c(as.numeric(ts_data), as.numeric(forecast_result$mean)),
                  start = start(ts_data),
                  frequency = frequency(ts_data))

# Создаем отдельный ряд только для прогнозных данных
forecast_only_ts <- ts(as.numeric(forecast_result$mean),
                       start = time(ts_data)[length(ts_data)] + 1/12,
                       frequency = frequency(ts_data))

# Строим график
print(autoplot(extended_ts, series = "Full Series") +
        scale_color_manual(values = c("Full Series" = "black")) +
        autolayer(forecast_only_ts, series = "Forecast") +
        scale_color_manual(name = "Data", 
                           values = c("Full Series" = "black", 
                                      "Forecast" = "blue")) +
        labs(title = "Monthly Housing Starts (Jan 1983 – Oct 1989) with Forecast",
             y = "Contracts", x = "Year") +
        guides(color = "none"))

# Точечный прогноз на 3 лага
cat("\nТочечный прогноз (h=3):\n")

last_date <- max(data_clean$Month)
forecast_dates <- seq(last_date, by = "month", length.out = 4)[-1] # 3 будущих месяца

for (i in 1:3) {
  cat(sprintf("%s: %.2f\n", 
              format(forecast_dates[i], "%b %Y"),
              forecast_result$mean[i]))
}

# 80% доверительные интервалы
cat("\n\n80% доверительные интервалы:\n")
for (i in 1:3) {
  cat(sprintf("%s: [%.2f, %.2f]\n", 
              format(forecast_dates[i], "%b %Y"),
              forecast_result$lower[i,1], forecast_result$upper[i,1]))
}

# 95% доверительные интервалы
cat("\n95% доверительные интервалы:\n")
for (i in 1:3) {
  cat(sprintf("%s: [%.2f, %.2f]\n", 
              format(forecast_dates[i], "%b %Y"),
              forecast_result$lower[i,2], forecast_result$upper[i,2]))
}