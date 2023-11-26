from Strings import *
from telebot import TeleBot
from DbController import User, Database, Mail
from Keyboard import *
import logging
from random import randint

logging.basicConfig(filename='error.log',
                    format='[%(asctime)s] => %(message)s',
                    level=logging.ERROR)

bot = TeleBot(API_KEY)
chats = {}
db = Database()




class Message:
    def __init__(self, text, keyboard=None):
        self.__msg = None
        self.text = text
        self.keyboard = keyboard

    def send_message(self, chat_id):
        self.__msg = bot.send_message(chat_id=chat_id, text=self.text, reply_markup=self.keyboard)

    def delete_message(self,timeout=0):
        if self.__msg:
            bot.delete_message(self.__msg.chat.id, self.__msg.id,timeout=timeout)

    def edit_message(self, text=None, keyboard=None):
        if self.__msg:

            if text:
                bot.edit_message_text(text, self.__msg.chat.id, self.__msg.id)
            if keyboard:
                bot.edit_message_reply_markup(self.__msg.chat.id, self.__msg.id, reply_markup=keyboard)

    def get_id(self):
        return self.__msg.id


class Chat:
    ST_WAS_EDIT = ST_EDIT
    ST_HOME='home'
    ST_EDIT='edit'


    def __init__(self, id):
        self.__id = id
        self.__state = self.ST_HOME
        self.__messages = {}

    def get_user(self):
        return db.select(User, [User.chat_id == self.__id], one=True)

    def get_message(self, theme):
        if theme in self.__messages:
            return self.__messages[theme]
        else:
            return None

    def add_message(self, msg: Message,theme=None):
        if theme:
            msg.send_message(self.__id)
            self.__messages[theme]=msg
        else:
            msg.send_message(self.__id)
            msg.delete_message(timeout=3)



    def set_state(self, state):
        self.__state = state

    def get_state(self):
        return self.__state

    def get_id_chat(self):
        return self.__id


class Notifier:
    def timer(self):
        import time, datetime
        while True:
            if datetime.datetime.now().date() >= datetime.datetime.fromisoformat(END_DATE).date():
                self.select_santa()
                self.select_secret()
                time.sleep(24 * 60 * 60)

    def send_wished(self, chat: Chat):

        chat.add_message(Message(TXT_WISHED(db.get_count_wished())),'notify')


    def update_notify(self):

        for chat in chats:
            if msg:=chat.get_message('notify'):
                msg.edit_message(TXT_WISHED(db.get_count_wished()))

    def select_secret(self):
        users = db.select(User)
        tmp = []
        import random
        for user in users:
            picks = [i for i in users if i != user and i not in tmp]

            pick = random.choice(picks)
            tmp.append(pick)
            db.update(User,[User.id==user.id],secret=pick.id)
            chats[user.chat_id].add_message(Message(f'Письмо для секретного Санты.\n{pick.mail[0].text}'),'secret')

    def select_santa(self):
        if count:=db.get_count_wished()>1:
            santa_id = db.update(User, [User.id == randint(1,count )], User.chat_id, {'isSanta': True})
            chats[santa_id].add_message(Message(TXT_SANTA),'santa')


def init(message):
    if len(db.select(User, [User.chat_id == message.chat.id, ])) == 0:
        db.insert(User, chat_id=message.chat.id, name=message.from_user.username)

    chats[message.chat.id] = Chat(message.chat.id)


def main():

    @bot.message_handler(content_types=['text'])
    def point(message):
        if message.chat.id not in chats:
            init(message)
        chat = chats[message.chat.id]

        bot.delete_message(message.chat.id,message.id)


        match chat.get_state():
            case Chat.ST_HOME:
                if message.text != '/start':
                    db.insert(Mail,uid=message.chat.id,text=message.text)
                    chat.add_message(Message(f'Твое письмо:',key_main),'body')
                    chat.add_message(Message(f'{message.text}'),'mail')
                    chat.add_message(Message('Поздравляю! Письмо добавлено.'))
                    chat.get_message('text').delete_message()
                    db.update(User,[User.id==chat.get_user().id],isWised=True)
                    chat.set_state(Chat.ST_WAS_EDIT)
                    Notifier().send_wished(chat)
                else:
                    chat.add_message(Message('Напиши письмо.'),'text')

            case Chat.ST_EDIT:
                chat.get_message('mail').edit_message(f'{message.text}')
                chat.add_message(Message('Письмо изменено'))
                chat.set_state(Chat.ST_WAS_EDIT)
            case Chat.ST_WAS_EDIT :
                if message.text==Chat.ST_WAS_EDIT:

                    chat.set_state(Chat.ST_EDIT)
                else:
                    chat.add_message(Message('Ты уже написал письмо.'))
    # Notifier().timer()
    bot.polling(none_stop=True)

if __name__ == "__main__":
    main()
