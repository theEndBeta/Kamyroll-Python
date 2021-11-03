FROM python:3

RUN pip install --upgrade pip

RUN mkdir -p /app/config && chmod -R 0755 /app

WORKDIR /app

RUN apt-get update \
	&& apt-get install -y ffmpeg

COPY . /app

RUN pip install .

RUN cp /app/kamyroll.json.tmpl /app/config/kamyroll.json

ENTRYPOINT ["kamyroll"]
