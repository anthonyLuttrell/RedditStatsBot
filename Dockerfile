FROM pypy:3.9-slim
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=UTF-8
RUN mkdir /statsbot
RUN mkdir /statsbot/log
WORKDIR /statsbot
COPY . /statsbot/
RUN pip install -r requirements.txt
STOPSIGNAL SIGQUIT
CMD ["python","-u","main.py"]