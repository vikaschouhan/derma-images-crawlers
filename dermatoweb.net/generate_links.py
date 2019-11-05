from   selenium import webdriver
from   selenium.webdriver.common.keys import Keys
from   selenium.webdriver.support.ui import WebDriverWait
from   selenium.webdriver.support import expected_conditions as EC
from   selenium.webdriver.common.by import By
from   selenium.common.exceptions import TimeoutException
from   selenium.webdriver.common.action_chains import ActionChains
from   selenium.common.exceptions import *
import string
import requests
from   bs4 import BeautifulSoup
import os, sys
import time
import argparse
import pickle

# This function is messed up (due to the messed up website it crawls :(.)
def _populate_links(driver, alpha_char):
    front_url = 'http://dermatoweb2.udl.es/atlas.php?lletra={}'.format(alpha_char)
    print('>> Querying {}'.format(front_url))
    info_dict = {}

    def load_front_page():
        driver.get(front_url)
        sel1 = driver.find_element_by_xpath('/html/body/div/center/table/tbody/tr[5]/td/div/table/tbody/tr/td/div[1]/table/tbody/tr/td[2]')
        # Hover to sel1
        ActionChains(driver).move_to_element(sel1).perform()
        time.sleep(1)
        # Heuristics (This site is f***ing crazy !! One of the craziest I have seen in recent years. Who the f**k designed it ??)
        div_l = driver.find_element_by_id('menuFg1').find_elements_by_tag_name('div')
        if ''.join([x.text for x in div_l]) == '':
            try:
                div_l = driver.find_element_by_id('menuFg3').find_elements_by_tag_name('div')
            except NoSuchElementException:
                print('WARNING:: menuFg3 failed !!')
            # endtry
        # endif
        if ''.join([x.text for x in div_l]) == '':
            div_l = driver.find_element_by_id('menuFg0').find_elements_by_tag_name('div')
        # endif
        return div_l
    # enddef

    div_l = load_front_page()
    num_links = len(div_l)
    print('INFO::: {} links found under this page.'.format(num_links))
    for i_link in range(1, num_links):
        print('INFO::: i_link = {}'.format(i_link))
        div_l = load_front_page()
        text  = div_l[i_link].text
        try:
            div_l[i_link].click()
            time.sleep(2)
            if driver.current_url != front_url:
                info_dict[text] = driver.current_url
                print('>> {} -> {}'.format(text, driver.current_url))
            else:
                # Hover over the element to get subelements
                ActionChains(driver).move_to_element(div_l[i_link]).perform()
                # Get elements
                # Heuristics
                div2_l = driver.find_element_by_id('menuFg0').find_elements_by_tag_name('div')
                if ''.join([x.text for x in div2_l]) == '':
                    try:
                        div2_l = driver.find_element_by_id('menuFg1').find_elements_by_tag_name('div')
                    except NoSuchElementException:
                        print('WARNING::: menuFg1 failed !!')
                    # endtry
                 # endif
                if ''.join([x.text for x in div2_l]) == '':
                    try:
                         div2_l = driver.find_element_by_id('menuFg2').find_elements_by_tag_name('div')
                    except NoSuchElementException:
                        print('WARNING::: menuFg2 failed !!')
                    # endtry
                 # endif
                num_links2 = len(div2_l)
                print('INFO::: {} links found under {} heading'.format(num_links2, text))

                for ii_link in range(1, num_links2):
                    print('INFO::: ii_link = {}'.format(ii_link))
                    div_l = load_front_page()
                    # Hover over the element to get subelements
                    ActionChains(driver).move_to_element(div_l[i_link]).perform()
                    # Heuristoics
                    div2_l = driver.find_element_by_id('menuFg0').find_elements_by_tag_name('div')
                    if ''.join([x.text for x in div2_l]) == '':
                        try:
                            div2_l = driver.find_element_by_id('menuFg1').find_elements_by_tag_name('div')
                        except NoSuchElementException:
                            print('WARNING::: menuFg1 failed !!')
                        # endtry
                    # endif
                    if ''.join([x.text for x in div2_l]) == '':
                        try:
                            div2_l = driver.find_element_by_id('menuFg2').find_elements_by_tag_name('div')
                        except NoSuchElementException:
                            print('WARNING::: menuFg2 failed !!')
                        # endtry
                    # endif

                    try:
                        text2  = div2_l[ii_link].text
                    except IndexError:
                        break
                    # endtry

                    try:
                        div2_l[ii_link].click()
                        time.sleep(1)
                        info_dict[text2] = driver.current_url
                        print('>> {} -> {}'.format(text2, driver.current_url))
                    except ElementNotVisibleException:
                        print('WARNING::: Couldnot click on link "{}"'.format(text2))
                # endfor
            # endif
        except ElementNotVisibleException:
            print('WARNING::: Couldnot click on link "{}"'.format(text))
    # endfor
    return info_dict
# enddef

def populate_links(out_dir):
    lowercase_chars = string.ascii_lowercase
    out_tmp_dir = '{}/tmp_files'.format(out_dir)
    os.makedirs(out_tmp_dir, exist_ok=True)
    info_dict = {}

    driver = webdriver.Chrome()
    for char_t in lowercase_chars:
        out_tmp_file = '{}/{}.pkl'.format(out_tmp_dir, char_t)

        if os.path.exists(out_tmp_file):
            print('>> {} already exists !! Skipping for {}'.format(out_tmp_file, char_t))
            info_dict[char_t] = pickle.load(open(out_tmp_file, 'rb'))
        else:
            print('>> {} doesnot exist !! Crawling !!'.format(out_tmp_file))
            info_dict[char_t] = _populate_links(driver, char_t)
            print('>> Saving {}'.format(out_tmp_file))
            pickle.dump(info_dict[char_t], open(out_tmp_file, 'wb'))
    # endfor

    # stage1 file
    stage1_file = '{}/{}'.format(out_dir, 'stage1_file.pkl')
    print('Writing stage1 file {}'.format(stag1_file))
    pickle.dump(info_dict, open(stage1_file, 'wb'))
# enddef

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out_dir',   help='Output directory.', type=str, default=None)
    args = parser.parse_args()

    if args.__dict__['out_dir'] is None:
        print('Invalid inputs. Please check --help.')
        sys.exit(-1)
    # endif
  
    populate_links(args.__dict__['out_dir'])
# endif
