FROM pypy:3.9-slim
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=UTF-8
RUN mkdir /statsbot
WORKDIR /statsbot
RUN mkdir /json
WORKDIR /statsbot
COPY . /statsbot/
RUN pip install -r requirements.txt
STOPSIGNAL SIGQUIT
CMD ["python", "main.py"]