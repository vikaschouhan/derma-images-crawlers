# Inspired by https://github.com/tcxxxx/DermNet-images-crawler
# Much of the logic is same as that of code from above repository.
# The new code has just been cleaned with more meaningful names and
# fault tolerance has been added. If the code gets interrupted midway, it's
# possible to resume from exact same point !!
# Same license applying to above repository applies here too !!
# Author : presentisgood@gmail.com
import requests
from   PIL import Image
from   bs4 import BeautifulSoup
from   io import BytesIO
import os
import shutil
from   pprint import pprint
import pickle
import argparse
import sys

type_name_list = ['Acne-and-Rosacea-Photos', 'Actinic-Keratosis-Basal-Cell-Carcinoma-and-other-Malignant-Lesions',
             'Atopic-Dermatitis-Photos', 'Bullous-Disease-Photos', 'Cellulitis-Impetigo-and-other-Bacterial-Infections', 
             'Eczema-Photos', 'Exanthems-and-Drug-Eruptions', 'Hair-Loss-Photos-Alopecia-and-other-Hair-Diseases',
             'Herpes-HPV-and-other-STDs-Photos', 'Light-Diseases-and-Disorders-of-Pigmentation',
             'Lupus-and-other-Connective-Tissue-diseases', 'Melanoma-Skin-Cancer-Nevi-and-Moles', 'Nail-Fungus-and-other-Nail-Disease', 
             'Poison-Ivy-Photos-and-other-Contact-Dermatitis', 'Psoriasis-pictures-Lichen-Planus-and-related-diseases', 
             'Scabies-Lyme-Disease-and-other-Infestations-and-Bites', 'Seborrheic-Keratoses-and-other-Benign-Tumors', 
             'Systemic-Disease', 'Tinea-Ringworm-Candidiasis-and-other-Fungal-Infections', 
             'Urticaria-Hives', 'Vascular-Tumors', 'Vasculitis-Photos', 'Warts-Molluscum-and-other-Viral-Infections']

def photo2links(photo_links):
    thumbr_links = []
    
    for url_t in photo_links:
        print('>> Query {}'.format(url_t), end='\r')
        soup_page = BeautifulSoup(requests.get(url_t).text, features='lxml')
        for link_t in soup_page.find_all("img"):
            link_tt = link_t.get("src")
            if 'Thumb' in link_tt:
                thumbr_links.append(link_tt.replace('Thumb', ''))
            # endif
        # endfor
    # endfor
    return list(set(thumbr_links))
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

def get_max_nums(link_t):
    req_t     = requests.get(link_t)
    html_page = req_t.text
    soup_page = BeautifulSoup(html_page, features='lxml')

    navigationl = soup_page.find_all("div", attrs={"class": "pagination"})
    max_links_num = 1

    if not navigationl:
        pass
    else:
        for navi_t in navigationl:
            for i in navi_t.children:
                try:
                    link_contents = i.contents[0]
                except:
                    pass
                else:
                    if link_contents == 'Next':
                        max_links_num = int(last_link_num)
                        break
                    else: 
                        last_link_num = link_contents
                    # endif
                # endtry
            # endfor
        # endfor
    # endif
    return int(max_links_num)
# enddef

def populate_stage1_links(type_name_list):
    root = 'http://www.dermnet.com'
    stage1_links = {}
    for type_name in type_name_list:
        print('>> Query type_name {}'.format(type_name), end='\r')
        req_t = requests.get(root + '/images/' + type_name)
        html_page = req_t.text
        soup_page = BeautifulSoup(html_page, features='lxml')

        sub_links = {}
        for link in soup_page.find_all('a'):
            id_this = link.get('href')
            if '/images/' in id_this:
                # Get subtype name
                sub_type = id_this.replace('/images/', '')
                # Store in hash
                sub_links[sub_type] = root + id_this
            # endif
        # endfor
        stage1_links[type_name] = sub_links
    # endfor

    return stage1_links
