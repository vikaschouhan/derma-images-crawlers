import requests
import os
import pickle
from   bs4 import BeautifulSoup

base_url = 'http://www.globalskinatlas.com/diagindex.cfm'

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

def scrape_front_page():
    req   = requests.get(base_url)
    soup  = BeautifulSoup(req.text, 'lxml')
    tbl   = soup.find('table', {'class' : 'text-med'})
    alist = tbl.find_all('a')
    links = {}
    for lnk_t in alist:
        if lnk_t.text == '':
            print('>> WARN:: Skipping {} due to No name !!'.format(lnk_t.attrs['href']))
            continue
        # endif
        links[lnk_t.text] = requests.compat.urljoin(base_url, lnk_t.attrs['href'])
    # endfor
    return links
# enddef

def scrape_2nd_level_pages(links):
    lnks_d = {}
    for indx_t, lbl_t in enumerate(links):
        print('>> [{:<3}/{:<3}]'.format(indx_t+1, len(links)), end='\r')
        url_t  = links[lbl_t]
        req    = requests.get(url_t)
        soup   = BeautifulSoup(req.text, 'lxml')
        a_lnks = soup.find_all('a')
        # Search for links which lead to 3rd level pages
        # Remove duplicates
        # Strip spaces from final links
        lnks   = list(set([x.attrs['href'].strip() for x in a_lnks if x.attrs['href'].startswith('imagedetail.cfm')]))
        lnks_d[lbl_t] = lnks
    # endfor
    return lnks_d
# enddef

def __scrape_3rd_level_page(url):
    req      = requests.get(url)
    soup     = BeautifulSoup(req.text, 'lxml')
    a_lnks   = soup.find_all('a')
    # Next level links
    n_links  = [x for x in  soup.find_all('a') if ('href' in x.attrs) and (x.attrs['href'].startswith('imagedetail.cfm'))]
    # Images corresponding to next level links
    n_ilinks = [x.find('img') for x in n_links]
    # Find all image links
    ilinks   = soup.find_all('img')
    # Find link with label "View Full Size"
    vlabel   = "View Full Size"
    v_links  = [x for x in a_lnks if x.text.strip() == vlabel]
    # Get image links after removing next level image links
    it_links = set(set(ilinks) - set(n_ilinks))
    # Remove logos. Only pick valid links
    it_linkt = [x for x in it_links if 'globalskinatlas.com/upload' in x.attrs['src']][0]

    # Check if "View Full Size" link is acually present on the page. If not,
    # pick the lower resolution thumbnail
    if len(v_links) > 0:
        # This is a <a> tag
        v_link = v_links[0]
        v_link_img = v_link.attrs['href']
    else:
        # This is a <img> tag
        v_link = it_linkt
        v_link_img = v_link.attrs['src']
    # endif

    # Get parent of v_link
    v_parent = v_link.parent

    # Debug information
    #print('n_links  = ', n_links)
    #print('n_ilinks = ',n_ilinks)
    #print('ilinks   = ', ilinks)
    #print('v_links  = ', v_links)
    #print('it_links = ', it_links)
    #print('it_linkt = ', it_linkt)
    #print('text     = ', v_parent.text)

    return {'img' : v_link_img, 'nlinks' : n_links, 'mdata' : v_parent.text}
# enddef

def scrape_3rd_level_page(url):
    data_t = __scrape_3rd_level_page(url)
    img_t  = data_t['img']
    # Next level links. Convert to canonical forms
    nlinks = [requests.compat.urljoin(base_url,  x.attrs['href']) for x in data_t['nlinks']]
    img_l  = []

    # Add this link to list
    img_l.append({'img': img_t, 'mdata': data_t['mdata']})

    # Iterate over child links
    for n_link_t in nlinks:
        ndata_t = __scrape_3rd_level_page(n_link_t)
        img_l.append({'img' : ndata_t['img'], 'mdata' : ndata_t['mdata']})
    # endfor

    return img_l
# enddef

def scrape_3rd_level_pages(links, out_dir):
    lnk_dict = {}
    for indx_t, lbl_t in enumerate(links):
        print('>> [{:<3}/{:<3}] -> {}'.format(indx_t+1, len(links), lbl_t), end='\r', flush=True)
        # Check if lbl_t has already been downloaded
        lbln_t  = lbl_t.replace('/', ' - ').strip()
        ckpt    = '{}/{}.pkl'.format(out_dir, lbln_t)
        if os.path.isfile(ckpt):
            print('>> WARN:: Skipping {} as checkpoint file found !!'.format(lbl_t))
            im_lnks = load_pickle(ckpt)
        else:
            im_lnks = []
            # Convert to canonical urls
            lnks_l = [requests.compat.urljoin(base_url, x) for x in links[lbl_t]]
            for lnk_t in lnks_l:
                im_lnks += scrape_3rd_level_page(lnk_t)
            # endfor

            # Save checkpoint
            save_pickle(im_lnks, ckpt)
        # endif

        lnk_dict[lbl_t] = im_lnks
    # endfor
    return lnk_dict
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

def download_images(link_dict, out_dir):
    mkdir(out_dir)
    for indx_t, lbl_t in enumerate(link_dict):
        lbln_t    = lbl_t.replace('/', ' - ').strip()
        out_dir_t = '{}/{}'.format(out_dir, lbln_t)
        mkdir(out_dir_t)

        print('>> [{:<3}/{:<3}] -> {}'.format(indx_t+1, len(link_dict), lbl_t), end='\r')
        for item_t in link_dict[lbl_t]:
            img_url = item_t['img']
            mdata   = item_t['mdata']
            fname   = '{}____{}'.format(lbln_t, os.path.basename(img_url))
            mfname  = '{}.txt'.format(fname)
            fpath   = '{}/{}'.format(out_dir_t, fname)
            mfpath  = '{}/{}'.format(out_dir_t, mfname)

            # Check if image was already downloaded
            if os.path.isfile(fpath):
                print('>> WARN:: Skipping {} as already downloaded !!'.format(fname))
                continue
            # endif

            # Save file
            img_download(img_url, fpath)
            # Save metadata
            write_text(mdata, mfpath)
        # endfor
    # endfor
# enddef

if __name__ == '__main__':
    out_dir = './out_dir'
    m1_file = '{}/m1.pkl'.format(out_dir)
    m2_file = '{}/m2.pkl'.format(out_dir)
    m3_dir  = '{}/m3_files'.format(out_dir)
    im_dir  = '{}/images'.format(out_dir)
    mkdir(out_dir)
    mkdir(m3_dir)
    mkdir(im_dir)

    # M1 pages
    if os.path.isfile(m1_file):
        print('>> m1 checkpoint found !! Not downloading first stage links.')
        m1  = load_pickle(m1_file)
    else:
        print('>> Downloading front page links')
        m1  = scrape_front_page()
        save_pickle(m1, m1_file)
    # endif

    # M2 pages
    if os.path.isfile(m2_file):
        print('>> m2 checkpoint found !! Not downloading 2nd stage links.')
        m2 = load_pickle(m2_file)
    else:
        print('>> Downloading 2nd level page links.')
        m2 = scrape_2nd_level_pages(m1)
        save_pickle(m2, m2_file)
    # endif

    # M3 pages
    m3 = scrape_3rd_level_pages(m2, m3_dir)

    # Download images
    download_images(m3, im_dir)
# endif
