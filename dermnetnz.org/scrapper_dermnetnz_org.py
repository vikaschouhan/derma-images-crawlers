from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import requests
from bs4 import BeautifulSoup
import os, sys
#from PIL import image

base_url = 'https://www.dermnetnz.org'

def get_all_class_path(load_timeout=3):
    coll_url = '{}/{}'.format(base_url, 'image-library')
    options  = webdriver.ChromeOptions()
    options.add_argument('headless')
    driver   = webdriver.Chrome(chrome_options=options) #using selenium to obtain RENDERED html & easily navigate it

    print('Opening {}'.format(coll_url))
    driver.get(coll_url)
    html     = driver.execute_script("return document.body.innerHTML")
    try:
        WebDriverWait(driver, load_timeout).until(EC.presence_of_element_located((By.CLASS_NAME, 'imageList__group__item')))
    except TimeoutException:
        print("Timed out !!")
        return None
    # endtry

    print('Retrieving image classes.')
    html     = driver.execute_script("return document.body.innerHTML")
    soup     = BeautifulSoup(html, 'html5lib')
    class_list = soup.findAll("a", {"class" : "imageList__group__item"})
    class_dict = {}
    for item_t in class_list:
        class_dict[item_t.find('h6').text] = '{}/{}'.format(base_url, item_t.attrs['href'])
    return class_dict
# enddef

def get_all_imgs_path(web_path):
    req      = requests.get(web_path)
    html     = req.text
    soup     = BeautifulSoup(html, "html5lib")
    img_list = soup.findAll("div", {"class" : "imageLinkBlock__item__image" })
    img_lnew = []
    for x in img_list:
        img_part_path  = x.find('img').attrs['src']
        # Get full size image not the resampled one
        img_p0, img_p1 = img_part_path.split('_resampled')
        img_name       = os.path.basename(img_p1)
        img_lnew.append('{}/{}/{}'.format(base_url, img_p0, img_name))
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

def scrape_all(root_dir='./dermnetz_org_img_list'):
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
