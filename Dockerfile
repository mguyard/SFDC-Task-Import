FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY import-sfdc-task.py .

ENTRYPOINT [ "python", "./import-sfdc-task.py" ]