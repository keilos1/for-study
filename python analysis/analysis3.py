import re
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np
import math


def parse_log_file(filename):
    """
    Парсит лог-файл и извлекает данные для устройства A00000000002
    """
    pattern = r'(\d{2}:\d{2}:\d{2},\d{3}).*?A00000000002\s+<--->.*?KEEP.*?volume=(\d+)'

    data = []

    try:
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                match = re.search(pattern, line)
                if match:
                    time_str, volume_str = match.groups()
                    time_str = time_str.replace(',', '.')
                    time_obj = datetime.strptime(time_str, '%H:%M:%S.%f')
                    volume = int(volume_str)
                    data.append((time_obj, volume))

    except FileNotFoundError:
        print(f"Файл {filename} не найден!")
        return []
    except Exception as e:
        print(f"Ошибка чтения файла: {e}")
        return []

    data.sort(key=lambda x: x[0])
    return data


def filter_first_10_minutes(data):
    """
    Фильтрует данные за первые 10 минут
    """
    if not data:
        return []

    start_time = data[0][0]
    end_time = start_time + timedelta(minutes=10)

    filtered_data = [(time, volume) for time, volume in data if time <= end_time]
    return filtered_data


def calculate_10min_averages(data):
    """
    Рассчитывает средние значения volume за 10-минутные интервалы
    """
    if not data:
        return [], []

    start_time = data[0][0]
    intervals = []
    averages = []

    # Обрабатываем максимум 6 интервалов
    for interval_num in range(6):
        current_start = start_time + timedelta(minutes=10 * interval_num)
        current_end = current_start + timedelta(minutes=10)

        # Данные для текущего интервала
        interval_data = [
            volume for time, volume in data
            if current_start <= time < current_end
        ]

        # Округляем и добавляем в массивы
        if interval_data:
            avg_volume = np.mean(interval_data)
            rounded_avg = math.floor(avg_volume)
            averages.append(rounded_avg)
            intervals.append(interval_num)

    return intervals, averages


def create_plots(data, intervals, averages):
    """
    Создает два графика
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    # График 1: Volume за первые 10 минут
    if data:
        times, volumes = zip(*data)
        start_time = times[0]
        time_diffs = [(t - start_time).total_seconds() / 60 for t in times]

        ax1.plot(time_diffs, volumes, 'tab:blue', linewidth=1, label='A00000000002')
        ax1.set_xlabel('')
        ax1.set_ylabel('Volume')
        ax1.set_title('График1. Volume', pad=20)
        ax1.set_xlabel('Время')

        time_labels = [f"01 15:{i:02d}" for i in range(0, 11)]
        ax1.set_xticks(range(0, 11))
        ax1.set_xticklabels(time_labels)

        legend = ax1.legend(loc='upper left', shadow=True, fontsize='10')
        legend.get_frame().set_facecolor('white')

    # График 2: Средние значения за 10-минутные интервалы
    if intervals and averages:
        ax2.plot(intervals, averages, 'tab:blue', linewidth=1, label='A00000000002')  # Добавил точки
        ax2.set_xlabel('Номер 10-минутки')
        ax2.set_ylabel('Volume')
        ax2.set_title('График2. Volume по 10-мин', pad=20)
        ax2.set_xticks(intervals)

        legend = ax2.legend(loc='upper left', shadow=True, fontsize='10')
        legend.get_frame().set_facecolor('white')

    plt.tight_layout()
    plt.show()


def main():
    filename = "n_log2.txt"

    data = parse_log_file(filename)

    if not data:
        print("Данные не найдены")
        return

    first_10min_data = filter_first_10_minutes(data)
    intervals, averages = calculate_10min_averages(data)

    create_plots(first_10min_data, intervals, averages)


if __name__ == "__main__":
    main()
