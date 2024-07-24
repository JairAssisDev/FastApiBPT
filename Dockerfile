FROM python:3.11

WORKDIR /app

COPY . .

RUN curl https://pyenv.run | bash

RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --only main

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "16000"]
