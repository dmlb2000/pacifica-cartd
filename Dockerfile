FROM python:3.6

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir amqp pymysql 'psycopg2<2.8' cryptography redis
ENV PEEWEE_PROTO mysql
ENV PEEWEE_USER cartd
ENV PEEWEE_PASS cartd
ENV PEEWEE_PORT 3306
ENV PEEWEE_ADDR 127.0.0.1
ENV PEEWEE_DATABASE pacifica_cartd
COPY . .
RUN pip install .
ENTRYPOINT ["/bin/bash", "/usr/src/app/entrypoint-celery.sh"]
