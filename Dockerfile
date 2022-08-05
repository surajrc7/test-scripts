FROM nikolaik/python-nodejs:python3.8-nodejs18-slim

# Install curl, node, & yarn
WORKDIR /app/frontend
RUN apt-get update && apt-get install -y --no-install-recommends gfortran libopenblas-dev liblapack-dev && rm -rf /var/lib/apt/lists/*
RUN pip3 install cython
RUN apt update && apt install -y --no-install-recommends g++ && apt remove -y g++ && rm -rf /var/lib/apt/lists/*
RUN python -m pip install setuptools

RUN npm i yarn
COPY ./project /app/project
COPY ./frontend /app/frontend
RUN yarn install

WORKDIR /app/project
# Install Python dependencies
COPY ./project/requirements.txt /app/project/
RUN pip install -r requirements.txt

WORKDIR /app
# SECRET_KEY is only included here to avoid raising an error when generating static files.
# Be sure to add a real SECRET_KEY config variable in Heroku.
EXPOSE 8080
EXPOSE 3000

ENV PYTHONUNBUFFERED  "1"

COPY entry-point.sh /app/entry-point.sh

CMD ["/bin/bash", "/app/entry-point.sh"]