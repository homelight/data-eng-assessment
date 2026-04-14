FROM quay.io/astronomer/astro-runtime:13.6.0-python-3.12-slim

COPY requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir -r /tmp/requirements.txt
