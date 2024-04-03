FROM python:3.12-slim

WORKDIR /code

COPY poetry.lock pyproject.toml ./

RUN pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-root --without dev,test \
    && rm -rf $(poetry config cache-dir)/{cache,artifacts}

COPY ./main.py /code/main.py

ENTRYPOINT ["poetry", "run", "python", "main.py"]
