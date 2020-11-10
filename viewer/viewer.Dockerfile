FROM python:3.7.6-slim-buster
RUN apt-get update && apt-get install -y openssh-server graphviz
COPY . /data_viewer
WORKDIR /data_viewer
RUN pip install --upgrade pip
RUN pip install -e /data_viewer
EXPOSE 5000
ENTRYPOINT [ "python" ]
CMD [ "/data_viewer/viewer/server_test.py" ]
