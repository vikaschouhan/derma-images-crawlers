import requests
from   bs4 import BeautifulSoup
from   pprint import pprint
import os
import sys
import argparse
import pickle
import shutil

def download_image(url, image_path):
    try:
        req_t = requests.get(url, stream=True)
        if req_t.status_code == 200:
            with open(image_path, 'wb') as fout:
                req_t.raw.decode_content = True
                shutil.copyfileobj(req_t.raw, fout)
            # endwith
        # endif
    except Exception as e:
        print(e)
        print("Failed to save " + image_path)
        print(url + "\n")
    else:
        print("Successfully saved " + image_path)
    # endtry
# enddef

def get_image_links(im_url):
    req_t = requests.get(im_url)
    soup  = BeautifulSoup(req_t.text, features='lxml')
    links = ['https:' + x.get('src') for x in soup.find('div', {'class' :'field-items'}).find_all('img')]

    return links
# enddef

def populate_class_links_map():
    req_t = requests.get('https://medicine.uiowa.edu/dermatology/education/clinical-skin-disease-images')
    soup  = BeautifulSoup(req_t.text, features='lxml')
    ul_list = soup.find('div', {'class': 'content'}).find_all('ul')

    class_url_map = {}
    for ul_t in ul_list:
        li_list = ul_t.find_all('li')
        for li_t in li_list:
            class_url_map[li_t.text] = 'https:' + li_t.find('a').get('href')
        # endfor
    # endfor

    # Populate image links
    class_links_map = {}
    for key_t in class_url_map:
        print('>> Analysing {}'.format(key_t), end='\r')
        class_links_map[key_t] = get_image_links(class_url_map[key_t])
    # endfor

    return class_links_map
# enddef

def main(out_dir):
    os.makedirs(out_dir, exist_ok=True)

    # Get class links map
    class_link_map_file = '{}/class_links_map.pkl'.format(out_dir)
    if os.path.exists(class_link_map_file):
        print('>> {} already exists. Loading from here.'.format(class_link_map_file))
        class_links_map = pickle.load(open(class_link_map_file, 'rb'))
    else:
        print('>> {} doesnot exist. Crawling !!'.format(class_link_map_file))
        class_links_map = populate_class_links_map()
        print('>> Saving class_links map to {}'.format(class_link_map_file))
        pickle.dump(class_links_map, open(class_link_map_file, 'wb'))
    # endif

    # Download links
    for key_t in class_links_map:
        subdir_t = '{}/{}/{}'.format(out_dir, 'images', key_t)
        os.makedirs(subdir_t, exist_ok=True)

        for lnk_t in class_links_map[key_t]:
            im_path = '{}/{}'.format(subdir_t, os.path.basename(lnk_t.rstrip('/')))
            im_url  = lnk_t
            print('>> Download {}'.format(im_url))
            download_image(im_url, im_path)
        # endfor
    # endfor
# enddef

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--out_dir',   help='Output directory.', type=str, default=None)
    args = parser.parse_args()

    if args.__dict__['out_dir'] is None:
        print('Invalid inputs. Please check --help.')
        sys.exit(-1)
    # endif
  
    main(args.__dict__['out_dir'])
# endif
