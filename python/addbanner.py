
import argparse
from datetime import datetime
import glob
import io
import json
import os
import random
import re
import string
import subprocess

from bs4 import BeautifulSoup
import requests
import tinify

import apikeys

def gen_random_version():
    """
    Generate random 10 character alphanumeric string for version numbering
    """
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))


def percent_to_float(rate):
    """
    Take a % string (e.g. '5.17%') and return as a float (0.0517)
    """
    if not rate:
        return None
    else:
        return float(rate.strip().replace('%','')) / 100.0


def split_lone_and_tenth(rates):
    """
    Parse string for lone encounter rate and tenth encounter rate, often 
    represented like: 0.10%(2.84%), and return floats of each
    """
    lone = rates[0:rates.find('(')] if rates.find('(') >= 0 else rates
    tenth_list = re.findall('\(([^)]+)', rates)
    tenth = tenth_list[0] if tenth_list else None

    return(percent_to_float(lone), percent_to_float(tenth))


def merge_and_dump_rates(new_banner, rate_up, range_rows):
    """
    Combine banner attributes and dump json file to banners folder
    """
    full_banner = {
        'name' : new_banner['name'],
        'rate_up' : rate_up,
        'range_rows' : range_rows
    }
    filename = os.path.join(os.getcwd(), os.pardir, 'banners', new_banner['banner_file'])
    with io.open(filename, 'w', encoding='utf-8') as bannerf:
        json.dump(full_banner, bannerf, indent=4)
    print(filename, 'saved to disk!')


def get_style_name(bs_tr, base_character):
    """
    For Another/Extra Style Class names, return character name + AS/ES instead
    """
    if bs_tr.find('td', class_='Astyle') or bs_tr.find('td', class_='Astyle2') or bs_tr.find('td', class_='style') or bs_tr.find('td', class_='branch_style'):
        return base_character + '(AS)'
    elif bs_tr.find('td', class_='Estyle') or bs_tr.find('td', class_='estyle'):
        return base_character + '(ES)'
    else:
        return None


def parse_title(text):
    """
    Remove special characters and return title for file naming
    """
    remove_list = ['3 Times Max ','1 Time Only ', '2 Times Max ', '\'', '"', '<', '>', ':', '/']
    for rm_str in remove_list:
        text = text.replace(rm_str, '')
    if 'Seven Days Encounter' in text:
        text += datetime.now().strftime(' %B %Y')
    return text


def parse_characters(text):
    """
    Parse rate up characters and return abbreviated names when necessary
    """
    replace_dict = {'Another Style' : '(AS)', 'Extra Style' : '(ES)'}
    for s in replace_dict.keys():
        if text.find(s) != -1:
            text = text[:text.index(s)-1] + replace_dict[s]
    return text


def insert_into_encounter_banners(new_banner):
    """
    Insert new banner info to encounter_banners list
    """
    filename = os.path.join(os.getcwd(), os.pardir, 'encounter_banners.json')
    with open(filename, 'r', encoding='utf-8') as encounters:
        encounter_banners_dict = json.load(encounters)
    
    encounter_banners_dict['limited'].insert(0, new_banner)

    with open(filename, 'w', encoding='utf-8') as encountersf:
        json.dump(encounter_banners_dict, encountersf, indent=4)


