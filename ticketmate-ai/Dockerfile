FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    TICKETMATE_HOST=0.0.0.0 \
    TICKETMATE_PORT=8080

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY data ./ticketmate-ai/data
COPY static ./ticketmate-ai/static
COPY server.py ./ticketmate-ai/server.py

EXPOSE 8080

CMD ["opentelemetry-instrument", "python", "ticketmate-ai/server.py"]
