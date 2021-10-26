FROM python

COPY requirements.txt .

RUN apt update && \
    apt-get install -y \
        protobuf-compiler && \
    pip install -r requirements.txt && \
    rm -rf var/lin/apt/lists/*

RUN mkdir /app
COPY book_parser.py /app/book_parser.py
COPY bloom_parse.sh /app/bloom_parse.sh

WORKDIR /app
