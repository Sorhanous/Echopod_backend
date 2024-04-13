# Use an official lightweight Python image.
FROM python:3.9-slim

# Set the working directory in the container to /app.
WORKDIR /app

# Copy the current directory contents into the container at /app.
COPY . /app

# Install any needed packages specified in requirements.txt.
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8080 available to the world outside this container.
EXPOSE 8080

# Define environment variable for detailed Flask logging.
ENV FLASK_ENV=development
ENV FLASK_APP=main.py

# Install gevent for asynchronous worker support.
RUN pip install gevent

# Run main.py using Gunicorn with gevent workers when the container launches.
CMD gunicorn -b :$PORT --worker-class=gevent --worker-connections=1000 --workers=3 main:app
