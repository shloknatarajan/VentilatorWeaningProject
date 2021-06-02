FROM postgres

MAINTAINER "team41"

WORKDIR /docker-entrypoint-initdb.d

COPY ./db/init.sql /docker-entrypoint-initdb.d/init.sql

EXPOSE 5432