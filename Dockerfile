FROM python:2.7

MAINTAINER nicnl25@gmail.com

# 1] Intégration des sources
RUN mkdir /oshde-orchestrator
WORKDIR /oshde-orchestrator
COPY src src

# 2] Installation des requirements python
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# 3] On est prêts, on lance tout
WORKDIR /oshde-orchestrator/src
ENTRYPOINT ['python', '-u', 'main.py']
