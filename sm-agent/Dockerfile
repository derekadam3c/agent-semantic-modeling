# syntax=docker/dockerfile:1

# Multi-stage Docker build for Power BI Semantic Modeling Agent
# Stage 1: Builder - compile dependencies and wheels
FROM python:3.11-slim as builder

# Set build arguments
ARG VERSION=1.0.0

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install dependencies
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip wheel && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Production - minimal runtime image
FROM python:3.11-slim as production

# Set version metadata
ARG VERSION=1.0.0
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.title="Power BI Semantic Modeling Agent"
LABEL org.opencontainers.image.description="Azure AI Foundry agent for automated semantic model generation and deployment"

# Install runtime dependencies (curl for health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user for security
RUN useradd -m -u 1000 agent
WORKDIR /app
RUN chown -R agent:agent /app

# Copy application code
COPY --chown=agent:agent src/ /app/src/
COPY --chown=agent:agent pyproject.toml /app/

# Set Python environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV VERSION=${VERSION}
ENV USE_MANAGED_IDENTITY=true

# Switch to non-root user
USER agent

# Expose agent HTTP port
EXPOSE 8000

# Health check configuration
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl --fail http://localhost:8000/health || exit 1

# Start the FastAPI agent
CMD ["python", "-m", "uvicorn", "src.agent.__main__:app", "--host", "0.0.0.0", "--port", "8000"]

# Stage 3: Development - with dev dependencies
FROM production as development

# Switch back to root to install dev dependencies
USER root

# Copy and install dev requirements
COPY requirements-dev.txt .
RUN /opt/venv/bin/pip install --no-cache-dir -r requirements-dev.txt

# Switch back to agent user
USER agent
