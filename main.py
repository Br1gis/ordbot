import telebot
from telebot import types
import time
import sqlite3
import config
from datetime import datetime
from pytz import timezone
import schedule
import threading



client = telebot.TeleBot(config.token)


curr_question_number = 1


list_of_answers = []

list_of_photonums = [1, 2, 3, 5, 9, 10, 13]

finally_text = []

need_number_for_13 = 0

times_for_remind = ['10:00', '14:00', '20:42']


regions = ['Europe/Moscow', 'Asia/Beijing', 'America/New_York']



global db
db = sqlite3.connect('botdb.sqlite3', check_same_thread=False)
global sql
sql = db.cursor()




@client.message_handler(content_types = ['text'])
def get_text(message):
    
    
    if message.text == "/start":
        check_reg(message)
    if message.text == '/admin':
        sql.execute(f"SELECT username FROM admins WHERE id = {message.chat.id}")
        if sql.fetchone() is None:
            pass
        else:
            admin_menu(message)
    if message.text == 'Рассылка':
        sql.execute(f"SELECT username FROM admins WHERE id = {message.chat.id}")
        if sql.fetchone()[0] is None:
            pass
        else:
            reply_markup = types.ReplyKeyboardMarkup(resize_keyboard = True)

            backup = types.KeyboardButton(text="Отмена")

            reply_markup.add(backup)
            msg = client.send_message(message.chat.id, '*Напишите текст для рассылки:*', parse_mode="Markdown", reply_markup=reply_markup)
            client.register_next_step_handler(msg, mailing)
    # if message.text == 'Назад':
    #     main_menu(message)
    # if message.text == 'Напомнить позже':
    #     print('2322fgfgjn')
    #     sql.execute('UPDATE users SET notif_status = ? WHERE id = ?', (1, message.chat.id))
    #     db.commit()
    #     client.send_message(message.chat.id, '*Уведомления успешно включены!*', parse_mode="Markdown")
    #     time.sleep(1)
    #     main_menu(message)
    # if message.text == 'Выключить уведомления':
    #     sql.execute('UPDATE users SET notif_status = ? WHERE id = ?', (0, message.chat.id))
    #     db.commit()
    #     client.send_message(message.chat.id, '*Уведомления успешно выключены!*', parse_mode="Markdown")
    #     time.sleep(1)
    #     main_menu(message)



