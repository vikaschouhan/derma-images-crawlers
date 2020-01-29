import os
import pickle
import requests
from   bs4 import BeautifulSoup

base_url = 'https://library.med.utah.edu/kw/derm/i_index/i_index.htm'

def mkdir(dir):
    if dir == None:
        return None
    # endif
    if not os.path.isdir(dir):
        os.makedirs(dir, exist_ok=True)
    # endif
# enddef

def rp(dir):
    if dir == None:
        return None
    # endif
    if dir[0] == '.':
        return os.path.normpath(os.getcwd() + '/' + dir)
    else:
        return os.path.normpath(os.path.expanduser(dir))
# enddef

def load_pickle(pickle_file):
    return pickle.load(open(pickle_file, 'rb')) if os.path.isfile(pickle_file) else None
# enddef

def save_pickle(pickle_obj, pickle_file):
    pickle.dump(pickle_obj, open(pickle_file, 'wb'))
# enddef

def scrape_main_page():
    req     = requests.get(base_url)
    soup    = BeautifulSoup(req.text, 'lxml')
    dls     = soup.find_all('dl')
    links   = []
    for dl_t in dls:
        lnks = dl_t.find_all('li')
        for lnk_t in lnks:
            url_t = requests.compat.urljoin(base_url, lnk_t.find('a').attrs['href'])
            lbl_t = lnk_t.find('strong').text
            links.append({'url' : url_t, 'label' : lbl_t})
        # endfor
    # endfor

    # Group links according to labels
    lnks    = {}
    for lnk_t in links:
        if lnk_t['label'] not in lnks:
            lnks[lnk_t['label']] = []
        # endif
        lnks[lnk_t['label']].append(lnk_t['url'])
    # endfor

    return lnks
# enddef

def scrape_next_level_pages(links):
    lnks = {}
    # Group links according to labels
    for lindx_t, lbl_t in enumerate(links):
        for indx_t, url_t in enumerate(links[lbl_t]):
            print('>> lblno=[{:<3}/{:<3}], sno=[{:<3}/{:<3}]'.format(lindx_t+1,
                len(links), indx_t+1, len(links[lbl_t])), end='\r')
            req   = requests.get(url_t)
            soup  = BeautifulSoup(req.text, 'lxml')
            try:
                img_t = requests.compat.urljoin(url_t, soup.find('span', {'id': 'mmlContent'}).find('img').attrs['src'])
            except AttributeError:
                print('>> ERROR::: No image found on ' + url_t, flush=True)
                continue
            # endtry
            txt_t = soup.find('span', {'id': 'mmlContent'}).text
            if lbl_t not in lnks:
                lnks[lbl_t] = []
            # endif
            lnks[lbl_t].append({'url' : img_t, 'metadata' : txt_t})
        # endfor
    # endfor

    return lnks
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
# enddef

def write_text(txt, txt_file):
    print(txt, file=open(txt_file, 'w'))
# enddef

def download_images(links, out_dir):
    mkdir(out_dir)
    for lindx_t, lbl_t in enumerate(links):
        lbln_t    = lbl_t.replace('/', ' - ')
        out_dir_t = '{}/{}'.format(out_dir, lbln_t)
        mkdir(out_dir_t)
        for indx_t, item_t in enumerate(links[lbl_t]):
            print('>> lblno=[{:<3}/{:<3}], sno=[{:<3}/{:<3}]'.format(lindx_t+1,
                len(links), indx_t+1, len(links[lbl_t])), end='\r')
            url_t     = item_t['url']
            metadata  = item_t['metadata']
            file_name = '{}____{}'.format(lbl_t.replace(' ', '_'), os.path.basename(url_t)).replace('/', ' - ')
            dst_file  = '{}/{}'.format(out_dir_t, file_name)
            txt_file  = '{}.txt'.format(dst_file)

            if os.path.isfile(dst_file):
                print('>> WARN:: Skipping already downloaded file {}'.format(dst_file))
            else:
                img_download(url_t, dst_file)
                write_text(metadata, txt_file)
            # endif
        # endfor
    # endfor
# enddef

if __name__ == '__main__':
    out_dir = './out_dir'
    m1_file = '{}/m1.pkl'.format(out_dir)
    m2_file = '{}/m2.pkl'.format(out_dir)
    d_dir   = '{}/images'.format(out_dir)
    mkdir(out_dir)

    if os.path.isfile(m1_file):
        print('>> m1 checkpoint found !! Not scraping first level pages.')
        m1  = load_pickle(m1_file)
    else:
        print('>> Scraping main page.')
        m1 = scrape_main_page()
        save_pickle(m1, m1_file)
    # endif

    if os.path.isfile(m2_file):
        print('>> m2 checkpoint found !! Not scraping 2nd level pages.')
        m2 = load_pickle(m2_file)
    else:
        print('>> Scraping 2nd level pages.')
        m2 = scrape_next_level_pages(m1)
        save_pickle(m2, m2_file)
    # endif

    print('>> Downloading images.')
    download_images(m2, d_dir)
# endif
