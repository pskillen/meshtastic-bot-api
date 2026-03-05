# Stage 1: Build Tailwind CSS
FROM node:24-slim AS builder

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY MeshtasticBotManager/package*.json ./

# Install Node.js dependencies
RUN npm install

# Copy the rest of the project files
COPY MeshtasticBotManager/ ./

# Run the Tailwind CSS build
RUN npm run tailwind

# Stage 2: Build the final image
FROM python:3.14-slim

# Add build argument for version
ARG VERSION=development

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV APP_VERSION=${VERSION}

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Django project
COPY ./MeshtasticBotManager /app/

# Replace version in settings.py
RUN sed -i "s/VERSION = os.environ.get('APP_VERSION', 'development')/VERSION = '${VERSION}'/" MeshtasticBotManager/settings.py

# Copy the generated Tailwind CSS file from the builder stage
COPY --from=builder /app/MeshtasticBotManager/static/css/tailwind.css /app/MeshtasticBotManager/static/css/tailwind.css

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose the port the app runs on
EXPOSE 8000

# Run the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
