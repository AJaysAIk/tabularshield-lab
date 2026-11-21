FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY data/processed ./data/processed
COPY data/manifest.json data/DATA_SOURCES.md ./data/
RUN pip install --no-cache-dir -e . && useradd --create-home researcher
USER researcher
EXPOSE 8000
CMD ["uvicorn", "tabularshield.api:app", "--host", "0.0.0.0", "--port", "8000"]

