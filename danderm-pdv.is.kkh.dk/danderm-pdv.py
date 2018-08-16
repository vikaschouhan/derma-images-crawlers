import re
import pprint
import argparse
import sys
import json
import os
import requests

def gurl(page_info):
    base_url = 'http://www.danderm-pdv.is.kkh.dk/atlas/pics' #4/4-1.jpg
    url_t = '{}/{}/{}-{}.jpg'.format(base_url, page_info[0], page_info[0], page_info[1])
    return url_t
# enddef

def img_download(url, dwn_path):
    headers = { 'User-Agent' : 'Mozilla/5.0' }
    r = requests.get(url, stream=True, headers=headers)
    if r.status_code == 200:
        with open(dwn_path, "wb") as f:
            for chunk in r:
                f.write(chunk)
            # endfor
        # endwith
    # endif
# enddef

def download_images(index_dict, out_dir):
    # Create out_dir
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)
    # endif

    entries = index_dict['entries']
    for major_cat in entries:
        major_cat_name = major_cat
        sub_entries    = entries[major_cat]['categories']

        # Create major category directory
        major_dir = '{}/{}'.format(out_dir, major_cat_name)
        if not os.path.isdir(major_dir):
            os.mkdir(major_dir)
        # endif

        if len(sub_entries) == 0:
            page_info = entries[major_cat]['pages']
            if len(page_info) == 0:
                continue
            # endif

            # If there are no sub-entries, download all images directly in major dir
            for ind_t in range(page_info[1][0], page_info[1][1]):
                url_t = gurl([page_info[0], ind_t])
                print('-> Downloading {}    '.format(os.path.basename(url_t)), end='\r')
                pic_path = '{}/{}'.format(major_dir, os.path.basename(url_t))
                img_download(url_t, pic_path)
            # endfor
        else:
            # Sub categories are present. Iterate over all subcategories.
            for sub_entry_t in sub_entries:
                sub_entry_name = sub_entry_t
                page_info = sub_entries[sub_entry_t]

                # If page info is empty, ignore and continue
                if len(page_info) == 0:
                    continue
                # endif

                # Create sub directory
                sub_cat_dir = '{}/{}'.format(major_dir, sub_entry_name)
                if not os.path.isdir(sub_cat_dir):
                    os.mkdir(sub_cat_dir)
                # endif

                for ind_t in range(page_info[1][0], page_info[1][1]):
                    url_t = gurl([page_info[0], ind_t])
                    print('-> Downloading {}    '.format(os.path.basename(url_t)), end='\r')
                    pic_path = '{}/{}'.format(sub_cat_dir, os.path.basename(url_t))
                    img_download(url_t, pic_path)
                # endfor
            # endfor
        # endif
# enddef

if __name__ == '__main__':
    parser  = argparse.ArgumentParser()
    parser.add_argument('--json',          help='Database json file',        type=str, default=None)
    args    = parser.parse_args()

    if args.__dict__['json'] == None:
        print('--json is required. Exiting.')
        sys.exit(-1)
    # endif

    index_dict = json.load(open(args.__dict__['json'], 'r'))
    download_images(index_dict, './danderm-pdv')
# endif
