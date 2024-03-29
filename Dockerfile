FROM python:3.10-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt
RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6 -y
RUN apt-get install -y libzbar0
RUN pip3 install -r requirements.txt

EXPOSE 80

COPY ./API .

CMD [ "python3", "app.py" ]
