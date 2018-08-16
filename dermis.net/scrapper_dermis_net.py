import requests
from bs4 import BeautifulSoup
import os, sys
#from PIL import image

base_url = 'http://www.dermis.net/dermisroot'
root_url = 'http://www.dermis.net'

def get_all_class_path(load_timeout=3):
    coll_url = '{}/{}'.format(base_url, 'en/list/all/search.htm')
    req_t    = requests.get(coll_url)
    html     = req_t.text
    soup     = BeautifulSoup(html, 'html5lib')
    grp_grp  = soup.find('div', {'id' : 'ctl00_Main_pnlSearchControl' })
    class_list = grp_grp.findAll('a', {'class' : 'list'})
    class_dict = {}
    for item_t in class_list:
        class_dict[item_t.text] = '{}/{}'.format(base_url, item_t.attrs['href'])
    return class_dict
# enddef

def get_all_imgs_path(web_path):
    req      = requests.get(web_path)
    html     = req.text
    soup     = BeautifulSoup(html, "html5lib")
    grp_grp  = soup.find('div', {'id' : 'ctl00_Main_pnlImages' })
    img_list = grp_grp.findAll('img')
    img_lnew = []
    for x in img_list:
        img_part_path  = x.attrs['src']
        # Get full size image not the resampled one
        img_pp     = img_part_path.split('/')
        img_name   = img_pp[-1]
        img_pp[-2] = '550px' # Replace default low resolution with high resolution
        img_pn     = '/'.join(img_pp)
        img_lnew.append('{}/{}'.format(root_url, img_pn))
    # endfor
    return img_lnew
# enddef

def img_download(url, dwn_path):
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with open(dwn_path, "wb") as f:
            for chunk in r:
                f.write(chunk)
            # endfor
        # endwith
    # endif
    #im = Image.open(dwn_path+".png")
    #im.convert('RGB').save(dwn_path + ".jpg","JPEG") #this converts png image as jpeg
    #os.remove(dwn_path + '.png')
# enddef

def scrape_all(root_dir='./dermis_net_img_list'):
    # Create root directory if it doesnot exist
    if not os.path.isdir(root_dir):
        os.mkdir(root_dir)
    # endif
    class_dict = get_all_class_path()
    for k,v in class_dict.items():
        print('Retrieving all images for {}'.format(k))
        img_list = get_all_imgs_path(v)
        # Create this dir
        leaf_dir = '{}/{}'.format(root_dir, k.replace(' ', '_'))
        if not os.path.isdir(leaf_dir):
            os.makedirs(leaf_dir)
        # endif
        # Download all images
        for img_t in img_list:
            print('Downloading {}'.format(img_t))
            dwn_path = '{}/{}'.format(leaf_dir, os.path.basename(img_t))
            img_download(img_t, dwn_path)
        # endfor
    # endfor
# enddef

scrape_all()
