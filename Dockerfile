FROM python:3.14-alpine3.21

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN pip install --upgrade pip \
    && pip install fastapi uvicorn httpx pydantic

COPY src/ src/

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "80"]
EXPOSE 80
