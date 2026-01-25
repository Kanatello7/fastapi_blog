FROM python:3.12-slim AS build

WORKDIR /app 

RUN apt-get update -y && \ 
    apt-get install -y curl && \ 
    curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH="/root/.local/bin/:${PATH}"
COPY pyproject.toml uv.lock ./ 
RUN uv sync 

FROM python:3.12-slim AS runtime
COPY --from=build /app/.venv /app/.venv 

ENV PATH="/app/.venv/bin:${PATH}"

COPY . . 
RUN chmod +x start_app.sh