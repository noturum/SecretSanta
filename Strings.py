DB = 'sqlite:///data.db'
API_KEY = ''
WISHED_COUNT = 6
ST_EDIT = 'Изменить письмо'
END_DATE = '2023-12-05'
TXT_SANTA = "Поздравляю тебя друг, ты выбран на роль Санты в этом году!"


def TXT_WISHED(count):
    return f'Уже написали сообщение {"🎅🏻" * count} из {WISHED_COUNT}.\n Выбор тайного Санты пройдет 5 декабря!' if count < WISHED_COUNT else f'Все Санты в сборе!\n Выбор тайного Санты пройдет 5 декабря!'
