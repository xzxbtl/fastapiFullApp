FROM python:3.13

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.env .
COPY . .

ENV PYTHONPATH=/app

CMD ["sh", "-c", "if [ $SERVICE_TYPE = 'bot' ]; then python -m bot.bot; else uvicorn PetProject.src.main:app --host 0.0.0.0 --port 8000 --reload; fi"]