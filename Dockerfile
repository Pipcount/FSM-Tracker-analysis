# Official Python image : https://hub.docker.com/_/python
FROM python:3.12-slim

WORKDIR /app

COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "polar_test.py"]