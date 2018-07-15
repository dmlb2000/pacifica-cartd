FROM python:3.6

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir amqp
COPY . .
CMD ["celery", "-A", "cart", "worker", "-l", "info"]
