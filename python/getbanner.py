
import os
import sys
import re
import io
import json

import requests
from bs4 import BeautifulSoup

RATES = {}
NUMBER_LINE_LONE, NUMBER_LINE_TENTH = [], []


def split_lone_and_tenth(rates):
    #some cells have both lone and tenth encounter rates in one, with tenth encounter in parens, like: 0.10%(2.84%)
    #return both lone and tenth, if no tenth return None
    lone = rates[0:rates.find('(')] if rates.find('(') >= 0 else rates
    tenth_list = re.findall('\(([^)]+)', rates)
    tenth = tenth_list[0] if tenth_list else None

    return(lone, tenth)


def merge_and_dump_rates(banner_name, rate_up):
    full_banner = {
        'name' : banner_name,
        'rate_up' : rate_up,
        'range_rows' : {'lone' : NUMBER_LINE_LONE, 'tenth' : NUMBER_LINE_TENTH}
    }
    filename = os.path.join(os.getcwd(), os.pardir, 'banners', banner_name + '.json')
    with io.open(filename, 'w', encoding='utf-8') as bannerf:
        json.dump(full_banner, bannerf, indent=4)
    print(filename, 'saved to disk!')


def rounding(rate):
    return str(round(rate, 2))


def scrape_html(url):
    my_request = requests.get(url)

    #should be html in unicode; .text = content of the response in unicode #http://docs.python-requests.org/en/master/api/#requests.Response
    html = my_request.text

    soup = BeautifulSoup(html, 'html.parser')

    last_character = ''
    start_range_lone, start_range_tenth = 0.0, 0.0

    for table in soup.find_all('table', limit=1):
        for tr in table.find_all('tr'):
            as_character = '' if not tr.find('td', class_='style') else last_character + '(AS)'
            for idx, td in enumerate(tr.find_all('td')):
                if idx == 0: #character name
                    character = td.string if not as_character else as_character
                    last_character = character
                if idx == 1 and td.string: #3 star rates
                    NUMBER_LINE_LONE.append({
                        'name' : character,
                        'rarity' : 3,
                        'start_range' : start_range_lone,
                        'end_range' : start_range_lone + (float(td.string[:-1]) / 100)
                    })
                    start_range_lone += (float(td.string[:-1]) / 100)
                if idx == 2 and td.string: #4 star rates
                    lone, tenth = split_lone_and_tenth(td.string)
                    NUMBER_LINE_LONE.append({
                        'name' : character,
                        'rarity' : 4,
                        'start_range' : start_range_lone,
                        'end_range' : start_range_lone + (float(lone[:-1]) / 100)
                    })
                    start_range_lone += (float(lone[:-1]) / 100)
                    if tenth:
                        NUMBER_LINE_TENTH.append({
                            'name' : character,
                            'rarity' : 4,
                            'start_range' : start_range_tenth,
                            'end_range' : start_range_tenth + (float(tenth[:-1]) / 100)
                        })
                        start_range_tenth += (float(tenth[:-1]) / 100)
                if idx == 3 and td.string: #5 star rates
                    lone, tenth = split_lone_and_tenth(td.string)
                    NUMBER_LINE_LONE.append({
                        'name' : character,
                        'rarity' : 5,
                        'start_range' : start_range_lone,
                        'end_range' : start_range_lone + (float(lone[:-1]) / 100)
                    })
                    start_range_lone += (float(lone[:-1]) / 100)
                    if tenth:
                        NUMBER_LINE_TENTH.append({
                            'name' : character,
                            'rarity' : 5,
                            'start_range' : start_range_tenth,
                            'end_range' : start_range_tenth + (float(tenth[:-1]) / 100)
                        })
                        start_range_tenth += (float(tenth[:-1]) / 100)


def main():
    url = 'https://api-us.another-eden.games/asset/lottery_notice/view/fccc479020e53a780a51064b13b3b878?language=en'
    banner_name = 'Manifestation Weapon Discovery Claude Tsukiha'
    rate_up = ['Tsukiha','Claude']

    scrape_html(url)

    merge_and_dump_rates(banner_name, rate_up)



if __name__ == '__main__':
    main()