FROM python:3.6

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir 'celery[librabbitmq]'
COPY . .
CMD ["celery", "-A", "cart", "worker", "-l", "info"]
