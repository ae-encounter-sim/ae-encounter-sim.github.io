
import os
import sys
import re
import io
import json

import requests
from bs4 import BeautifulSoup

RATES = {}
NUMBER_LINE_LONE, NUMBER_LINE_TENTH = [], []


def percent_to_float(rate):
    if not rate:
        return None
    else:
        return float(rate.strip().replace('%','')) / 100.0


def split_lone_and_tenth(rates):
    #some cells have both lone and tenth encounter rates in one, with tenth encounter in parens, like: 0.10%(2.84%)
    #return both lone and tenth, if no tenth return None
    lone = rates[0:rates.find('(')] if rates.find('(') >= 0 else rates
    tenth_list = re.findall('\(([^)]+)', rates)
    tenth = tenth_list[0] if tenth_list else None

    return(percent_to_float(lone), percent_to_float(tenth))


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


def get_style_name(bs_tr, base_character):
    if bs_tr.find('td', class_='Astyle') or bs_tr.find('td', class_='Astyle2') or bs_tr.find('td', class_='style') or bs_tr.find('td', class_='branch_style'):
        return base_character + '(AS)'
    elif bs_tr.find('td', class_='Estyle') or bs_tr.find('td', class_='estyle'):
        return base_character + '(ES)'
    else:
        return None


def scrape_html(url):
    my_request = requests.get(url)

    #should be html in unicode; .text = content of the response in unicode #http://docs.python-requests.org/en/master/api/#requests.Response
    html = my_request.text

    soup = BeautifulSoup(html, 'html.parser')

    base_character = ''
    start_range_lone, start_range_tenth = 0.0, 0.0

    for table in soup.find_all('table', limit=1):
        for tr in table.find_all('tr'):
            style_character = get_style_name(tr, base_character)
            for idx, td in enumerate(tr.find_all('td')):
                if idx == 0: #character name
                    character = td.string.strip() if not style_character else style_character
                    base_character = character if not character[-1] == ')' else base_character
                if idx == 1 and td.string: #3 star rates
                    NUMBER_LINE_LONE.append({
                        'name' : character,
                        'rarity' : 3,
                        'start_range' : start_range_lone,
                        'end_range' : start_range_lone + percent_to_float(td.string)
                    })
                    start_range_lone += percent_to_float(td.string)
                if idx == 2 and td.string: #4 star rates
                    lone, tenth = split_lone_and_tenth(td.string)
                    NUMBER_LINE_LONE.append({
                        'name' : character,
                        'rarity' : 4,
                        'start_range' : start_range_lone,
                        'end_range' : start_range_lone + lone
                    })
                    start_range_lone += lone
                    if tenth:
                        NUMBER_LINE_TENTH.append({
                            'name' : character,
                            'rarity' : 4,
                            'start_range' : start_range_tenth,
                            'end_range' : start_range_tenth + tenth
                        })
                        start_range_tenth += tenth
                if idx == 3 and td.string: #5 star rates
                    lone, tenth = split_lone_and_tenth(td.string)
                    NUMBER_LINE_LONE.append({
                        'name' : character,
                        'rarity' : 5,
                        'start_range' : start_range_lone,
                        'end_range' : start_range_lone + lone
                    })
                    start_range_lone += lone
                    if tenth:
                        NUMBER_LINE_TENTH.append({
                            'name' : character,
                            'rarity' : 5,
                            'start_range' : start_range_tenth,
                            'end_range' : start_range_tenth + tenth
                        })
                        start_range_tenth += tenth


def main():
    url = 'https://api-us.another-eden.games/asset/lottery_notice/view/a3032eee7da3990a9fb1b54898f5902f?language=en'
    banner_name = 'Episode The Lost Tome and the Silver Unfading Flower'
    rate_up = ['Hardy','Cynthia']

    scrape_html(url)

    merge_and_dump_rates(banner_name, rate_up)



if __name__ == '__main__':
    main()