@client.callback_query_handler(func=lambda call: True)
def callback_handler(call):

    for i in sql.execute(f"SELECT current_qnum FROM users WHERE id = {call.message.chat.id}"):
        global curr_question_number
        curr_question_number = int(i[0])
        break
    global need_number_for_13


    if call.data == 'next1':
        markup_inline = types.InlineKeyboardMarkup(row_width = 1)
        second_next = types.InlineKeyboardButton(text="Далее", callback_data="next2")
        markup_inline.add(second_next)#☘️Диагностический бот\n\nНесет за собой только рекомендательный характер\n\nВсе вопросы здоровья решайте со своим лечащим врачом
        client.edit_message_text(chat_id = call.message.chat.id, message_id = call.message.message_id, text =  f'*☘️Диагностический бот\n\nНесет за собой только рекомендательный характер\n\nВсе вопросы здоровья решайте со своим лечащим врачом*', parse_mode = "Markdown", reply_markup=markup_inline)
    if call.data == 'next2':
        #client.edit_message_text(chat_id = call.message.chat.id, message_id = call.message.message_id, text =  f'*☘️Вся информация сохранна и конфиденциальна\n\nПрохождение теста занимает всего 20-35 минут в течении дня\n\nP.S. Данный метод не имеет аналогов на просторе интернета*', parse_mode = "Markdown")
        markup_inline = types.InlineKeyboardMarkup(row_width = 1)
        third_next = types.InlineKeyboardButton(text="Далее", callback_data="next3")
        markup_inline.add(third_next)
        client.edit_message_text(chat_id = call.message.chat.id, message_id = call.message.message_id, text =  f'*☘️Вся информация сохранна и конфиденциальна\n\nПрохождение теста занимает всего 20-35 минут в течении дня\n\nP.S. Данный метод не имеет аналогов на просторе интернета*', parse_mode = "Markdown", reply_markup=markup_inline)
    if call.data == 'next3':
        markup_inline = types.InlineKeyboardMarkup(row_width = 1)
        region1 = types.InlineKeyboardButton(text="Европа(СНГ)", callback_data="Europe/Moscow")
        region2 = types.InlineKeyboardButton(text="Азия", callback_data="Asia/Vladivostok")
        region3 = types.InlineKeyboardButton(text="Америка", callback_data="America/New_York")
        markup_inline.add(region1, region2, region3)
        client.edit_message_text(chat_id = call.message.chat.id, message_id = call.message.message_id, text =  f'*☘️Перед тем, как мы начнём, пожалуйста, выберите свой регион*', parse_mode = "Markdown", reply_markup=markup_inline)
    if call.data in regions:
        sql.execute(f'UPDATE users SET time_region = ? WHERE id = ?', (call.data, call.message.chat.id,))
        db.commit()
        client.edit_message_text(chat_id = call.message.chat.id, message_id = call.message.message_id, text =  f'*☘️Большое спасибо! Переносим вас в главное меню...*', parse_mode = "Markdown")
        time.sleep(2)
        main_menu(call.message) 
    if call.data == 'start_test':
        starting_testing(call.message)
    if call.data == 'remind_later':
        sql.execute('UPDATE users SET notif_status = ? WHERE id = ?', (1, call.message.chat.id))
        db.commit()
        msg = client.send_message(call.message.chat.id, '*Уведомления успешно включены!*', parse_mode="Markdown")
        time.sleep(1)
        inline_markup = types.InlineKeyboardMarkup(row_width=1)

        start_test = types.InlineKeyboardButton(text="Начать тест", callback_data='start_test')
        remind_button = types.InlineKeyboardButton(text="Выключить уведомления", callback_data='remind_later')
        
        inline_markup.add(start_test, remind_button)
        client.delete_message(call.message.chat.id, msg.message_id)
        client.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='*Используйте кнопки ниже ⬇️*', parse_mode="Markdown", reply_markup=inline_markup)
        
    if call.data == 'off_notif':
        sql.execute('UPDATE users SET notif_status = ? WHERE id = ?', (0, call.message.chat.id))
        db.commit()
        msg = client.send_message(call.message.chat.id, '*Уведомления успешно выключены!*', parse_mode="Markdown")
        time.sleep(2)
        inline_markup = types.InlineKeyboardMarkup(row_width=1)

        start_test = types.InlineKeyboardButton(text="Начать тест", callback_data='start_test')
        remind_button = types.InlineKeyboardButton(text="Напомнить позже", callback_data='remind_later')
        
        inline_markup.add(start_test, remind_button)
        client.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='*Используйте кнопки ниже ⬇️*', parse_mode="Markdown", reply_markup=markup_inline)
        client.delete_message(call.message.chat.id, msg.message_id)
    if call.data == '1':
        print('colda??7')
        if curr_question_number == 13:
            print('superlol')
            need_number_for_13 = 50
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
        elif curr_question_number == 14:
            number_of_pulse = 50 - need_number_for_13
            print(number_of_pulse)
            print('lol')
            if number_of_pulse < 10:
                ansnum = 1
                print('spammm')
                sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {int(call.data)}")
                text_chap = sql.fetchone()[0]
                sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
                last_test_res = sql.fetchone()[0]
                if last_test_res is None or last_test_res == '0':
                    
                    itog = text_chap + '\n'
                    print(itog)
                    sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                    db.commit()
                    #finally_text.append(f"{sql.fetchone()[0]}\n")
                    sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                    db.commit()
                    question_handler(call.message)
                else:
                    itog = f'{last_test_res}{text_chap}\n'
                    sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                    db.commit()
                    #finally_text.append(f"{sql.fetchone()[0]}\n")
                    sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                    db.commit()
                    question_handler(call.message)
            else:
                ansnum = 2
                print('spammm')
                sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {ansnum}")
                text_chap = sql.fetchone()[0]
                sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
                last_test_res = sql.fetchone()[0]
                if last_test_res is None:
                    
                    itog = text_chap + '\n'
                    print(itog)
                    sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                    db.commit()
                    #finally_text.append(f"{sql.fetchone()[0]}\n")
                    sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                    db.commit()
                    question_handler(call.message)
                else:
                    itog = f'{last_test_res}{text_chap}\n'
                    sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                    db.commit()
                    #finally_text.append(f"{sql.fetchone()[0]}\n")
                    sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                    db.commit()
                    question_handler(call.message)
        else:
            print('spammm')
            sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {int(call.data)}")
            text_chap = sql.fetchone()[0]
            sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
            last_test_res = sql.fetchone()[0]
            if last_test_res is None:
                
                itog = text_chap + '\n'
                print(itog)
                sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                db.commit()
                #finally_text.append(f"{sql.fetchone()[0]}\n")
                sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                db.commit()
                question_handler(call.message)
            else:
                itog = f'{last_test_res}{text_chap}\n'
                sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                db.commit()
                #finally_text.append(f"{sql.fetchone()[0]}\n")
                sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                db.commit()
                question_handler(call.message)
    if call.data == '2':
        print('colda??7')
        if curr_question_number == 13:
            print('superlol')
            need_number_for_13 = 50
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
        elif curr_question_number == 14:
            number_of_pulse = 50 - need_number_for_13
            print(number_of_pulse)
            print('lol')
            if number_of_pulse < 10:
                ansnum = 1
                print('spammm')
                sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {int(call.data)}")
                text_chap = sql.fetchone()[0]
                sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
                last_test_res = sql.fetchone()[0]
                if last_test_res is None:
                    
                    itog = text_chap + '\n'
                    print(itog)
                    sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                    db.commit()
                    #finally_text.append(f"{sql.fetchone()[0]}\n")
                    sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                    db.commit()
                    question_handler(call.message)
                else:
                    itog = f'{last_test_res}{text_chap}\n'
                    sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                    db.commit()
                    #finally_text.append(f"{sql.fetchone()[0]}\n")
                    sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                    db.commit()
                    question_handler(call.message)
            else:
                ansnum = 2
                print('spammm')
                sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {ansnum}")
                text_chap = sql.fetchone()[0]
                sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
                last_test_res = sql.fetchone()[0]
                if last_test_res is None:
                    
                    itog = text_chap + '\n'
                    print(itog)
                    sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                    db.commit()
                    #finally_text.append(f"{sql.fetchone()[0]}\n")
                    sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                    db.commit()
                    question_handler(call.message)
                else:
                    itog = f'{last_test_res}{text_chap}\n'
                    sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                    db.commit()
                    #finally_text.append(f"{sql.fetchone()[0]}\n")
                    sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                    db.commit()
                    question_handler(call.message)
        else:
            print('spammm')
            sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {int(call.data)}")
            text_chap = sql.fetchone()[0]
            sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
            last_test_res = sql.fetchone()[0]
            if last_test_res is None:
                
                itog = text_chap + '\n'
                print(itog)
                sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                db.commit()
                #finally_text.append(f"{sql.fetchone()[0]}\n")
                sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                db.commit()
                question_handler(call.message)
            else:
                itog = f'{last_test_res}{text_chap}\n'
                sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                db.commit()
                #finally_text.append(f"{sql.fetchone()[0]}\n")
                sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                db.commit()
                question_handler(call.message)
    if call.data == '3':
        print('colda??7')
        if curr_question_number == 13:
            print('superlol')
            need_number_for_13 = 60
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
        elif curr_question_number == 14:
            number_of_pulse = 60 - need_number_for_13
            print(number_of_pulse)
            print('lol')
            if number_of_pulse < 10:
                ansnum = 1
                print('spammm')
                sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {int(call.data)}")
                text_chap = sql.fetchone()[0]
                sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
                last_test_res = sql.fetchone()[0]
                if last_test_res is None:
                    
                    itog = text_chap + '\n'
                    print(itog)
                    sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                    db.commit()
                    #finally_text.append(f"{sql.fetchone()[0]}\n")
                    sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                    db.commit()
                    question_handler(call.message)
                else:
                    itog = f'{last_test_res}{text_chap}\n'
                    sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                    db.commit()
                    #finally_text.append(f"{sql.fetchone()[0]}\n")
                    sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                    db.commit()
                    question_handler(call.message)
            else:
                ansnum = 2
                print('spammm')
                sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {ansnum}")
                text_chap = sql.fetchone()[0]
                sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
                last_test_res = sql.fetchone()[0]
                if last_test_res is None:
                    
                    itog = text_chap + '\n'
                    print(itog)
                    sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                    db.commit()
                    #finally_text.append(f"{sql.fetchone()[0]}\n")
                    sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                    db.commit()
                    question_handler(call.message)
                else:
                    itog = f'{last_test_res}{text_chap}\n'
                    sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                    db.commit()
                    #finally_text.append(f"{sql.fetchone()[0]}\n")
                    sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                    db.commit()
                    question_handler(call.message)
        else:
            print('spammm')
            sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {int(call.data)}")
            text_chap = sql.fetchone()[0]
            sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
            last_test_res = sql.fetchone()[0]
            if last_test_res is None:
                
                itog = text_chap + '\n'
                print(itog)
                sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                db.commit()
                #finally_text.append(f"{sql.fetchone()[0]}\n")
                sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                db.commit()
                question_handler(call.message)
            else:
                itog = f'{last_test_res}{text_chap}\n'
                sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                db.commit()
                #finally_text.append(f"{sql.fetchone()[0]}\n")
                sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                db.commit()
                question_handler(call.message)
    if call.data == '4':
        print('colda??7')
        if curr_question_number == 13:
            print('superlol')
            need_number_for_13 = 70
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
        elif curr_question_number == 14:
            number_of_pulse = 70 - need_number_for_13
            print(number_of_pulse)
            print('lol')
            if number_of_pulse < 10:
                ansnum = 1
                print('spammm')
                text_chap = ''
                for ij in sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {int(call.data)}"):
                    text_chap = ij[0]
                    break
                print(text_chap + 'chpeeek')
                
                sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
                last_test_res = sql.fetchone()[0]
                if last_test_res is None:
                    itog = text_chap + '\n'
                    print(itog)
                    sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                    db.commit()
                    #finally_text.append(f"{sql.fetchone()[0]}\n")
                    sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                    db.commit()
                    question_handler(call.message)
                else:
                    itog = f'{last_test_res}{text_chap}\n'
                    sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                    db.commit()
                    #finally_text.append(f"{sql.fetchone()[0]}\n")
                    sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                    db.commit()
                    question_handler(call.message)
            else:
                ansnum = 2
                print('spammm')
                for ij in sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {ansnum}"):
                    text_chap = ij[0]
                    break
                sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
                last_test_res = sql.fetchone()[0]
                if last_test_res is None:
                    
                    itog = text_chap + '\n'
                    print(itog)
                    sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                    db.commit()
                    #finally_text.append(f"{sql.fetchone()[0]}\n")
                    sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                    db.commit()
                    question_handler(call.message)
                else:
                    itog = f'{last_test_res}{text_chap}\n'
                    sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                    db.commit()
                    #finally_text.append(f"{sql.fetchone()[0]}\n")
                    sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                    db.commit()
                    question_handler(call.message)
        else:
            print('spammm')
            for ij in sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {int(call.data)}"):
                text_chap = ij[0]
                break
            sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
            last_test_res = sql.fetchone()[0]
            if last_test_res is None:
                
                itog = text_chap + '\n'
                print(itog)
                sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                db.commit()
                #finally_text.append(f"{sql.fetchone()[0]}\n")
                sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                db.commit()
                question_handler(call.message)
            else:
                itog = f'{last_test_res}{text_chap}\n'
                sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                db.commit()
                #finally_text.append(f"{sql.fetchone()[0]}\n")
                sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                db.commit()
                question_handler(call.message)
    if call.data == '5':
        text_chap = ''
        print('colda??7')
        if curr_question_number == 13:
            print('superlol')
            need_number_for_13 = 80
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
        elif curr_question_number == 14:
            number_of_pulse = 80 - need_number_for_13
            print(number_of_pulse)
            print('lol')
            if number_of_pulse < 10:
                ansnum = 1
                print('spammm')
                for ij in sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {int(call.data)}"):
                    text_chap = ij[0]
                    break
                sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
                last_test_res = sql.fetchone()[0]
                if last_test_res is None:
                    
                    itog = text_chap + '\n'
                    print(itog)
                    sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                    db.commit()
                    #finally_text.append(f"{sql.fetchone()[0]}\n")
                    sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                    db.commit()
                    question_handler(call.message)
                else:
                    itog = f'{last_test_res}{text_chap}\n'
                    sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                    db.commit()
                    #finally_text.append(f"{sql.fetchone()[0]}\n")
                    sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                    db.commit()
                    question_handler(call.message)
            else:
                ansnum = 2
                print('spammm')
                for ij in sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {int(call.data)}"):
                    text_chap = ij[0]
                    break
                sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
                last_test_res = sql.fetchone()[0]
                if last_test_res is None:
                    
                    itog = text_chap + '\n'
                    print(itog)
                    sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                    db.commit()
                    #finally_text.append(f"{sql.fetchone()[0]}\n")
                    sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                    db.commit()
                    question_handler(call.message)
                else:
                    itog = f'{last_test_res}{text_chap}\n'
                    sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                    db.commit()
                    #finally_text.append(f"{sql.fetchone()[0]}\n")
                    sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                    db.commit()
                    question_handler(call.message)
        else:
            print('spammm')
            for ij in sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {int(call.data)}"):
                text_chap = ij[0]
                break
            sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
            last_test_res = sql.fetchone()[0]
            if last_test_res is None:
                
                itog = text_chap + '\n'
                print(itog)
                sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                db.commit()
                #finally_text.append(f"{sql.fetchone()[0]}\n")
                sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                db.commit()
                question_handler(call.message)
            else:
                itog = f'{last_test_res}{text_chap}\n'
                sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                db.commit()
                #finally_text.append(f"{sql.fetchone()[0]}\n")
                sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                db.commit()
                question_handler(call.message)
    if call.data == '6':
        text_chap = ''
        print('colda??7')
        if curr_question_number == 13:
            print('superlol')
            need_number_for_13 = 90
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
        elif curr_question_number == 14:
            number_of_pulse = 90 - need_number_for_13
            print(number_of_pulse)
            print('lol')
            if number_of_pulse < 10:
                ansnum = 1
                print('spammm')
                for ij in sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {int(call.data)}"):
                    text_chap = ij[0]
                    break
                sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
                last_test_res = sql.fetchone()[0]
                if last_test_res is None:
                    
                    itog = text_chap + '\n'
                    print(itog)
                    sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                    db.commit()
                    #finally_text.append(f"{sql.fetchone()[0]}\n")
                    sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                    db.commit()
                    question_handler(call.message)
                else:
                    itog = f'{last_test_res}{text_chap}\n'
                    sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                    db.commit()
                    #finally_text.append(f"{sql.fetchone()[0]}\n")
                    sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                    db.commit()
                    question_handler(call.message)
            else:
                ansnum = 2
                print('spammm')
                for ij in sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {int(call.data)}"):
                    text_chap = ij[0]
                    break
                sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
                last_test_res = sql.fetchone()[0]
                if last_test_res is None:
                    
                    itog = text_chap + '\n'
                    print(itog)
                    sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                    db.commit()
                    #finally_text.append(f"{sql.fetchone()[0]}\n")
                    sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                    db.commit()
                    question_handler(call.message)
                else:
                    itog = f'{last_test_res}{text_chap}\n'
                    sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                    db.commit()
                    #finally_text.append(f"{sql.fetchone()[0]}\n")
                    sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                    db.commit()
                    question_handler(call.message)
        else:
            print('spammm')
            for ij in sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {int(call.data)}"):
                text_chap = ij[0]
                break
            sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
            last_test_res = sql.fetchone()[0]
            if last_test_res is None:
                
                itog = text_chap + '\n'
                print(itog)
                sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                db.commit()
                #finally_text.append(f"{sql.fetchone()[0]}\n")
                sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                db.commit()
                question_handler(call.message)
            else:
                itog = f'{last_test_res}{text_chap}\n'
                sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                db.commit()
                #finally_text.append(f"{sql.fetchone()[0]}\n")
                sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                db.commit()
                question_handler(call.message)
    if call.data == '7':
        text_chap = ''
        print('colda??7')
        if curr_question_number == 13:
            print('superlol')
            need_number_for_13 = 100
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
        elif curr_question_number == 14:
            number_of_pulse = 100 - need_number_for_13
            print(number_of_pulse)
            print('lol')
            if number_of_pulse < 10:
                ansnum = 1
                print('spammm')
                for ij in sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {int(call.data)}"):
                    text_chap = ij[0]
                    break
                sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
                last_test_res = sql.fetchone()[0]
                if last_test_res is None:
                    
                    itog = text_chap + '\n'
                    print(itog)
                    sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                    db.commit()
                    #finally_text.append(f"{sql.fetchone()[0]}\n")
                    sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                    db.commit()
                    question_handler(call.message)
                else:
                    itog = f'{last_test_res}{text_chap}\n'
                    sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                    db.commit()
                    #finally_text.append(f"{sql.fetchone()[0]}\n")
                    sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                    db.commit()
                    question_handler(call.message)
            else:
                ansnum = 2
                print('spammm')
                for ij in sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {int(call.data)}"):
                    text_chap = ij[0]
                    break
                sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
                last_test_res = sql.fetchone()[0]
                if last_test_res is None:
                    
                    itog = text_chap + '\n'
                    print(itog)
                    sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                    db.commit()
                    #finally_text.append(f"{sql.fetchone()[0]}\n")
                    sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                    db.commit()
                    question_handler(call.message)
                else:
                    itog = f'{last_test_res}{text_chap}\n'
                    sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                    db.commit()
                    #finally_text.append(f"{sql.fetchone()[0]}\n")
                    sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                    db.commit()
                    question_handler(call.message)
        else:
            print('spammm')
            for ij in sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {int(call.data)}"):
                text_chap = ij[0]
                break
            sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
            last_test_res = sql.fetchone()[0]
            if last_test_res is None:
                
                itog = text_chap + '\n'
                print(itog)
                sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                db.commit()
                #finally_text.append(f"{sql.fetchone()[0]}\n")
                sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                db.commit()
                question_handler(call.message)
            else:
                itog = f'{last_test_res}{text_chap}\n'
                sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                db.commit()
                #finally_text.append(f"{sql.fetchone()[0]}\n")
                sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                db.commit()
                question_handler(call.message)
    if call.data == '8':
        text_chap = ''
        print('colda??7')
        if curr_question_number == 13:
            print('superlol')
            need_number_for_13 = 100
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
        elif curr_question_number == 14:
            number_of_pulse = 100 - need_number_for_13
            print(number_of_pulse)
            print('lol')
            if number_of_pulse < 10:
                ansnum = 1
                print('spammm')
                for ij in sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {int(call.data)}"):
                    text_chap = ij[0]
                    break
                sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
                last_test_res = sql.fetchone()[0]
                if last_test_res is None:
                    
                    itog = text_chap + '\n'
                    print(itog)
                    sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                    db.commit()
                    #finally_text.append(f"{sql.fetchone()[0]}\n")
                    sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                    db.commit()
                    question_handler(call.message)
                else:
                    itog = f'{last_test_res}{text_chap}\n'
                    sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                    db.commit()
                    #finally_text.append(f"{sql.fetchone()[0]}\n")
                    sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                    db.commit()
                    question_handler(call.message)
            else:
                ansnum = 2
                print('spammm')
                for ij in sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {int(call.data)}"):
                    text_chap = ij[0]
                    break
                sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
                last_test_res = sql.fetchone()[0]
                if last_test_res is None:
                    
                    itog = text_chap + '\n'
                    print(itog)
                    sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                    db.commit()
                    #finally_text.append(f"{sql.fetchone()[0]}\n")
                    sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                    db.commit()
                    question_handler(call.message)
                else:
                    itog = f'{last_test_res}{text_chap}\n'
                    sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                    db.commit()
                    #finally_text.append(f"{sql.fetchone()[0]}\n")
                    sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                    db.commit()
                    question_handler(call.message)
        else:
            print('spammm')
            for ij in sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {int(call.data)}"):
                text_chap = ij[0]
                break
            sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
            last_test_res = sql.fetchone()[0]
            if last_test_res is None:
                
                itog = text_chap + '\n'
                print(itog)
                sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                db.commit()
                #finally_text.append(f"{sql.fetchone()[0]}\n")
                sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                db.commit()
                question_handler(call.message)
            else:
                itog = f'{last_test_res}{text_chap}\n'
                sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
                db.commit()
                #finally_text.append(f"{sql.fetchone()[0]}\n")
                sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
                db.commit()
                question_handler(call.message)
        
        
        
    if call.data == '9':
        
        
        print('spammm')
        sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {int(call.data)}")
        text_chap = sql.fetchone()[0]
        sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
        last_test_res = sql.fetchone()[0]
        if last_test_res is None:
                
            itog = text_chap + '\n'
            print(itog)
            sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
            db.commit()
            #finally_text.append(f"{sql.fetchone()[0]}\n")
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
        else:
            itog = f'{last_test_res}{text_chap}\n'
            sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
            db.commit()
            #finally_text.append(f"{sql.fetchone()[0]}\n")
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
        
        
        
    if call.data == '10':
        print('spammm')
        sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {int(call.data)}")
        text_chap = sql.fetchone()[0]
        sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
        last_test_res = sql.fetchone()[0]
        if last_test_res is None:
                
            itog = text_chap + '\n'
            print(itog)
            sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
            db.commit()
            #finally_text.append(f"{sql.fetchone()[0]}\n")
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
        else:
            itog = f'{last_test_res}{text_chap}\n'
            sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
            db.commit()
            #finally_text.append(f"{sql.fetchone()[0]}\n")
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
        
        
        
    if call.data == '11':
        print('spammm')
        sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {int(call.data)}")
        text_chap = sql.fetchone()[0]
        sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
        last_test_res = sql.fetchone()[0]
        if last_test_res is None:
                
            itog = text_chap + '\n'
            print(itog)
            sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
            db.commit()
            #finally_text.append(f"{sql.fetchone()[0]}\n")
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
        else:
            itog = f'{last_test_res}{text_chap}\n'
            sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
            db.commit()
            #finally_text.append(f"{sql.fetchone()[0]}\n")
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
    if call.data == '12':
        print('spammm')
        sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {int(call.data)}")
        text_chap = sql.fetchone()[0]
        sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
        last_test_res = sql.fetchone()[0]
        if last_test_res is None:
                
            itog = text_chap + '\n'
            print(itog)
            sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
            db.commit()
            #finally_text.append(f"{sql.fetchone()[0]}\n")
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
        else:
            itog = f'{last_test_res}{text_chap}\n'
            sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
            db.commit()
            #finally_text.append(f"{sql.fetchone()[0]}\n")
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
    if call.data == '13':
        print('spammm')
        sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {int(call.data)}")
        text_chap = sql.fetchone()[0]
        sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
        last_test_res = sql.fetchone()[0]
        if last_test_res is None:
                
            itog = text_chap + '\n'
            print(itog)
            sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
            db.commit()
            #finally_text.append(f"{sql.fetchone()[0]}\n")
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
        else:
            itog = f'{last_test_res}{text_chap}\n'
            sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
            db.commit()
            #finally_text.append(f"{sql.fetchone()[0]}\n")
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
    if call.data == '14':
        print('spammm')
        sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {int(call.data)}")
        text_chap = sql.fetchone()[0]
        sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
        last_test_res = sql.fetchone()[0]
        if last_test_res is None:
                
            itog = text_chap + '\n'
            print(itog)
            sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
            db.commit()
            #finally_text.append(f"{sql.fetchone()[0]}\n")
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
        else:
            itog = f'{last_test_res}{text_chap}\n'
            sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
            db.commit()
            #finally_text.append(f"{sql.fetchone()[0]}\n")
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
    if call.data == '15':
        print('spammm')
        sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {int(call.data)}")
        text_chap = sql.fetchone()[0]
        sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
        last_test_res = sql.fetchone()[0]
        if last_test_res is None:
                
            itog = text_chap + '\n'
            print(itog)
            sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
            db.commit()
            #finally_text.append(f"{sql.fetchone()[0]}\n")
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
        else:
            itog = f'{last_test_res}{text_chap}\n'
            sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
            db.commit()
            #finally_text.append(f"{sql.fetchone()[0]}\n")
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
    if call.data == '16':
        print('spammm')
        sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {int(call.data)}")
        text_chap = sql.fetchone()[0]
        sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
        last_test_res = sql.fetchone()[0]
        if last_test_res is None:
                
            itog = text_chap + '\n'
            print(itog)
            sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
            db.commit()
            #finally_text.append(f"{sql.fetchone()[0]}\n")
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
        else:
            itog = f'{last_test_res}{text_chap}\n'
            sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
            db.commit()
            #finally_text.append(f"{sql.fetchone()[0]}\n")
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
    if call.data == '17':
        print('spammm')
        sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {int(call.data)}")
        text_chap = sql.fetchone()[0]
        sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
        last_test_res = sql.fetchone()[0]
        if last_test_res is None:
                
            itog = text_chap + '\n'
            print(itog)
            sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
            db.commit()
            #finally_text.append(f"{sql.fetchone()[0]}\n")
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
        else:
            itog = f'{last_test_res}{text_chap}\n'
            sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
            db.commit()
            #finally_text.append(f"{sql.fetchone()[0]}\n")
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
    if call.data == '18':
        print('spammm')
        sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {int(call.data)}")
        text_chap = sql.fetchone()[0]
        sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
        last_test_res = sql.fetchone()[0]
        if last_test_res is None:
                
            itog = text_chap + '\n'
            print(itog)
            sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
            db.commit()
            #finally_text.append(f"{sql.fetchone()[0]}\n")
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
        else:
            itog = f'{last_test_res}{text_chap}\n'
            sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
            db.commit()
            #finally_text.append(f"{sql.fetchone()[0]}\n")
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
    if call.data == '19':
        print('spammm')
        sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {int(call.data)}")
        text_chap = sql.fetchone()[0]
        sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
        last_test_res = sql.fetchone()[0]
        if last_test_res is None:
                
            itog = text_chap + '\n'
            print(itog)
            sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
            db.commit()
            #finally_text.append(f"{sql.fetchone()[0]}\n")
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
        else:
            itog = f'{last_test_res}{text_chap}\n'
            sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
            db.commit()
            #finally_text.append(f"{sql.fetchone()[0]}\n")
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
    if call.data == '20':
        print('spammm')
        sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {int(call.data)}")
        text_chap = sql.fetchone()[0]
        sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
        last_test_res = sql.fetchone()[0]
        if last_test_res is None:
                
            itog = text_chap + '\n'
            print(itog)
            sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
            db.commit()
            #finally_text.append(f"{sql.fetchone()[0]}\n")
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
        else:
            itog = f'{last_test_res}{text_chap}\n'
            sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
            db.commit()
            #finally_text.append(f"{sql.fetchone()[0]}\n")
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
    if call.data == '21':
        print('spammm')
        sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {int(call.data)}")
        text_chap = sql.fetchone()[0]
        sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
        last_test_res = sql.fetchone()[0]
        if last_test_res is None:
                
            itog = text_chap + '\n'
            print(itog)
            sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
            db.commit()
            #finally_text.append(f"{sql.fetchone()[0]}\n")
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
        else:
            itog = f'{last_test_res}{text_chap}\n'
            sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
            db.commit()
            #finally_text.append(f"{sql.fetchone()[0]}\n")
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
    if call.data == '22':
        print('spammm')
        sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {int(call.data)}")
        text_chap = sql.fetchone()[0]
        sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
        last_test_res = sql.fetchone()[0]
        if last_test_res is None:
                
            itog = text_chap + '\n'
            print(itog)
            sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
            db.commit()
            #finally_text.append(f"{sql.fetchone()[0]}\n")
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
        else:
            itog = f'{last_test_res}{text_chap}\n'
            sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
            db.commit()
            #finally_text.append(f"{sql.fetchone()[0]}\n")
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
    if call.data == '23':
        print('spammm')
        sql.execute(f"SELECT answ_text FROM answers WHERE que_number = {curr_question_number} AND answ_number = {int(call.data)}")
        text_chap = sql.fetchone()[0]
        sql.execute(f'SELECT test_result FROM users WHERE id = {call.message.chat.id}')
        last_test_res = sql.fetchone()[0]
        if last_test_res is None:
                
            itog = text_chap + '\n'
            print(itog)
            sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
            db.commit()
            #finally_text.append(f"{sql.fetchone()[0]}\n")
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
        else:
            itog = f'{last_test_res}{text_chap}\n'
            sql.execute(f"UPDATE users SET test_result = ? WHERE id = ?", (itog, call.message.chat.id))
            db.commit()
            #finally_text.append(f"{sql.fetchone()[0]}\n")
            sql.execute(f"UPDATE users SET current_qnum = current_qnum + {1} WHERE id = {call.message.chat.id}") 
            db.commit()
            question_handler(call.message)
       



