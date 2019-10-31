import requests
from   bs4 import BeautifulSoup
from   pprint import pprint
import os
import sys
import argparse
import pickle
import shutil

base_url = 'http://www.meddean.luc.edu/lumen/MedEd/medicine/dermatology/melton'

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

def populate_stage1_links():
    req_t = requests.get('{}/content.htm'.format(base_url))
    soup = BeautifulSoup(req_t.text, features='lxml')
    stage1_links = {x.find('a').text : '{}/{}'.format(base_url, x.find('a').get('href')) for x in soup.find_all('li')}
    return stage1_links
# enddef

def populate_stage2_links(stage1_links):
    stage2_links = {}
    for key_t in stage1_links:
        print('>> Query {}'.format(key_t), end='\r')
        req_t = requests.get(stage1_links[key_t])
        soup  = BeautifulSoup(req_t.text, features='lxml')
        # Type 2 page where there are futher links to images
        if soup.find('ul'):
            uls = soup.find('ul')
            links_t = {x.find('a').text : '{}/{}'.format(base_url, x.find('a').get('href')) for x in uls.find_all('li')}
            # Resolve the html links further to get each image link
            newlinks = {}
            for key_t in links_t:
                req_t = requests.get(links_t[key_t])
                soup  = BeautifulSoup(req_t.text, features='lxml')
                try:
                    newlinks[key_t] = base_url + '/' + soup.find('center').find('img').get('src').strip()
                except AttributeError:
                    print('ERROR::: Couldnot fetch image link for {}'.format(key_t))
                # endtry
            # endfor
            stage2_links[key_t] = newlinks
        # Type 1 page where there is single link to single image
        else:
            link_t = base_url + '/' + soup.find('center').find('img').get('src').strip()
            stage2_links[key_t] = link_t
        # endif
    # endfor

    return stage2_links
# enddef

def main(out_dir):
    # Start downloading
    os.makedirs(out_dir, exist_ok=True)

    stage2_file  = '{}/stage2_file.pkl'.format(out_dir)
    if os.path.exists(stage2_file):
        print('>> stage2 file {} exists. Loading from here.'.format(stage2_file))
        stage2_links = pickle.load(open(stage2_file, 'rb'))
    else:
        print('>> stage2 file {} doesnot exist. Crawling.'.format(stage2_file))
        stage2_links = populate_stage2_links(populate_stage1_links())
        print('>> Storing stage2 links to {}'.format(stage2_file))
        pickle.dump(stage2_links, open(stage2_file, 'wb'))
    # endif
   
    print('>> Downloading files !!')
    im_dir = '{}/images'.format(out_dir)
    os.makedirs(im_dir, exist_ok=True)
    for key_t in stage2_links:
        if isinstance(stage2_links[key_t], dict):
            for subkey_t in stage2_links[key_t]:
                im_url  = stage2_links[key_t][subkey_t]
                name1   = key_t.replace(' ', '_').replace('"', '')
                name2   = subkey_t.replace(' ', '_').replace('"', '')
                im_path = '{}/{}__{}__{}'.format(im_dir, name1, name2, os.path.basename(im_url.rstrip('/')))
                print('>> Downloading {}'.format(im_url))
                download_image(im_url, im_path)
            # endfor
        # endif
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

