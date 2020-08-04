FROM frolvlad/alpine-python3

ENV AWS_ACCESS_KEY_ID=""
ENV AWS_SECRET_ACCESS_KEY=""

COPY source/* /opt/
COPY source/static/* /opt/static/
COPY source/templates/*.html /opt/templates/

RUN pip3 install -r /opt/requirements.txt

CMD ["/opt/app.py"]

ENTRYPOINT ["python3"]