def main_menu(message):
    sql.execute(f'SELECT notif_status FROM users WHERE id = {message.chat.id}')
    if sql.fetchone()[0] == 0:
        inline_markup = types.InlineKeyboardMarkup(row_width=1)

        start_test = types.InlineKeyboardButton(text="Начать тест", callback_data='start_test')
        remind_button = types.InlineKeyboardButton(text="Напомнить позже", callback_data='remind_later')
        
        inline_markup.add(start_test, remind_button)
        client.send_message(message.chat.id, '*Используйте кнопки ниже ⬇️*', parse_mode="Markdown", reply_markup = inline_markup)
    else:
        inline_markup = types.InlineKeyboardMarkup(row_width=1)

        start_test = types.InlineKeyboardButton(text="Начать тест", callback_data='start_test')
        remind_button = types.InlineKeyboardButton(text="Выключить уведомления", callback_data='off_notif')

        inline_markup.add(start_test, remind_button)
        client.send_message(message.chat.id, '*Используйте кнопки ниже ⬇️*', parse_mode="Markdown", reply_markup = inline_markup)



def admin_menu(message, msg_chat_id:int = None, msg_text:str = None):
    if msg_text is None:
        if msg_chat_id is None:
            reply_markup = types.ReplyKeyboardMarkup(resize_keyboard = True)

            mail_ing = types.KeyboardButton(text="Рассылка")

            leave_back = types.KeyboardButton('Назад')

            reply_markup.add(mail_ing, leave_back)
            client.send_message(message.chat.id, '*Админ-панель: *', parse_mode="Markdown", reply_markup = reply_markup)
        else:
            reply_markup = types.ReplyKeyboardMarkup(resize_keyboard = True)

            mail_ing = types.KeyboardButton(text="Рассылка")

            leave_back = types.KeyboardButton('Назад')

            reply_markup.add(mail_ing, leave_back)
            client.send_message(msg_chat_id, '*Админ-панель: *', parse_mode="Markdown", reply_markup = reply_markup)
    
    else:
        if msg_chat_id is None:
            reply_markup = types.ReplyKeyboardMarkup(resize_keyboard = True)

            mail_ing = types.KeyboardButton(text="Рассылка")

            leave_back = types.KeyboardButton('Назад')

            reply_markup.add(mail_ing, leave_back)
            client.send_message(message.chat.id, f'*{msg_text}*', parse_mode="Markdown", reply_markup = reply_markup)
        else:
            reply_markup = types.ReplyKeyboardMarkup(resize_keyboard = True)

            mail_ing = types.KeyboardButton(text="Рассылка")

            leave_back = types.KeyboardButton('Назад')

            reply_markup.add(mail_ing, leave_back)
            client.send_message(msg_chat_id, f'*{msg_text}*', parse_mode="Markdown", reply_markup = reply_markup)
    




