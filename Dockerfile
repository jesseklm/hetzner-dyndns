FROM python:3-bullseye

WORKDIR /usr/src/app

COPY requirements.txt requirements.txt

RUN pip install --prefer-binary -r requirements.txt
# later use for packaging
# RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./main.py" ]
