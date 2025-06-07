FROM python:3.13-slim

WORKDIR /backend

COPY requirements.txt ./requirements.txt

RUN pip install --no-cache-dir --upgrade -r ./requirements.txt

COPY . .

EXPOSE 8000

# Principle of least privilege: create a new user for running the application
RUN \
    groupadd -g 1001 runner_backend && \
    useradd -r -u 1001 -g runner_backend runner_backend && \
    chown -R runner_backend:runner_backend /backend

USER runner_backend

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
