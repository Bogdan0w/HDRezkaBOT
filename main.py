from bs4 import BeautifulSoup
import requests
import telebot
from HdRezkaApi import *

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
    if final_res:
        for note in final_res:
            inf = list(note.values())
            urlmovie = inf[3]
            rezka = HdRezkaApi(urlmovie)
            if rezka.type == "video.tv_series":
                seriesdata = rezka.getSeasons()
                print(seriesdata[1])
                
                bot.send_message(message.chat.id, f''.format(message.from_user, bot.get_me()))
            finalurl = rezka.getStream('1', '1')('720p')
            bot.send_photo(message.chat.id, inf[2], f'<b><a href="{finalurl}">{inf[0]}</a></b>\n{inf[1]}'.format(message.from_user, bot.get_me()),
                           parse_mode='html')
        if len(soup.find_all('div', class_='b-content__inline_item')) > 3:
            bot.send_message(message.chat.id, f'<b><a href="{base+req}">БОЛЬШЕ РЕЗУЛЬТАТОВ ЗДЕСЬ</a></b>'.format(message.from_user, bot.get_me()),
                            parse_mode='html')
    else:
        bot.send_message(message.chat.id, 'Ничего не найдено')

bot.polling(none_stop=True)
