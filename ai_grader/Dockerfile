FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Install CPU-only torch first to avoid pulling 3GB+ CUDA packages and to
# stay on a version compatible with sentence-transformers 3.0.1
RUN pip install --no-cache-dir torch==2.3.1+cpu --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download model at build time so the container starts ready faster
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2', device='cpu', model_kwargs={'low_cpu_mem_usage': False})"

COPY main.py .

# Prevent sentence-transformers / huggingface_hub from hitting the network at runtime.
# The model is already baked into the image via the RUN step above.
ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

EXPOSE 8001
CMD ["python", "main.py"]
