FROM python:3.11.6
RUN mkdir /app
WORKDIR /app
RUN pip3 install aiogram==3.0.0
RUN pip3 install requests==2.31.0
RUN chmod 755 .
COPY bot ./bot/
COPY __init__.py .
#CMD ["python", "main.py"]