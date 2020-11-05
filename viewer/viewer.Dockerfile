FROM python:alpine3.7
COPY . /data_viewer
WORKDIR /data_viewer
RUN pip install --upgrade pip
RUN pip install cython
RUN pip install /data_viewer
EXPOSE 5000
ENTRYPOINT [ "python" ]
CMD [ "/data_viewer/viewer/server.py" ]
