FROM python:3.12-bookworm

WORKDIR /neopets
COPY . /neopets/

RUN pip install playwright==1.48.0 && \
    playwright install --with-deps

RUN pip install -r requirements.txt

CMD ["python", "main.py"]