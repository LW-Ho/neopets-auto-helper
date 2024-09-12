FROM mcr.microsoft.com/playwright/python:v1.46.0-jammy

WORKDIR /neopets
COPY . /neopets/

RUN pip install -r requirement.txt

CMD ["python", "main.py"]