FROM python:3.11
RUN useradd -m -u 1000 user
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
USER user
CMD ["tail", "-f", "/dev/null"]
