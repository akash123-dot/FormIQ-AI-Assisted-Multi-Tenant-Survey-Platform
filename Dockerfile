FROM python:3.12-slim


COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.8.4 /lambda-adapter /opt/extensions/lambda-adapter


ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


WORKDIR /app


RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt


COPY . /app/

WORKDIR /app/smart_survey

ARG SECRET_KEY=dummy-build-key-not-used-in-production
ENV SECRET_KEY=$SECRET_KEY


RUN python manage.py collectstatic --noinput


ENV PORT=8000
EXPOSE 8000


CMD ["gunicorn", "smart_survey.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "1"]