import argparse
import cld3
import pandas as pd
import os
import json
from os import listdir
from os.path import isfile, join
from bs4 import BeautifulSoup

def sorted_book(source):
  book_text = []
  book_sorted = []
  mydir = source
  htmfile = [f for f in listdir(mydir) if "htm" in f]
  with open(os.path.join(mydir, htmfile[0])) as file:
    page = file.read()
  soup = BeautifulSoup(page, 'html.parser')
  book = soup.select("div p")
  for text in book:
    if text.get_text() != '':
      book_text = text.get_text()
      book_language = cld3.get_language(str(book_text)).language
      if book_language != 'en' and book_language != 'un':
        book_sorted.append(book_text)
  return book_sorted

def metadata(source):
  mpath = os.path.join(source, "meta.json")
  with open(mpath) as metadata:
    metadata = json.load(metadata)
  return metadata

def output(source, metadata, book_content, outdir):
  text_key = {'BookText': book_content}
  metadata.update(text_key)
  with open(os.path.join(outdir, "out.json"), "w") as f:
    metadata_full = json.dump(metadata,f, indent="  ", check_circular=True, allow_nan=True, cls=None, separators=None)
  return metadata_full

def main():
  parser = argparse.ArgumentParser(description="Preprocess Bloom books")

  parser.add_argument("--source",dest='source',help="directory containing the input bloom book files")
  parser.add_argument("--out", dest='out', help="output directory for parsed book files")

  args = parser.parse_args()

  book_content = sorted_book(args.source)
  metadata_fin = metadata(args.source)
  output_fin = output(args.source, metadata_fin, book_content, args.out)

if __name__ == "__main__":
  main()

