FROM python:3.12-alpine

WORKDIR /usr/src/app

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

COPY . .

CMD [ "python", "./main.py" ]
