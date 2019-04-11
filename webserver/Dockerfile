FROM python:3.7-slim

ARG APP_ENV="dev"
ENV WORKER_HOME=home/worker/

RUN useradd -ms /bin/bash worker
COPY requirements.txt /requirements.txt
RUN python3 -m pip install -r /requirements.txt

USER worker

EXPOSE 5000
