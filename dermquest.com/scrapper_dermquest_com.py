import requests
import os, sys
import json
import copy
#from PIL import image

facet_url = 'https://www.dermquest.com/Services/facetData.ashx'

def mkdir(dir):
    if not os.path.isdir(dir):
        os.mkdir(dir)
    # endif
# enddef

def rp(dir):
    return os.path.expanduser(dir)
# enddef

def __gd(x):
    return x.replace('/', '_____').replace(',', '______')
# enddef

# For recursive node parsing
def parse_node(top_dict_node, parent_facet_id, flat_dict, init_text):
    # SUCKER !! top level keys are strings but same keys are integers when referrred to
    # some other node. This a json file issue
    # The parent_facet_id which we got from some other node is an integer, but it needs
    # to be cast to string since all top lavel keys are strings
    parent_facet_id = str(parent_facet_id)

    node_this  = top_dict_node[parent_facet_id]

    facet_list = node_this["Facets"]
    facet_text = '{}____{}'.format(init_text, node_this["Text"]) if init_text else node_this["Text"]

    # Check if it's final node
    if facet_list == []:
        flat_dict[parent_facet_id] = facet_text
        return 0
    # This is an intermediate node, hence iterate over all facet ids
    else:
        for facet_t in facet_list:
            parse_node(top_dict_node, facet_t, flat_dict, facet_text)
        # endfor
    # endif
# enddef

def get_facets():
    req_t      = requests.get(facet_url)
    facet_json = req_t.json()

    # This is a flat dictionary
    facets_flat_dict = {}
    facets_tree_dict = {}

    for head_key_t in facet_json["facet_collection"]:
        head_value_t = facet_json["facet_collection"][head_key_t]

        # Populate as flat dict
        facets_flat_dict[head_key_t] = {}
        for sub_key_t in head_value_t["Facets"]:
            sub_value_text_t = head_value_t["Facets"][sub_key_t]["Text"]
            facets_flat_dict[head_key_t][sub_key_t] = sub_value_text_t
        # endfor

        # Populate as tree dict (also flat but takes into account names of previous nodes)
        facets_tree_dict[head_key_t] = {}
        for top_sub_key_t in head_value_t["Roots"]:
            parse_node(head_value_t["Facets"], top_sub_key_t, facets_tree_dict[head_key_t], None)
        # endfor
    # endfor

    return facets_tree_dict, facets_flat_dict
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

# @args :-
#          facet           : facet is either single facet_id or list of facet ids
#          facet_tree_dict : this is the dictionary which we get from get_facets() function above
#          retrieval_mode  : This is one of ['lesions', 'localization', 'symptoms', 'pathos', 'diagnosis']
def query_facets_single(facet, facet_tree_dict, retrieval_mode, max_retries=5):
    # All possible retrieval types supported
    retrieval_mode_type_list = list(facet_tree_dict.keys())

    # Check for error conditions
    if retrieval_mode not in retrieval_mode_type_list:
        print('Error !! Wrong retrieval_mode {}. Supported values are {}'.format(retrieval_mode, retrieval_mode_type_list))
        return
    # endif

    if isinstance(facet, list):
        facet_str = '|'.join([str(x) for x in facet])
    else:
        facet_str = str(facet)
    # endif

    retrieval_url_template = 'https://www.dermquest.com/Services/imageData.ashx?{}={}&page='.format(retrieval_mode, facet_str) + '{}'
    # Iterate
    page_no = 1
    result_list = []
    req_t = None
    max_page_no = None

    while True:
        # If max_page_no is defined and current page no > max_page_no, exit this loop
        if max_page_no and page_no > max_page_no:
            break
        # endif

        # Try to query the url. Return for max_retries
        x_attempt = 1
        while True:
            act_url_t = retrieval_url_template.format(page_no)
            print('Query {}'.format(act_url_t))
            req_t     = requests.get(act_url_t)
            if req_t.status_code != 200:
                if x_attempt > max_retries:
                    print('Query of {} failed !! Reason {}'.format(act_url_t, req_t.reason))
                    return
                else:
                    # Try another attempt
                    x_attempt = x_attempt + 1
                    continue
                # endif
            else:
                break
            # endif
        # endwhile

        # Read response json
        req_json = req_t.json()

        # If the url returned empty results, break this loop and return since there is no more
        # data to fetch
        if req_json["Results"] == []:
            break
        # endif
        max_page_no = req_json["NumberOfPages"] if "NumberOfPages" in req_json else None

        results = req_json["Results"]
        
        # Iterate over all results
        for case_t in results:
            #
            m_klist = ["localization", "diagnosis", "pathos", "symptoms", "lesions"]

            # Modify dictionary
            for rt_k_t in m_klist:
                if rt_k_t in case_t:
                    for rtitem_indx_t in range(len(case_t[rt_k_t])):
                        rtitem_id_t = case_t[rt_k_t][rtitem_indx_t]["Id"]
                        # Same f***ing reason as mentioned in parse_node
                        # Convert integer to string for key access
                        rtitem_id_t = str(rtitem_id_t)
                        if rtitem_id_t in facet_tree_dict[rt_k_t]:
                            rtitem_id_name = facet_tree_dict[rt_k_t][rtitem_id_t]
                        else:
                            rtitem_id_name = ''
                        # endif

                        # Add name also
                        case_t[rt_k_t][rtitem_indx_t]["IdName"] = rtitem_id_name
                    # endfor
                # endif
            # endfor

            result_list.append(copy.copy(case_t))
        # endfor

        # Increment page count
        page_no = page_no + 1
    # endwhile

    return result_list
