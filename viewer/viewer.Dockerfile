FROM python:alpine3.7
COPY . /data_viewer
WORKDIR /data_viewer
RUN pip install --upgrade pip
RUN apk update
RUN apk add make automake gcc g++ subversion python3-dev
RUN pip install /data_viewer
EXPOSE 5000
ENTRYPOINT [ "python" ]
CMD [ "/data_viewer/viewer/server.py" ]
