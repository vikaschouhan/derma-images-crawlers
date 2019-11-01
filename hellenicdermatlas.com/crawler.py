import requests
import json
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

root_url = 'http://www.hellenicdermatlas.com'

def qp(x):
    return url_normalize(x)
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

def get_max_page_count(first_page_link):
    req_t      = requests.get(first_page_link)
    if req_t.status_code != 200:
        return -1
    # endif

    soup_t     = BeautifulSoup(req_t.text, features='lxml')
    try:
        page_info  = soup_t.find('div', {'id' : 'content'}).find('div', {'id' : 'paging'}).find_all('a')
    except:
        return 1
    # endtry

    page_list  = []
    for page_t in page_info:
        try:
            page_list.append(int(page_t.text))
        except:
            continue
        # endtry
    # endfor

    return max(page_list)
# enddef

def get_page_link_with_page_num(first_page_link, page_num):
    tok_list = first_page_link.split('/')                                                                                                                                               
    tok_list[-2] = str(page_num)
    return '/'.join(tok_list)
# enddef

def get_all_page_links(first_page_link):
    max_page_cnt = get_max_page_count(first_page_link)
    if max_page_cnt == -1:
        return -1
    # endif
    return [get_page_link_with_page_num(first_page_link, x) for x in range(1, max_page_cnt+1)]
# enddef

def get_image_links(page_link):
    req_t      = requests.get(page_link)
    soup_t     = BeautifulSoup(req_t.text, features='lxml')
    try:
        image_links = ['{}/{}'.format(root_url, x.find('a').get('href')) for x in soup_t.find('div', {'id' : 'content'}).find('table').find_all('table')]
        return [get_image_data(x) for x in image_links]
    except:
        return []
    # endtry
# enddef

def get_image_data(im_link):
    req_t      = requests.get(im_link)
    soup_t     = BeautifulSoup(req_t.text, features='lxml')
    content_t  = soup_t.find('div', {'id' : 'content'})
    img_link_t = content_t.find('img').get('src')
    info_tr_l  = content_t.find('table').find_all('tr')[2:] # Remove first entry as it's not relevant

    info_dict = {}
    for info_r_t in info_tr_l:
        td_l = info_r_t.find_all('td')
        info_dict[td_l[0].text.strip()] = td_l[1].text.strip()
    # endfor

    info_dict['link'] = '{}/{}'.format(root_url, img_link_t)
    return info_dict
# enddef

def get_stage1_links():
    base_url = 'http://www.hellenicdermatlas.com/en/search/browse/'

    req_t       = requests.get(base_url)
    soup_t      = BeautifulSoup(req_t.text, features='lxml')
    clist_t     = [x.find('a') for x in soup_t.find('div', {'id' : 'content'}).find('ol').find_all('li')]
    class_map   = {x.text.strip() : '{}/{}'.format(root_url, x.get('href')) for x in clist_t}
    return class_map
# enddef

def main(out_dir):
    os.makedirs(out_dir, exist_ok=True)

    # stage1 file
    stage1_file = '{}/stage1_file.pkl'.format(out_dir)
    if os.path.exists(stage1_file):
        print('>> stage1 file {} exists. loading from here.'.format(stage1_file))
        stage1_map = pickle.load(open(stage1_file, 'rb'))
    else:
        print('>> stage1 file not found. Crawling !!')
        stage1_map = get_stage1_links()
        print('>> Saving stage1 map in {}'.format(stage1_file))
        pickle.dump(stage1_map, open(stage1_file, 'wb'))
    # endif

    # Stage2 file
    stage2_file = '{}/stage2_file.pkl'.format(out_dir)
    if os.path.exists(stage2_file):
        print('>> found stage2 file {}. Loading from here.'.format(stage2_file))
        page_links_map = pickle.load(open(stage2_file, 'rb'))
    else:
        print ('>> stage2 file not found. Crawling !!')
        # get all page links
        page_links_map = {}
        for class_t in stage1_map:
            print('>> Analysing {}'.format(class_t), end='\r')
            page_links = get_all_page_links(stage1_map[class_t])
            if page_links == -1:
                continue
            # endif
            page_links_map[class_t] = page_links
        # endfor

        # Save stage2 file
        print('>> Saving stage2 info in {}'.format(stage2_file))
        pickle.dump(page_links_map, open(stage2_file, 'wb'))
    # endif

    # Stage3
    stage3_file = '{}/stage3_file.pkl'.format(out_dir)
    if os.path.exists(stage3_file):
        print('>> stage3 file {} found. Loading from here'.format(stage3_file))
        img_links_map = pickle.load(open(stage3_file, 'rb'))
    else:
        print('>> stage3 file not found. Crawling !!')
        img_links_map = {}
        for class_t in page_links_map:
            print('>> Analysing {}'.format(class_t))
            
            # Stage3 tmp files
            stage3_tmp_dir = '{}/stage3_tmp_dir'.format(out_dir)
            os.makedirs(stage3_tmp_dir, exist_ok=True)
            stage3_tmp_file = '{}/{}.pkl'.format(stage3_tmp_dir, class_t)
            if os.path.exists(stage3_tmp_file):
                print('>> Reading img links for {} from {}'.format(class_t, stage3_tmp_file))
                img_links_map[class_t] = pickle.load(open(stage3_tmp_file, 'rb'))
            else:
                img_links_list = []
                for page_link_t in page_links_map[class_t]:
                    print('>> Analysing {}'.format(page_link_t))
                    img_links_list += get_image_links(page_link_t)
                # endfor
                img_links_map[class_t] = img_links_list
                print('>> Saving img links info for {} in {}'.format(class_t, stage3_tmp_file))
                pickle.dump(img_links_map[class_t], open(stage3_tmp_file, 'wb'))
            # endif
        # endfor

        # Save stage3 info
        print('>> Saving stage3 file {}'.format(stage3_file))
        pickle.dump(img_links_map, open(stage3_file, 'wb'))
    # endif

    # We have all the data now. Start downloading !!
    im_dir = '{}/images'.format(out_dir)
    os.makedirs(im_dir, exist_ok=True)
    for class_t in img_links_map:
        class_dir_t = '{}/{}'.format(im_dir, class_t)
        os.makedirs(class_dir_t, exist_ok=True)

        for info_t in img_links_map[class_t]:
            img_url  = info_t['link']
            img_path = '{}/{}'.format(class_dir_t, os.path.basename(img_url))
            inf_path = '{}/{}.json'.format(class_dir_t, os.path.basename(img_url))

            # Check if image file exists. if not, just skip
            if os.path.exists(img_path):
                print('>> {} exists. Skipping {}'.format(img_path, img_url))
                continue
            # endif

            # Download image
            print('>> Downloading {}'.format(img_url))
            download_image(img_url, img_path)

            # Save json
            print('>> Saving {}'.format(inf_path))
            json.dump(info_t, open(inf_path, 'w'), ensure_ascii=False)
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
