FROM python:3.7-alpine
ADD src/requirements.txt /requirements.txt
RUN apk --no-cache add libpq jpeg-dev zlib-dev \
  && apk --no-cache add --virtual build-dependencies postgresql-dev build-base \
  && pip install -U pip setuptools \
  && pip install --no-cache-dir -r /requirements.txt \
  && apk del build-dependencies

ENV PYTHONUNBUFFERED 1

RUN mkdir /code/
WORKDIR /code/
ADD ./src /code/

EXPOSE 8080

ENV DJANGO_SETTINGS_MODULE=fannypack.settings

CMD ["python", "manage.py", "runserver", "0.0.0.0:8080"]
