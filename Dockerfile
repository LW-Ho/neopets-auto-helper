FROM apify/actor-python-playwright-camoufox:3.12-1.58.0

COPY . ./

RUN pip install -r requirements.txt

CMD ["python", "main.py"]