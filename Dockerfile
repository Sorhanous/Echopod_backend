# Use an official lightweight Python image.
FROM python:3.9-slim

# Set the working directory in the container to /app.
WORKDIR /app

# Install system dependencies required for uWSGI and Python packages.
RUN apt-get update && apt-get install -y \
    gcc \
    libc6-dev \
    libpcre3 \
    libpcre3-dev \
    libssl-dev \
    git

# Copy the current directory contents into the container at /app.
COPY . /app

# Install any needed packages specified in requirements.txt.
RUN pip install --no-cache-dir -r requirements.txt

# Upgrade pip, setuptools, and wheel.
RUN pip install --upgrade pip setuptools wheel

# Clone and build uWSGI from source
RUN git clone https://github.com/unbit/uwsgi.git
WORKDIR /app/uwsgi
RUN python uwsgiconfig.py --build

# Return to app directory
WORKDIR /app

# Remove the build dependencies to keep the container light.
RUN apt-get purge -y \
    gcc \
    libc6-dev \
    libpcre3-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Make port 8080 available to the world outside this container.
EXPOSE 8080

# Define environment variable for detailed Flask logging.
ENV FLASK_ENV=development
ENV FLASK_APP=main.py
ENV PORT=8080


# Run main.py using uWSGI when the container launches.
CMD ["/app/uwsgi/uwsgi", "--http-socket", "0.0.0.0:8080", "--wsgi-file", "main.py", "--callable", "app", "--master", "--processes", "4", "--threads", "2"]
