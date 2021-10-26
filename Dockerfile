FROM python

COPY requirements.txt .

RUN pip install -r requirements.txt

RUN mkdir /app
COPY book_parser.py /app/book_parser.py
COPY bloom_parse.sh /app/bloom_parse.sh

WORKDIR /app
