FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ARG PORT=5000
ENV PORT=${PORT}
EXPOSE ${PORT}

CMD ["python", "app.py"]
