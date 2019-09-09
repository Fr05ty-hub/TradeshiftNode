FROM redis
COPY ./appendonly.aof ./data/appendonly.aof
FROM python:3.7-alpine
WORKDIR /data
ENV FLASK_APP python/app.py
ENV FLASK_RUN_HOST 0.0.0.0
RUN apk add --no-cache gcc musl-dev linux-headers
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
run pip install pytest
ADD python/tests/test_api.py /tests/
COPY . .
CMD ["flask", "run"]