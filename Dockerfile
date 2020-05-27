FROM python:3.6

WORKDIR /app

COPY ./requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

EXPOSE 8000

ENTRYPOINT [ "gunicorn", "wsgi:app", "--bind", "0.0.0.0:8000" ]
