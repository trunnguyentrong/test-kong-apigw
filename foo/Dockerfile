FROM python:3-alpine

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt
COPY foo.py .

EXPOSE 8000

CMD ["python", "foo.py"]