FROM python:3.7-slim

ARG APP_ENV="dev"

RUN useradd -ms /bin/bash worker
COPY requirements.txt /requirements.txt
RUN python3 -m pip install -r /requirements.txt

USER worker
WORKDIR /home/worker

EXPOSE 5000 5050
