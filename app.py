import os.path

from Strings import *
from telebot import TeleBot
from DbController import User, Database, Mail
from Keyboard import *
import logging
import time, datetime
from random import randint
from threading import Thread
import pickle
logging.basicConfig(filename='error.log',
                    format='[%(asctime)s] => %(message)s',
                    level=logging.ERROR)

bot = TeleBot(API_KEY)


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
            try:
                bot.delete_message(self.__msg.chat.id, self.__msg.id,timeout=timeout)
            except:
                logging.error('delete msg')

    def edit_message(self, text=None, keyboard=None):
        if self.__msg:
            try:
                if text:
                    bot.edit_message_text(text, self.__msg.chat.id, self.__msg.id)
                if keyboard:
                    bot.edit_message_reply_markup(self.__msg.chat.id, self.__msg.id, reply_markup=keyboard)
            except:
                logging.error('edit msg')

    def get_id(self):
        return self.__msg.id


class Chat:
    ST_WAS_APPEND = ST_EDIT
    ST_HOME='home'
    ST_EDIT='edit'
    ST_WAS_DELETE=ST_DELETE


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
            msg.delete_message(timeout=1000)



    def set_state(self, state):
        self.__state = state

    def get_state(self):
        return self.__state

    def get_id_chat(self):
        return self.__id


class Notifier(Thread):
    def __init__(self):
        super().__init__()

    def run(self):
        print('timer run')
        while True:

            if datetime.datetime.now().date() >= datetime.datetime.fromisoformat(END_DATE).date():
                self.select_santa()
                self.select_secret()
                time.sleep(24 * 60 * 60)

    def send_wished(self, chat: Chat):
        if chat.get_message('notify'):
            self.update_notify()
            print(chat.get_id_chat())
        else:
            chat.add_message(Message(TXT_WISHED(db.get_count_wished())),'notify')


    def update_notify(self):

        for chat in chats.values():
            if msg:=chat.get_message('notify'):
                try:
                    msg.edit_message(TXT_WISHED(db.get_count_wished()))
                except:
                    print(f'ipdate {chat.get_id_chat()}')
                    chat.add_message(Message(TXT_WISHED(db.get_count_wished())),'notify')


    def select_secret(self):
        users = db.select(User)
        tmp = []
        import random
        for user in users:
            picks = [i for i in users if i != user and i not in tmp]

            pick = random.choice(picks)

            tmp.append(pick)
            db.update(User,[User.id==user.id],User.id,secret=pick.id)
            if user.chat_id in chats:
                chats[user.chat_id].add_message(Message(f'Письмо для секретного Санты.\n{pick.mail[0].text}'),'secret')
            else:
                chats[user.chat_id]=Chat(user.chat_id)
                chats[user.chat_id].add_message(Message(f'Письмо для секретного Санты.\n{pick.mail[0].text}'), 'secret')


    def select_santa(self):
        if count:=db.get_count_wished()>1:
            santa_id = db.update(User, [User.id == randint(1,count )],returning=User.chat_id ,isSanta= True)
            if santa_id in chats:
                chats[santa_id].add_message(Message(TXT_SANTA),'santa')
            else:
                chats[santa_id]=Chat(santa_id)
                chats[santa_id].add_message(Message(TXT_SANTA),'santa')



def init(message):
    if len(db.select(User, [User.chat_id == message.chat.id, ])) == 0:
        db.insert(User, chat_id=message.chat.id, name=message.from_user.username)

    chats[message.chat.id] = Chat(message.chat.id)

chats = {}
if os.path.exists('dump.pickle'):
    with open('dump.pickle', 'rb') as handle:
        chats = pickle.load(handle)
def main():
    @bot.message_handler(commands=['r'])
    def r(message):
        raise Exception
    @bot.message_handler(commands=['secret'])
    def sec(message):
        Notifier().select_secret()
        Notifier().select_santa()
    @bot.message_handler(content_types=['text'])
    def point(message):
        if message.chat.id not in chats:
            init(message)
        chat = chats[message.chat.id]

        bot.delete_message(message.chat.id,message.id)

        bot.get_chat(message.chat.id)
        match chat.get_state():
            case Chat.ST_HOME:
                if message.text != '/start':
                    chat.get_message('text').delete_message()
                    if len(chat.get_user().mail)>0:
                        db.delete(Mail, [Mail.uid == chat.get_user().id])
                    db.insert(Mail,uid=chat.get_user().id,text=message.text)
                    chat.add_message(Message(f'Твое письмо:',key_main),'body')

                    chat.add_message(Message(f'{chat.get_user().mail[0].text}'),'mail')

                    chat.add_message(Message('Поздравляю! Письмо добавлено.'))

                    db.update(User,[User.id==chat.get_user().id],isWised=True)
                    chat.set_state(Chat.ST_WAS_APPEND)
                    Notifier().send_wished(chat)


                else:
                    chat.add_message(Message('Напиши письмо.'),'text')

            case Chat.ST_EDIT:
                db.update(Mail,[Mail.uid==chat.get_user().id],text=Mail.text+f"\n{message.text}")
                chat.get_message('append').delete_message()
                chat.get_message('mail').edit_message(f'{chat.get_user().mail[0].text}')

                chat.add_message(Message('Письмо дополнено'))
                chat.set_state(Chat.ST_WAS_APPEND)
            case Chat.ST_WAS_APPEND :
                if message.text==Chat.ST_WAS_APPEND:

                    chat.set_state(Chat.ST_EDIT)
                    chat.add_message(Message('Дополни письмо.'), 'append')

                elif message.text == Chat.ST_WAS_DELETE:
                    chat.set_state(Chat.ST_HOME)
                    chat.get_message('mail').delete_message()
                    chat.get_message('body').delete_message()
                    chat.add_message(Message('Напиши письмо.'), 'text')
                elif message.text == '/start':
                    chat.add_message(Message('Напиши письмо.'), 'text')
                    chat.set_state(Chat.ST_HOME)

                else:
                    chat.add_message(Message('Воспользуйся кнопками'))


    # Notifier().start()
    bot.polling(none_stop=True)


if __name__ == "__main__":
    # try:
        main()
    # except Exception as e:
    #     print(e)
    #     with open('dump.pickle', 'wb') as handle:
    #         pickle.dump(chats, handle)
    #         handle.close()
    #     exit(0)
