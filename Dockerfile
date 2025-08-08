# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Create a non-root user
RUN useradd --create-home appuser
USER appuser
WORKDIR /home/appuser/app

# Copy dependency configuration files
COPY --chown=appuser:appuser requirements.txt setup.cfg setup.py ./

# Install dependencies
# We install dependencies first to leverage Docker layer caching
RUN pip install --no-cache-dir --user -r requirements.txt
RUN pip install --no-cache-dir --user .

# Copy the rest of the application code
COPY --chown=appuser:appuser . .

# Expose the port that Streamlit runs on
EXPOSE 8501

# Set the healthcheck
HEALTHCHECK CMD streamlit healthcheck

# Command to run the application
CMD ["streamlit", "run", "app.py"]
