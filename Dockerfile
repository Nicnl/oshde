FROM python:2.7

# Intégration des sources
RUN mkdir /oshde-orchestrator
WORKDIR /oshde-orchestrator
COPY src src
COPY requirements.txt requirements.txt

# Installation des requirements python
RUN pip install -r requirements.txt

# On est prêts, on lance tout
CMD ['python', '-u', 'main.py']
