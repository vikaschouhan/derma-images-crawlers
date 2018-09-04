import requests
from   bs4 import BeautifulSoup
import re
import pprint
import os
import json

def img_download(url, dwn_path, headers):
    r = requests.get(url, stream=True, headers=headers)
    if r.status_code == 200:
        with open(dwn_path, "wb") as f:
            for chunk in r:
                f.write(chunk)
            # endfor
        # endwith
    # endif
# enddef

def download_images(out_dir):
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)
    # endif
    db_json = '{}/{}'.format(out_dir, 'atlasdermatologico.json')
    headers = { 'User-Agent': 'Mozilla/5.0' }

    # If db_json exists just skip the db creation stage
    if os.path.exists(db_json) and os.path.isfile(db_json):
        pass
    else:
        base_url     = 'http://www.atlasdermatologico.com.br'
        browse_url   = '{}/browse.jsf'.format(base_url)
        
        # Get base names
        req_this     = requests.get(browse_url, headers=headers)
        soup_this    = BeautifulSoup(req_this.text, 'lxml')
        row_ele      = soup_this.find('ul', {'class' : 'ui-datalist-data'})
        row_list     = row_ele.find_all('li')
        
        index_dict   = {}
        for row_t in row_list:
            item_name = row_t.find('span', {'itemprop' : 'name'}).text
            item_url  = row_t.find('a', {'class' : 'capitalized'}).attrs['href']
            index_dict[item_name] = { 'redirect_url' : item_url, 'img_urls' : [] }
        # endfor
        
        #print(index_dict)
        # Iterate over each class
        index_ctr = 1
        total_entries = len(index_dict)
        for item_t in index_dict:
            print('Inspecting [{:<4}/{:<4}]'.format(index_ctr, total_entries), end='\r')
        
            item_hurl = index_dict[item_t]['redirect_url']
            item_url  = '{}/{}'.format(base_url, item_hurl)
            item_name = item_t
        
            req_this  = requests.get(item_url, headers=headers)
            soup_this = BeautifulSoup(req_this.text, 'lxml')
            gallery   = soup_this.find('div', {'class' : 'article-content gallery'})
            urls      = gallery.find_all('a', {'class' : 'thumbWrapper'})
            url_list  = [ x.attrs['href'] for x in urls ]
        
            # Extract image ids
            imgid_list = []
            for url_t in url_list:
                match = re.search('imageId=(\d+)', url_t)
                if match:
                    imgid_list.append('{}/img?imageId={}'.format(base_url, match.groups()[0]))
                # endif
            # endfor
        
            # Add
            index_dict[item_t]['img_urls'] = imgid_list
            index_ctr = index_ctr + 1
            #if index_ctr == 5:
            #    break
        # endfor

        # Save index_dict as json
        print('Saving url information in {}'.format(db_json))
        json.dump(index_dict, open(db_json, 'w'))
    # endif

    index_dict = json.load(open(db_json, 'r'))
    # Download images
    index_ctr = 1
    total_entries = len(index_dict)
    for item_t in index_dict:
        pic_ctr = 0
        print('Downloading [{:4}/{:4}  -> {:4}]'.format(index_ctr, total_entries, len(index_dict[item_t]['img_urls'])), end='\r')
        for url_t in index_dict[item_t]['img_urls']:
            pic_dir = '{}/{}'.format(out_dir, item_t.replace(' ', '_'))
            if not os.path.isdir(pic_dir):
                os.mkdir(pic_dir)
            # endif
            pic_path = '{}/{}.jpg'.format(pic_dir, pic_ctr)
            # Check if pic path exists
            if not os.path.isfile(pic_path):
                img_download(url_t, pic_path, headers)
            # endif
            pic_ctr  = pic_ctr + 1
        # endfor
        index_ctr = index_ctr + 1
    # endfor
# enddef

download_images('./atlas_dermatologico')
