FROM python:3.12-alpine

RUN apk add --no-cache iputils
WORKDIR /app
COPY monitor.py /app/monitor.py
RUN mkdir -p /app/results
CMD ["python", "/app/monitor.py"]
