from datetime import datetime, timedelta

# Эстонские государственные праздники с фиксированными датами
estonian_fixed_holidays = {
    'new_year': {
        'date': "01.01",
        'name_eng': "New Year's Day",
        'name_est': "Uusaasta",
        'name_rus': "Новый год"
    },
    'independence_day': {
        'date': "24.02",
        'name_eng': "Independence Day",
        'name_est': "Iseseisvuspäev",
        'name_rus': "День независимости"
    },
    'spring_day': {
        'date': "01.05",
        'name_eng': "Spring Day",
        'name_est': "Kevadpüha",
        'name_rus': "День весны"
    },
    'victory_day': {
        'date': "23.06",
        'name_eng': "Victory Day",
        'name_est': "Võidupüha",
        'name_rus': "День победы"
    },
    'midsummer_day': {
        'date': "24.06",
        'name_eng': "Midsummer Day",
        'name_est': "Jaanipäev",
        'name_rus': "Иванова ночь"
    },
    'restoration_independence_day': {
        'date': "20.08",
        'name_eng': "Restoration of Independence Day",
        'name_est': "Taasiseseisvumispäev",
        'name_rus': "День восстановления независимости"
    },
    'christmas_eve': {
        'date': "24.12",
        'name_eng': "Christmas Eve",
        'name_est': "Jõululaupäev",
        'name_rus': "Канун Рождества"
    },
    'christmas_day': {
        'date': "25.12",
        'name_eng': "Christmas Day",
        'name_est': "Esimene jõulupüha",
        'name_rus': "Первый день Рождества"
    },
    'boxing_day': {
        'date': "26.12",
        'name_eng': "Boxing Day",
        'name_est': "Teine jõulupüha",
        'name_rus': "Второй день Рождества"
    }
}

# Русские праздники с фиксированными датами
russian_fixed_holidays = {
    'ru_victory_day': {
        'date': "09.05",
        'name_eng': "Victory Day",
        'name_rus': "День Победы"
    },
    'ru_defender_of_fatherland_day': {
        'date': "23.02",
        'name_eng': "Defender of the Fatherland Day",
        'name_rus': "День защитника Отечества"
    }
}

# Функция для вычисления даты Пасхи
def calc_easter_date(year):
    a = year % 19
    b = year % 4
    c = year % 7
    d = (19 * a + 24) % 30
    e = ((2 * b) + (4 * c) + (6 * d) + 5) % 7

    # Специальные годы
    if year in [1954, 1981, 2049, 2076]:
        date_of_easter = (22 + d + e) - 7
    else:
        date_of_easter = 22 + d + e

    return (4, date_of_easter - 31) if date_of_easter > 31 else (3, date_of_easter)

def get_floating_holidays(year):
    """Возвращает список плавающих праздников для данного года."""
    easter_date = datetime(year, *calc_easter_date(year))
    mother_date = datetime(year, 5, 1) + timedelta(days=(6 - datetime(year, 5, 1).weekday() + 7))
    father_date = datetime(year, 11, 1) + timedelta(days=(6 - datetime(year, 11, 1).weekday() + 14))
    
    return {
        'easter': {
            'date': easter_date,  # Assume `easter_date` is dynamically calculated
            'name_eng': "Easter",
            'name_rus': "Пасха",
            'name_est': "Lihavõtted"
        },
        'mother_day': {
            'date': mother_date,  # Assume `mother_date` is dynamically calculated
            'name_eng': "Mother's Day",
            'name_rus': "День матери",
            'name_est': "Emadepäev"
        },
        'father_day': {
            'date': father_date,  # Assume `father_date` is dynamically calculated
            'name_eng': "Father's Day",
            'name_rus': "День отца",
            'name_est': "Isadepäev"
        }
    }

def print_holidays(holidays, title):
    """Выводит праздники из списка."""
    print(f"\n{title}:")
    for holiday, date in holidays:
        print(f"{holiday}: {date.strftime('%Y-%m-%d')}")

if __name__ == '__main__':
    print(get_floating_holidays(2024))