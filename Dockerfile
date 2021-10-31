FROM python:3

RUN pip install --upgrade pip

RUN mkdir -p /app && chmod 755 /app

WORKDIR /app

RUN apt-get update \
	&& apt-get install -y ffmpeg

COPY . /app

RUN pip install .

RUN cp kamyroll.json.tmpl /app/config/kamyroll.json

ENTRYPOINT ["kamyroll"]