def starting_testing(message):
    
    
    user_id = message.from_user.id
    uri = 0
    for i in sql.execute(f"SELECT test_status FROM users WHERE id = {user_id}"):
        uri = i[0]
    if uri == 1:
        client.send_message(message.chat.id, '*У вас уже есть начатый тест*', parse_mode="Markdown")
    else:
        user_id = message.from_user.id
        status = 1
        sql.execute(f"UPDATE users SET test_status = {status} WHERE id = {user_id}")
        db.commit()
        question_handler(message)



def question_handler(message):
    

    sql.execute(f"SELECT current_qnum FROM users WHERE id = {message.chat.id}")
    

    cur_question_number = int(sql.fetchone()[0])
    print(cur_question_number)

    if cur_question_number == 2:
        print('seca')

    if cur_question_number != 16:


        if cur_question_number == 13:
            print('supchik')


        if cur_question_number == 14:
            print('opaaa')


        sql.execute(f"SELECT amount_of_answers FROM questions WHERE q_number = {cur_question_number}")
        am_answ = int(sql.fetchone()[0])
        sql.execute(f"SELECT q_text FROM questions WHERE q_number = {cur_question_number}")
        text_of_question = sql.fetchone()[0]
        
        for a, b, c, d, e, f, g, h, i, ur, k, l, m, n, o, p, q, r, s, x, y, z in sql.execute(f"SELECT ans_1, ans_2, ans_3, ans_4, ans_5, ans_6, ans_7, ans_8, ans_9, ans_10, ans_11, ans_12, ans_13, ans_14, ans_15, ans_16, ans_17, ans_18, ans_19, ans_20, ans_21, ans_22 FROM questions WHERE q_number = {cur_question_number}"):
            answ1 = a
            answ2 = b
            answ3 = c
            answ4 = d
            answ5 = e
            answ6 = f
            answ7 = g
            answ8 = h
            answ9 = i
            answ10 = ur
            answ11 = k
            answ12 = l
            answ13 = m
            answ14 = n
            answ15 = o
            answ16 = p
            answ17 = q
            answ18 = r
            answ19 = s
            answ20 = x
            answ21 = y
            answ22 = z


            list_of_answers.append(answ1+'\n')
            list_of_answers.append(answ2+'\n')   
            list_of_answers.append(answ3+'\n')
            list_of_answers.append(answ4+'\n')
            list_of_answers.append(answ5+'\n')
            list_of_answers.append(answ6+'\n')
            list_of_answers.append(answ7+'\n')
            list_of_answers.append(answ8+'\n')
            list_of_answers.append(answ9+'\n')
            list_of_answers.append(answ10+'\n')
            list_of_answers.append(answ11+'\n')  
            list_of_answers.append(answ12+'\n')
            list_of_answers.append(answ13+'\n')
            list_of_answers.append(answ14+'\n')
            list_of_answers.append(answ15+'\n')
            list_of_answers.append(answ16+'\n')
            list_of_answers.append(answ17+'\n')
            list_of_answers.append(answ18+'\n')
            list_of_answers.append(answ19+'\n')
            list_of_answers.append(answ20+'\n')
            list_of_answers.append(answ21+'\n')
            list_of_answers.append(answ22+'\n')
            print(list_of_answers)
            break


        markup_inline = types.InlineKeyboardMarkup(row_width = 1)

        i = 0


        for i in range(am_answ):
            markup_inline.add(types.InlineKeyboardButton(f'{list_of_answers[i]}', callback_data=f"{i+1}"))
            
        if cur_question_number in list_of_photonums:
            image_file = open(f'{cur_question_number}.png', 'rb')
            client.send_photo(message.chat.id, photo=image_file, caption=f'{text_of_question}')
            time.sleep(3)
            client.send_message(message.chat.id, '*Варианты ответа*', parse_mode="Markdown", reply_markup=markup_inline)
        else:
            client.send_message(message.chat.id, f'{text_of_question}', parse_mode="Markdown")
            time.sleep(3)
            client.send_message(message.chat.id, '*Варианты ответа*', parse_mode="Markdown", reply_markup=markup_inline)
        list_of_answers.clear()
    else:           
        client.send_message(message.chat.id, '*Тест подошёл к концу! Немного подождите, бот обрабатывает ответы...*', parse_mode="Markdown")
        time.sleep(5)
        sql.execute(f"UPDATE users SET test_status = {0} WHERE id = {message.chat.id}")
        db.commit()
        sql.execute(f"SELECT test_result FROM users WHERE id = {message.chat.id}")
        client.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=f'*Результат:*\n\n{"".join(sql.fetchone()[0])}', parse_mode="Markdown")
        list_of_answers.clear()
        sql.execute(f'UPDATE users SET test_result = ? WHERE id = ?', (None, message.chat.id,))
        db.commit()
        sql.execute(f'UPDATE users SET current_qnum = 1 WHERE id = {message.chat.id}')
        db.commit()
        
        
