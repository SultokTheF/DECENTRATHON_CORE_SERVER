FROM python:3.11

ENV PYTHONBUFFERED 1

WORKDIR /server

COPY requirements.txt /server/

RUN pip install -r requirements.txt

COPY . /server/

EXPOSE 8000

CMD ["sh", "-c", "python3 manage.py runserver 0.0.0.0:8000"]