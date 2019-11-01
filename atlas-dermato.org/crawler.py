import requests
import re
from   bs4 import BeautifulSoup
from   pprint import pprint
import os
import sys
import argparse
import pickle
import shutil
import string
from   url_normalize import url_normalize

def qp(x):
    return url_normalize(x)
# enddef

def find_class_links_map(soup, base_url):
    ele_list = []
    for x in soup.find_all('a'):
        y = re.search('../(\w+).htm', x.get('href'))
        if y and y.groups()[0] not in ['contact', 'index']:
            ele_list.append(x)
        # endif
    # endfor

    links_dict = {}
    for ele_t in ele_list:
        links_dict[ele_t.text.strip().replace('\n ', '')] = qp(base_url + '/' + ele_t.get('href'))
    # endfor

    return links_dict
# enddef

def populate_class_links():
    base_url       = 'http://www.atlas-dermato.org/atlas/abc'
    alpha_exl_list = ['j', 'w', 'y']
    alpha_list     = list(set(x for x in string.ascii_lowercase) - set(alpha_exl_list))

    links_dict = {}
    for char_t in alpha_list:
        print('Analysing classes starting with "{}"'.format(char_t), end='\r')
        link_t = '{}/{}.html'.format(base_url, char_t)
        req_t  = requests.get(link_t)
        soup_t = BeautifulSoup(req_t.text, features='lxml')
        links_dict =  {**links_dict, **find_class_links_map(soup_t, base_url)}
    # endfor

    return links_dict
# enddef

def class_link_to_image_links(class_link, base_url='http://www.atlas-dermato.org/atlas/'):
    print('>> Query {}'.format(class_link), end='\r')
    req_t  = requests.get(class_link)
    soup_t = BeautifulSoup(req_t.text, features='lxml')
    elel   = [x for x in soup_t.find('table', {'id' : 'AutoNumber4'}).find_all('a') if x.find('img')]

    links_list = [qp('{}/{}'.format(base_url, x.get('href'))) for x in elel]
    return links_list
# enddef

def populate_image_links_map(out_dir):
    stage0_file = '{}/stage0_file.pkl'.format(out_dir)

    if os.path.exists(stage0_file):
        print('>> stage0 file {} exists. Loading from here.'.format(stage0_file))
        links_map = pickle.load(open(stage0_file, 'rb'))
    else:
        print('>> stage0 file {} doesnot exit. Crawling !!'.format(stage0_file))
        links_map = populate_class_links()
        print('>> Saving stage0 info to {}'.format(stage0_file))
        pickle.dump(links_map, open(stage0_file, 'wb'))
    # endif

    print('>> Crawling for stage1 info.')
    links_map = {k:class_link_to_image_links(v) for k,v in links_map.items()}
    return links_map
# enddef

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

def download_images(links_map, out_dir):
    im_dir = '{}/images'.format(out_dir)
    os.makedirs(im_dir, exist_ok=True)

    for class_t in links_map:
        class_dir = '{}/{}'.format(im_dir, class_t)
        os.makedirs(class_dir, exist_ok=True)

        for link_t in links_map[class_t]:
            im_path = '{}/{}'.format(class_dir, os.path.basename(link_t))
            im_url  = link_t
            # Download image
            if os.path.exists(im_path):
                print('>> Not downloading from {} as image already exists !!'.format(im_url))
            else:
                print('>> Downloading {}'.format(im_url))
                download_image(im_url, im_path)
            # endif
        # endfor
    # endfor
# enddef
            
def main(out_dir):
    # mkdir
    os.makedirs(out_dir, exist_ok=True)

    # get class => links mapping
    stage1_file = '{}/stage1.pkl'.format(out_dir)
    if os.path.exists(stage1_file):
        print('>> stage1 file {} exists. Loading from here'.format(stage1_file))
        links_map = pickle.load(open(stage1_file, 'rb'))
    else:
        print('>> stage1 file {} doesnot exist. Crawling !!'.format(stage1_file))
        links_map = populate_image_links_map(out_dir)
        print('>> Saving stage1 file {}'.format(stage1_file))
        pickle.dump(links_map, open(stage1_file, 'wb'))
    # endif

    # Download images
    download_images(links_map, out_dir)
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
