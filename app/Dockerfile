FROM python:3.13

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.env .
COPY . .


CMD ["uvicorn", "PetProject.src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]