# enddef

def populate_stage2_links(stage1_links):
    fine_gr_dict = {}
    for type_name in stage1_links:
        fine_gr_dict[type_name] = {}
        for subtype_name in stage1_links[type_name]:
            print('>> Query subtype {}'.format(subtype_name), end='\r')
        
            link_t = stage1_links[type_name][subtype_name]
            max_links_num = get_max_nums(link_t)

            photo_links_list = []
            for i_link_num in range(max_links_num):
                photo_links_list.append(link_t + '/photos/' + str(i_link_num + 1))
            # endfor

            fine_gr_dict[type_name][subtype_name] = photo_links_list
        # endfor
    # endfor
    return fine_gr_dict
# enddef

def populate_stage3_links(stage2_links):
    fine_gr_dict = {}
    for type_name in stage2_links:
        fine_gr_dict[type_name] = {}
        for subtype_name in stage2_links[type_name]:
            fine_links = photo2links(stage2_links[type_name][subtype_name])
            fine_gr_dict[type_name][subtype_name] = fine_links
        # endfor
    # endfor
    return fine_gr_dict
# enddef

def main(out_dir):
    # make output dir
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
    # endif

    #############################################
    # Populate top links
    stage1_links_file = '{}/{}'.format(out_dir, 'stage1_links.pkl')
    if os.path.exists(stage1_links_file):
        print('{} found. Reading stage1_links from this file !!'.format(stage1_links_file))
        stage1_links = pickle.load(open(stage1_links_file, 'rb'))
    else:
        print('{} not found. Crawling.'.format(stage1_links_file))
        # Get top level links
        stage1_links = populate_stage1_links(type_name_list)
        print('Saving stage1_links in {}'.format(stage1_links_file))
        pickle.dump(stage1_links, open(stage1_links_file, 'wb'))
    # endif

    #############################################
    # Populate sub type photo links
    stage2_links_file = '{}/{}'.format(out_dir, 'stage2_links.pkl')
    if os.path.exists(stage2_links_file):
        print('{} found. Reading stage2_links from this file !!'.format(stage2_links_file))
        stage2_links = pickle.load(open(stage2_links_file, 'rb'))
    else:
        print('{} not found. Crawling.'.format(stage2_links_file))
        # Get top level links
        stage2_links = populate_stage2_links(stage1_links)
        print('Saving stage2_links in {}'.format(stage2_links_file))
        pickle.dump(stage2_links, open(stage2_links_file, 'wb'))
    # endif

    ##############################################
    # Populate finest level direct image links
    stage3_links_file = '{}/{}'.format(out_dir, 'stage3_links.pkl')
    if os.path.exists(stage3_links_file):
        print('{} found. Reading stage3_links from this file !!'.format(stage3_links_file))
        stage3_links = pickle.load(open(stage3_links_file, 'rb'))
    else:
        print('{} not found. Crawling.'.format(stage3_links_file))
        # Get top level links
        stage3_links = populate_stage3_links(stage2_links)
        print('Saving stage3_links in {}'.format(stage3_links_file))
        pickle.dump(stage3_links, open(stage3_links_file, 'wb'))
    # endif

    ##############################################
    # We have all the data now !!
    # Start downloading
    for type_name in stage3_links:
        for subtype_name in stage3_links[type_name]:
            for link_t in stage3_links[type_name][subtype_name]:
                # Make subdir
                subdir_t = '{}/{}/{}/{}'.format(out_dir, 'images', type_name, subtype_name)
                os.makedirs(subdir_t, exist_ok=True)

                # Start iterating
                photo_name = os.path.basename(link_t.rstrip('/'))
                photo_path = '{}/{}'.format(subdir_t, photo_name)

                if os.path.exists(photo_path):
                    print('>> Skipping {} as already downloaded !!'.format(photo_path))
                else:
                    print('>> Downloading {}'.format(link_t))
                    download_image(link_t, photo_path)
                # endif
            # endfor
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