def scrape_html(url):
    """
    Scrape banner html for pull rates, banner name, rate up characters, 
    and end datetime
    """
    my_request = requests.get(url)
    html = my_request.text
    soup = BeautifulSoup(html, 'html5lib')

    banner_name = ' '.join([parse_title(text) for text in soup.find('h2').stripped_strings])

    section_divs = soup.find_all('div', class_='section')

    rate_up = []
    mid_dot_pattern = re.compile(u'\u30FB')
    for mid_dots in section_divs[1].find_all(string=mid_dot_pattern):
        rm_dot = re.sub(mid_dot_pattern, '', mid_dots.text).strip()
        rate_up.append(parse_characters(rm_dot))

    #Banner End Datetime (format codes: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes)
    avail_until = [av_unt for av_unt in section_divs[0].find('p').stripped_strings if 'Available until' in av_unt]
    date_string = avail_until[0].replace('Available until ', '').replace(' (UTC)', '')
    end_time = datetime.strptime(date_string, '%H:%M %b %d, %Y')

    new_banner = {
        'name' : banner_name.replace('Fateful Encounter', 'Fateful Encounter:'),
        'banner_file' : banner_name + '.json',
        'banner_image' : banner_name + '.png',
        'banner_enddatetime' : end_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'official_link' : url,
        'banner_short_name' : banner_name.lower().replace(' ','-')
    }

    #if Sidekicks column exists in rates table, increment starting index for pull rates
    start_rates_idx = 1
    new_soup = BeautifulSoup('<div></div>', 'html5lib')
    for tag in soup.find_all('th', class_='fifthtd'):
        new_soup.append(tag)
    if new_soup.css.select('th:nth-of-type(2)') and new_soup.css.select('th:nth-of-type(2)')[0].text == 'Sidekick':
        start_rates_idx += 1

    #Pull Rates
    base_character = ''
    start_range_lone, start_range_tenth = 0.0, 0.0
    number_line_lone, number_line_tenth = [], []
    for table in soup.find_all('table', limit=1):
        for tr in table.find_all('tr'):
            style_character = get_style_name(tr, base_character)
            for idx, td in enumerate(tr.find_all('td')):
                if td.find('span'):
                    td.span.unwrap()
                    td.string = ''.join(td.strings)
                if idx == 0: #character name
                    character = td.string.strip() if not style_character else style_character
                    base_character = character if not character[-1] == ')' else base_character
                if idx == start_rates_idx and td.string: #3 star rates
                    number_line_lone.append({
                        'name' : character,
                        'rarity' : 3,
                        'start_range' : start_range_lone,
                        'end_range' : start_range_lone + percent_to_float(td.string)
                    })
                    start_range_lone += percent_to_float(td.string)
                if idx == (start_rates_idx + 1) and td.string: #4 star rates
                    lone, tenth = split_lone_and_tenth(td.string)
                    number_line_lone.append({
                        'name' : character,
                        'rarity' : 4,
                        'start_range' : start_range_lone,
                        'end_range' : start_range_lone + lone
                    })
                    start_range_lone += lone
                    if tenth:
                        number_line_tenth.append({
                            'name' : character,
                            'rarity' : 4,
                            'start_range' : start_range_tenth,
                            'end_range' : start_range_tenth + tenth
                        })
                        start_range_tenth += tenth
                if idx == (start_rates_idx + 2) and td.string: #5 star rates
                    lone, tenth = split_lone_and_tenth(td.string)
                    number_line_lone.append({
                        'name' : character,
                        'rarity' : 5,
                        'start_range' : start_range_lone,
                        'end_range' : start_range_lone + lone
                    })
                    start_range_lone += lone
                    if tenth:
                        number_line_tenth.append({
                            'name' : character,
                            'rarity' : 5,
                            'start_range' : start_range_tenth,
                            'end_range' : start_range_tenth + tenth
                        })
                        start_range_tenth += tenth

    return (new_banner, {'lone' : number_line_lone, 'tenth' : number_line_tenth}, rate_up)


