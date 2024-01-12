FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY export_event_exchange_sfdc.py .

ENTRYPOINT [ "python", "./export_event_exchange_sfdc.py" ]