FROM python:3-slim
WORKDIR /app
COPY . .
RUN pip install poetry
RUN poetry install --no-dev
ENTRYPOINT ["poetry","run","pyshacl"]
