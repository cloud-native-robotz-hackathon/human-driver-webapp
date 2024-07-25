FROM registry.access.redhat.com/ubi9/python-312:1-20

COPY requirements.txt /

RUN pip install --no-cache-dir -r /requirements.txt

ENV FLASK_APP=server \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8

EXPOSE 5000

WORKDIR /app
COPY *.py /app
ADD static/ /app/static/
ADD templates/ /app/templates/
CMD python3 -m flask run --host 0.0.0.0