def remind_tumbler(message):
    sql.execute('SELECT * FROM users')
    curer = sql.fetchall()
    for i in curer:
        user_tz = i[8]
        timezone_region = timezone(user_tz)
        dtime = datetime.now(timezone_region)
        region_time = dtime.strftime('%H:%M')
        print(region_time)

        if i[7] == 1:
            if region_time in times_for_remind:
                if i[4] == 0:
                    client.send_message(i[1], '*Не забудьте пройти тест!*', parse_mode="Markdown")
                if i[4] == 1:
                    client.send_message(i[1], '*У вас есть незаконченный тест!*', parse_mode="Markdown")
        else:
            pass


def start_tumb():
    message = ''
    remind_tumbler(message)


def mailing(message):
    admin_chat = message.chat.id
    if message.text == 'Отмена':
        admin_menu(message, msg_chat_id=admin_chat, msg_text='Отмена действия')
    else:
        

        sql.execute('SELECT id FROM users')
        rows = sql.fetchall()
        for row in range(len(rows)):
            if rows[row][0] is None:
                continue
            else:
                time.sleep(1)
                client.send_message(rows[row][0], f'{message.text}', parse_mode = "Markdown")
                print(rows[row][0])
        
        admin_menu(message, msg_chat_id=admin_chat, msg_text='✅ Рассылка завершена!')


