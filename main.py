from bs4 import BeautifulSoup
import requests
import telebot
from HdRezkaApi import *
from telebot import types

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
        if index == 1:
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
        global urlmovie
        urlmovie = ''.join(callbackdata)
        rezka = HdRezkaApi(urlmovie)        
        if rezka.type == "video.tv_series":
            if None in rezka.getTranslations():
                global seriesdata
                seriesdata = rezka.getSeasons()
                print(seriesdata)
                seasons = seriesdata[None]['seasons']
                print(seasons)
                keyboard = types.InlineKeyboardMarkup()
                for seasonname in seasons:
                    print(seasonname)
                    button = types.InlineKeyboardButton(text='Сезон ' + seasonname, callback_data='season_' +seasonname)
                    keyboard.add(button)
                bot.send_message(call.message.chat.id, 'Выберите сезон:', reply_markup=keyboard)
            else:
                global seriestranslator
                seriestranslator = rezka.translators
                keyboard = types.InlineKeyboardMarkup() 
                button = types.InlineKeyboardButton(text=ozvuchka, callback_data='ozvuchka_' + ozvuchka)
                keyboard.add(button)
                bot.send_message(call.message.chat.id, 'Выберите озвучку:', reply_markup=keyboard)
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
                global translator
                translator = rezka.translators
                print()
                print(rezka.getTranslations)
                keyboard = types.InlineKeyboardMarkup() 
                for ozvuchka, transnumber in translator.items():
                    print(ozvuchka)
                    button = types.InlineKeyboardButton(text=ozvuchka, callback_data='ozvuchka_' + ozvuchka)
                    keyboard.add(button)
                bot.send_message(call.message.chat.id, 'Выберите озвучку:', reply_markup=keyboard)
     
    @bot.callback_query_handler(func=lambda call: call.data.startswith('ozvuchka_'))
    def handle_callback(call):
        callbackdata = call.data.split('_')[1:]
        callbackozvuchka = ''.join(callbackdata)
        rezka = HdRezkaApi(urlmovie)
        print(callbackozvuchka)
        stream = rezka.getStream(translation=callbackozvuchka)
        global links
        links = stream.videos
        keyboard = types.InlineKeyboardMarkup()
        for quality, link in links.items():
            button = types.InlineKeyboardButton(text=quality, callback_data='quality_' + quality)
            keyboard.add(button)
        bot.send_message(call.message.chat.id, 'Выберите качество видео:', reply_markup=keyboard)
        

    @bot.callback_query_handler(func=lambda call: call.data.startswith('season_'))
    def episode(call):
        callbackdata = call.data.split('_')[1:]
        global season
        season = ''.join(callbackdata)
        episode = seriesdata[None]['episodes'][season]
        print(episode)
        keyboard = types.InlineKeyboardMarkup()
        for episodename in episode:
            button = types.InlineKeyboardButton(text='Серия ' + episodename, callback_data='episode_' + episodename)
            keyboard.add(button)
        bot.send_message(call.message.chat.id, 'Выберите серию:', reply_markup=keyboard)
        
    @bot.callback_query_handler(func=lambda call: call.data.startswith('episode_'))
    def laststepepisodeseason(call):
        callbackdata = call.data.split('_')[1:]
        episode = ''.join(callbackdata)
        rezka = HdRezkaApi(urlmovie)
        stream = rezka.getStream(season, episode)
        global links
        links = stream.videos
        keyboard = types.InlineKeyboardMarkup()
        for quality, link in links.items():
            button = types.InlineKeyboardButton(text=quality, callback_data='quality_' + quality)
            keyboard.add(button)
        bot.send_message(call.message.chat.id, 'Выберите качество видео:', reply_markup=keyboard)
         
    @bot.callback_query_handler(func=lambda call: call.data.startswith('quality_'))
    def handle_callback(call):
        callbackdata = call.data.split('_')[1:]
        quality = ''.join(callbackdata)
        finalurl = links[quality]
        print(finalurl)
        bot.send_message(call.message.chat.id, finalurl, parse_mode='html')
                    

    if final_res:
        for note in final_res:
            inf = list(note.values())
            urlmovie = inf[3]
            keyboard = types.InlineKeyboardMarkup()
            button_text = "Смотреть " + inf[0]
            button_callback = urlmovie
            button = types.InlineKeyboardButton(text=button_text, callback_data='movieurl_' + button_callback)
            keyboard.add(button)
            bot.send_photo(message.chat.id, inf[2], inf[1], reply_markup=keyboard)

    else:
        bot.send_message(message.chat.id, 'Ничего не найдено')

bot.polling(none_stop=True)
