from bs4 import BeautifulSoup
import requests
import telebot
from HdRezkaApi import *
from telebot import types
import base64

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36'}
TOKEN = '6162235622:AAGkwkn6H8cCf7NQKaQfyO25r-7tI0RV3SI'
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start', 'help'])
def help(message):
    bot.send_message(message.chat.id, '     Просто введите название фильма/сериала который ищете\n'
                                      '     По ссылках(названиях) можете перейти прямо на сайт')

@bot.message_handler(content_types=['text'])
def search(message):
    base = 'https://rezka.ag/search/?do=search&subaction=search&q='
    req = message.text
    html = requests.get(base + req, headers=headers).content
    soup = BeautifulSoup(html, 'lxml')
    final_res = []
    for index, note in enumerate(soup.find_all('div', class_='b-content__inline_item')):
        if index == 3:
            break
        else:
            final_res.append({'name': soup.find_all('div', class_='b-content__inline_item')[index]
                             .find('div', class_='b-content__inline_item-link').find('a').text,
                              'some_inf': soup.find_all('div', class_='b-content__inline_item')[index]
                             .find('div', class_='b-content__inline_item-link')
                             .find('div').text,
                              'img_link': soup.find_all('div', class_='b-content__inline_item')[index]
                             .find('div', class_='b-content__inline_item-cover')
                             .find('img').get('src'),
                              'link': soup.find_all('div', class_='b-content__inline_item')[index]
                             .find('div', class_='b-content__inline_item-cover')
                             .find('a').get('href')})

    @bot.callback_query_handler(func=lambda call: call.data.startswith('movieurl_'))
    def handle_callback(call):
        callbackdata = call.data.split('_')[1:]
        urlmovie = ''.join(callbackdata)
        rezka = HdRezkaApi(urlmovie)        
        if rezka.type == "video.tv_series":
            if None in rezka.getTranslations():
                print("hello")
            else:
                print("bye")
        else:
            if None in rezka.getTranslations():
                stream = rezka.getStream(1, 5)
                global links
                links = stream.videos
                keyboard = types.InlineKeyboardMarkup()           
                for quality, link in links.items():
                    button = types.InlineKeyboardButton(text=quality, callback_data='quality_' + quality)
                    keyboard.add(button)
                bot.send_message(call.message.chat.id, 'Выберите качество видео:', reply_markup=keyboard)
            else:
                bot.send_message(call.message.chat.id, "Ошибка: Не удалось получить ссылку на видео.")
                    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('quality_'))
    def handle_callback(call):
        callbackdata = call.data.split('_')[1:]
        quality = ''.join(callbackdata)
        finalurl = links[quality]
        print(finalurl)
        bot.send_message(call.message.chat.id, finalurl)
                    

    if final_res:
        for note in final_res:
            inf = list(note.values())
            urlmovie = inf[3]
            rezka = HdRezkaApi(urlmovie)
            keyboard = types.InlineKeyboardMarkup()
            button_text = "Смотреть " + inf[0]
            button_callback = urlmovie
            button = types.InlineKeyboardButton(text=button_text, callback_data='movieurl_' + button_callback)
            keyboard.add(button)
            bot.send_photo(message.chat.id, inf[2], inf[1].format(message.from_user, bot.get_me()),
                           parse_mode='html', reply_markup=keyboard)
            if rezka.type == "da":
                seriesdata = rezka.getSeasons()
                list_button_name = seriesdata[None]['seasons']
                latest_season = max(seriesdata[None]['seasons'], key=int)
                buttons = []
                for item in list_button_name:
                    button_text = {item}
                    button = types.InlineKeyboardButton(text=button_text, callback_data=item)
                    buttons.append(button)
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(*buttons)
                bot.send_message(message.chat.id, 'В сериале' + latest_season + 'сезонов'.format(message.from_user, bot.get_me()), reply_markup=keyboard)

    else:
        bot.send_message(message.chat.id, 'Ничего не найдено')

bot.polling(none_stop=True)
