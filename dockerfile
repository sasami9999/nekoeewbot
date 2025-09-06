FROM python:3.12.5
ARG dir=/workdir
WORKDIR $dir
COPY . .
RUN pip install -U pip && \
    pip install --no-cache-dir -r /workdir/src/requirements.txt
VOLUME $dir
CMD ["python","./src/discordbot_test.py"]