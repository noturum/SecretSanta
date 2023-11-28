from telebot import types
from Strings import ST_EDIT,ST_DELETE

key_main = types.ReplyKeyboardMarkup(True,True)
key_main.add(types.KeyboardButton(ST_EDIT),types.KeyboardButton(ST_DELETE))
