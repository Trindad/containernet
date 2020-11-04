FROM python:3.7-alpine3.7

COPY ./requirements.txt /requirements.txt

RUN apk update \
&& apk upgrade \
&& apk add bash

RUN pip3 install -r /requirements.txt

COPY ./app /app

WORKDIR /app

RUN mkdir /app/log

CMD [ "python", "-u", "app.py" ]