FROM python:2

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["celery", "-A", "cart", "worker", "-l", "info"]
