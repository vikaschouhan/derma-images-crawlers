# dermnet-images-crawler
### DermNet
[Dermnet](www.dermnet.com) is a publicly available dataset of more than 23000 dermatologist-curated skin disease images.
According to [this doc](https://pdfs.semanticscholar.org/af34/fc0aebff011b56ede8f46ca0787cfb1324ac.pdf), Dermnet organizes the skin diseases biologically in a **two-level** taxonomy. The bottom-level contains more than 600 skin diseases in a fine-grained granularity. The top-level contains **23** skin disease classes. Each of the top-level skin disease class contains a subcollection of the bottom-level skin diseases.

--------------------------------------------------------------------------
### Overview
This crawler is based off https://github.com/tcxxxx/DermNet-images-crawler. The original code has been ported to python3 and made more modular and readable. Several cryptic looking variable names have been changed to more meaningful names. Cmd line has been added via argparse module. Also, fault tolerance has been added at various stages of the crawling process. Thus, if the crawling process gets interrupted midway, it's possible to resume exactly from that point !!
In the code, several helpful modules were used:
- [Requests](http://docs.python-requests.org/en/master/)
- [Pillow](https://pillow.readthedocs.io/en/3.1.x/reference/Image.html)
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- io
- os
- shutil
- argparse

--------------------------------------------------------------------------
### Usage
python3 crawler.py --out_dir OUTPUT_DIR
where OUTPUT_DIR is the output directory where all downloaded images and temporary files are going to be saved.
