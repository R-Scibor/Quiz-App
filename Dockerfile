# --- STAGE 1: The Builder (Construction Site) ---
# Start with a Node.js image to build React. We name this stage 'frontend-builder' to refer to it later.
FROM node:18-alpine AS frontend-builder

# Set the directory inside the temporary builder container where we will work.
WORKDIR /app/frontend

# Copy package files first! This allows Docker to cache the 'npm install' step
# if your dependencies haven't changed, speeding up re-builds.
COPY frontend/package.json frontend/package-lock.json ./

# Install the dependencies listed in package.json.
RUN npm install

# Copy the rest of the frontend source code.
COPY frontend/ ./

# Compile the React app into static files (HTML/CSS/JS) in the 'dist' folder.
RUN npm run build

# --- STAGE 2: The Final Image (The Living Space) ---
# Start fresh with a lightweight Python image. The node_modules and build tools are gone.
FROM python:3.11-slim

# Prevent Python from writing .pyc files and bufferring stdout (good for logs).
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory for the application in the final container.
WORKDIR /app

# Copy python dependencies and install them.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend code from your local machine to the container.
COPY . .

# --- THE BRIDGE ---
# Copy ONLY the built frontend files ('dist' folder) from the 'frontend-builder' stage.
# We place them where Django expects to find them.
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Copy the entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Set the entrypoint to our script
ENTRYPOINT ["/app/entrypoint.sh"]

# The default command (passed to "exec $@" in entrypoint.sh)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "backend_project.wsgi"]