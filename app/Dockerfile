FROM python:3.8

RUN apt-get update && apt-get install -y strace

ADD requirements.txt /
RUN pip install -r requirements.txt
ADD app.py watch_process.py /
ADD caps_mapping.json /
ENTRYPOINT /usr/local/bin/python