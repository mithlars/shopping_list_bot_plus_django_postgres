FROM dot_base:latest
WORKDIR /bot
COPY bot/ ./
COPY __init__.py .
#CMD ["python", "main.py"]