FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ENV TZ=America/Sao_Paulo \
    LANG=pt_BR.UTF-8 \
    LANGUAGE=pt_BR \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project \
 && uv run playwright install --with-deps --only-shell chromium \
 && apt-get update && apt-get install -y --no-install-recommends tzdata \
 && rm -rf /var/lib/apt/lists/*

COPY . .

CMD ["uv", "run", "--no-sync", "python", "Agente.py"]