def check_reg(message):
    name = message.from_user.first_name
    user_id = message.from_user.id
    sql.execute(f"SELECT id FROM users WHERE id = {user_id}")
    if sql.fetchone() is None:
        user_id = message.from_user.id
        name = message.from_user.first_name
        lastname = message.from_user.last_name
        username = message.from_user.username
        sql.execute(f"INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (username, user_id, name, lastname, 0, None, 1, 0, None,))
        db.commit()
        client.send_message(message.chat.id, '*☘️Данный метод с вероятностью до  95% покажет состояние вашего здоровья и всех органов\n\nОтчет получите здесь в Телеграмме\n\nДаст вам рекомендации по восстановлению здоровья\n\nТочность теста зависит от вашей детальной и правильной информации*', parse_mode = "Markdown")
        time.sleep(3)
        markup_inline = types.InlineKeyboardMarkup(row_width = 1)
        first_next = types.InlineKeyboardButton(text="Далее", callback_data="next1")
        markup_inline.add(first_next)
        client.send_message(message.chat.id, '*Готовы узнать насколько вы здоровы?*', parse_mode="Markdown", reply_markup=markup_inline)
    else:
        main_menu(message)


def set_reminder_schedule():
    schedule.every(60).seconds.do(start_tumb)


def run_reminder_scheduler():
    while True:
        # Запускаем планировщик
        schedule.run_pending()
        time.sleep(1)


def main():
    # Устанавливаем расписание напоминаний
    set_reminder_schedule()

    # Запускаем планировщик напоминаний в отдельном потоке
    scheduler_thread = threading.Thread(target=run_reminder_scheduler).start()

    # Запускаем бота
    print('start')
    while True:
        try:
            client.polling(none_stop=True)
        except Exception as _ex:
            print(_ex)
            time.sleep(15)


if __name__ == '__main__': # чтобы код выполнялся только при запуске в виде сценария, а не при импорте модуля
    main()