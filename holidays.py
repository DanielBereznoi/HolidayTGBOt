from datetime import datetime, timedelta

# Эстонские государственные праздники с фиксированными датами
estonian_fixed_holidays = [
    ("Новый год", datetime(1, 1, 1)),  # Год здесь не важен
    ("День независимости", datetime(1, 2, 24)),
    ("День весны", datetime(1, 5, 1)),
    ("День победы", datetime(1, 6, 23)),
    ("Иванова ночь", datetime(1, 6, 24)),
    ("День восстановления независимости", datetime(1, 8, 20)),
    ("Канун Рождества", datetime(1, 12, 24)),
    ("Первый день Рождества", datetime(1, 12, 25)),
    ("Второй день Рождества", datetime(1, 12, 26)),
]

# Русские праздники с фиксированными датами
russian_fixed_holidays = [
    ("День Победы", datetime(1, 5, 9)),
]

# Функция для вычисления даты Пасхи
def calcEasterDate(year):
    a = year % 19
    b = year % 4
    c = year % 7
    d = (19 * a + 24) % 30
    e = ((2 * b) + (4 * c) + (6 * d) + 5) % 7

    # Специальные годы
    if year in [1954, 1981, 2049, 2076]:
        dateofeaster = (22 + d + e) - 7
    else:
        dateofeaster = 22 + d + e

    return (4, dateofeaster - 31) if dateofeaster > 31 else (3, dateofeaster)

def get_floating_holidays(year):
    """Возвращает список плавающих праздников для данного года."""
    easter_date = datetime(year, *calcEasterDate(year))
    mother_date = datetime(year, 5, 1) + timedelta(days=(6 - datetime(year, 5, 1).weekday() + 7))
    father_date = datetime(year, 6, 1) + timedelta(days=(6 - datetime(year, 6, 1).weekday() + 14))
    
    return [
        ("Пасха", easter_date),
        ("День матери", mother_date),
        ("День отца", father_date),
    ]

def print_holidays(holidays, title):
    """Выводит праздники из списка."""
    print(f"\n{title}:")
    for holiday, date in holidays:
        print(f"{holiday}: {date.strftime('%Y-%m-%d')}")

if __name__ == "__main__":
    year = datetime.now().year

    # Обновляем даты для фиксированных праздников
    updated_estonian_fixed_holidays = [(name, date.replace(year=year)) for name, date in estonian_fixed_holidays]
    updated_russian_fixed_holidays = [(name, date.replace(year=year)) for name, date in russian_fixed_holidays]
    updated_floating_holidays = get_floating_holidays(year)

    # Печатаем праздники
    print_holidays(updated_estonian_fixed_holidays, "Эстонские государственные праздники")
    print_holidays(updated_russian_fixed_holidays, "Русские праздники")
    print_holidays(updated_floating_holidays, "Плавающие праздники")
