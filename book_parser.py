import os
import json
from os import listdir
from os.path import isfile, join

import argparse
import pandas as pd
from bs4 import BeautifulSoup

def sorted_book(source):
    book_text = []
    book_sorted = []
    
    mydir = source
    
    htmfile = [f for f in listdir(mydir) if "htm" in f]
    with open(os.path.join(mydir, htmfile[0])) as file:
        page = file.read()
    
    soup = BeautifulSoup(page, 'html.parser')
    
    divs = soup.findAll('div')
    
    i = 0
    BookText = {}
    
    for div in divs:
        
        if div.has_attr('class') and 'bloom-translationGroup' in div.get('class'):
            entry = {}
            subdivs = div.findAll('div')
            
            for subdiv in subdivs:
                
                if (subdiv.has_attr('lang') and 
                        subdiv.get('lang') != '*' and 
                        subdiv.get('lang') != ''):
                    
                    texts = subdiv.findAll('p')
                    
                    book_text = ''
                    for text in texts:
                        if book_text != '':
                            book_text += '\n' + text.get_text()
                        else:
                            book_text = text.get_text()
                    entry[subdiv.get('lang')] = book_text
                    
            if len(entry.keys()) > 0:
                BookText[i] = entry
                    
            i += 1

    return BookText

def metadata(source):
    mpath = os.path.join(source, "meta.json")
    
    with open(mpath) as metadata:
        metadata = json.load(metadata)
    
    return metadata

def output(source, metadata, book_content, outdir):
    metadata.update(book_content)
   
    key = metadata['downloadSource']
    split_key = key.split('/')
    filename = split_key[1] + '.json'

    with open(os.path.join(outdir, filename), "w") as f:
        metadata_full = json.dump(
                metadata,f, indent="  ",
                check_circular=True, allow_nan=True,
                cls=None, separators=None
                )
    
    return metadata_full

def main():
    parser = argparse.ArgumentParser(
            description="Preprocess Bloom books"
            )

    parser.add_argument(
            "--source",dest='source',
            help="directory containing the input bloom book files"
            )
    parser.add_argument("--out", dest='out',
            help="output directory for parsed book files"
            )

    args = parser.parse_args()

    book_content = sorted_book(args.source)
    metadata_fin = metadata(args.source)
    output_fin = output(args.source, metadata_fin, book_content, args.out)

if __name__ == "__main__":
    main()