# enddef


# @args :-
#          facet_tree_dict : dictionary returned by get_facets()
#          out_dir         : output directory for keeping database files for each category
#          retrieval_mode  : should be one of ['lesions', 'localization', 'symptoms', 'pathos', 'diagnosis'].
#                            By default it's diagnosis
# NOTE: The server kicks us out after sometime, so this probably need to be run multiple times
def query_facets(facet_tree_dict, out_dir, retrieval_mode='diagnosis', max_retries=5):
    # All possible retrieval types supported
    retrieval_mode_type_list = list(facet_tree_dict.keys())

    # Check for error conditions
    if retrieval_mode not in retrieval_mode_type_list:
        print('Error !! Wrong retrieval_mode {}. Supported values are {}'.format(retrieval_mode, retrieval_mode_type_list))
        return
    # endif

    # mkdir if the dir doesn't exist
    mkdir(out_dir)
    facet_id_dict = facet_tree_dict[retrieval_mode]

    for facet_id_t in facet_id_dict:
        facet_name_t = facet_id_dict[facet_id_t]
        # Sanitize this file name to remove weird characters
        file_t = '{}/{}.json'.format(out_dir, __gd(facet_name_t))

        if os.path.exists(file_t):
            print('{} already exists !! Skipping.'.format(file_t))
            continue
        # endif

        # Read all pages for this facet_id
        result_t = query_facets_single(facet_id_t, facet_tree_dict, retrieval_mode, max_retries)

        # Write results
        print('Writing results for facet_id {} to {}'.format(facet_id_t, file_t))
        json.dump({'result' : result_t}, open(file_t, 'w'))
    # endfor
# enddef

def __main__():
    out_dir = './facets_db'
    facets_db_dir = '{}/facets_diagnosis'.format(out_dir)
    facets_tree_dict_file = '{}/facets_tree_dict.json'.format(out_dir)
    facets_flat_dict_file = '{}/facets_flat_dict.json'.format(out_dir)

    if not os.path.exists(facets_tree_dict_file) or not os.path.exists(facets_flat_dict_file):
        print('Either {} or {} doesnot exit. Downloading facets metadata.'.format(facets_tree_dict_file, facets_flat_dict_file))
        facet_tree_dict, facet_flat_dict = get_facets()
        print('Saving facets metadata to {} & {}'.format(facets_tree_dict_file, facets_flat_dict_file))
        json.dump(facet_tree_dict, open(facets_tree_dict_file, 'w'))
        json.dump(facet_flat_dict, open(facets_flat_dict_file, 'w'))
    else:
        facet_tree_dict = json.load(open(facets_tree_dict_file, 'r'))
        facet_flat_dict = json.load(open(facets_flat_dict_file, 'r'))
    # endif

    # Call query
    query_facets(facet_tree_dict, facets_db_dir, 'diagnosis')
# enddef

__main__()
