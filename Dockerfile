FROM python:3

RUN mkdir /app && chmod 755 /app

WORKDIR /app

RUN apt-get update \
	&& apt-get install -y ffmpeg

COPY . /app

RUN pip install .

RUN cp kamyroll_python/kamyroll.json /app/

ENTRYPOINT ["kamyroll"]
