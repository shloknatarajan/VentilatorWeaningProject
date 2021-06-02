FROM ubuntu:16.04

MAINTAINER "team41"

RUN apt-get update -y && \
    apt-get install -y python-pip python-dev

#WORKDIR /app

#COPY . /app

#RUN pip install -r requirements.txt


###
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt
COPY . /app
###
EXPOSE 5000

ENTRYPOINT [ "python" ]

CMD [ "app.py" ]


COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt
COPY . /app