def process_images(new_banner, img_path, img_prefix, base_path):
    """
    Convert file types, rename, move, and shrink images for encounter 
    """
    banner_img_folder = os.path.join(base_path, 'images', 'banners') #get dir for copying images

    if img_path:
        os.chdir(img_path)

    shorter_name = new_banner['banner_short_name'].replace('-','')
    shorter_banner_name = new_banner['banner_short_name'].replace('-',' ').title().replace(' ','')
    for img in glob.glob(img_prefix + '*'):
        subprocess.run(['magick','mogrify','-format','png',img]) #convert fake pngs to actual pngs
        
        if img[:-4] == img_prefix:
            if not new_banner['banner_short_name'] == 'fateful-seven-days':
                new_img_name = img_prefix + '-' + shorter_banner_name + '.png'
            else:
                new_img_name = img_prefix + '-7DE' + datetime.now().strftime('%B%Y') + '.png'
            os.rename(img, new_img_name) #rename to standard convention
            copy_string = f'copy {new_img_name} {banner_img_folder}'
            os.popen(copy_string) #move banner art original to images/banners/ folder
            subprocess.run(['magick','mogrify','-crop','1060x720+60+0',new_img_name]) #crop banner art
            tinify.key = apikeys.tinify_api_key
            dest = os.path.join(banner_img_folder, new_banner['banner_image'])
            source = tinify.from_file(new_img_name) #shrink and move to final dest
            source.to_file(dest)
        else:
            rename_img = img.replace(img_prefix, img_prefix + '.' + shorter_name)
            dest = os.path.join(banner_img_folder, rename_img)
            copy_string = f'copy {img} {dest}'
            os.popen(copy_string)

    combo_img = None
    if not new_banner['banner_short_name'] == 'fateful-seven-days':
        normal_img = f'{img_prefix}.normal.png'
        highlighted_img = f'{img_prefix}.highlighted.png'
        combo_img = f'{img_prefix}.{shorter_name}.combo.png'
        dest = os.path.join(banner_img_folder, combo_img)
        subprocess.run(['magick','convert',normal_img,highlighted_img,'-append',dest]) #create sprite for banner selector

    return combo_img


def update_version_in_html(base_path):
    """
    Find old version string and replace with new random string on index.html
    """
    filename = os.path.join(base_path, 'index.html')
    with open(filename, 'r', encoding='utf-8') as html:
        html_string = html.read()
        soup = BeautifulSoup(html_string, 'html5lib')

    #get previous version
    old_version_alphanum = None
    for link in soup.find_all('link'):
        if link['rel'] == ['stylesheet'] and 'encounter-sim.css' in link['href']:
            old_version_alphanum = link['href'][-10:]

    #replace with new version and export
    new_html_string = html_string.replace(old_version_alphanum, gen_random_version())
    with open(filename, 'w', encoding='utf-8') as file_out:
        file_out.write(new_html_string)


def build_css_string(combo_img, short_name):
    """
    Create CSS string for new banner select image
    """
    return f'a.banner-select.{short_name} {{\n  background: url("../images/banners/{combo_img}") 0 0 no-repeat;\n}}\n'


def add_new_banner_css(base_path, combo_img, new_banner):
    """
    Update encounter-sim.css with new banner's CSS
    """
    filename = os.path.join(base_path, 'css', 'encounter-sim.css')
    with open(filename, 'r', encoding='utf-8') as css:
        css_string = css.read()

    css_to_add = build_css_string(combo_img, new_banner['banner_short_name'])

    index = css_string.find('a.banner-select:hover')

    with open(filename, 'w', encoding='utf-8') as out_file:
        out_file.write(css_string[:index] + css_to_add + css_string[index:])


def main():
    parser = argparse.ArgumentParser(description='Add new banner to encounter_banners.json and scrape rates into banners/ folder')
    parser.add_argument('url', type=str, help='URL to banner rates, like https://api-us.another-eden.games/path/to/rates')
    parser.add_argument('--short_name', type=str, help='Short name for banner, used for CSS and images')
    parser.add_argument('--img_path', type=str, help='Path to banner images to process')
    parser.add_argument('--img_prefix', type=int, help='Prefix number of images to process, e.g. 91015, 91032, etc.')
    args = parser.parse_args()

    new_banner, range_rows, rate_up = scrape_html(args.url)

    if args.short_name:
        new_banner['banner_short_name'] = args.short_name

    print('New Banner:', new_banner)
    print('Rate Up:', rate_up)

    merge_and_dump_rates(new_banner, rate_up, range_rows)
    insert_into_encounter_banners(new_banner)
    print('Added to encounter_banners.json!')

    base_path = os.path.join(os.getcwd(), os.pardir)
    combo_img = None

    if not args.img_path or not args.img_prefix:
        print('Missing image path and/or prefix, no images processed.')
    else:
        combo_img = process_images(new_banner, args.img_path, str(args.img_prefix), base_path)
        print('Images processed and moved to images/banners/')

    update_version_in_html(base_path)
    
    if combo_img:
        add_new_banner_css(base_path, combo_img, new_banner)
        print('HTML and CSS updated for new banner')
    
        



if __name__ == '__main__':
    main()