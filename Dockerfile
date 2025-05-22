# Use official Python base image with conda
FROM continuumio/miniconda3:latest

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory to the repo root
WORKDIR /Datanalytics

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    postgresql-client \
    redis-tools \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Copy environment files first
COPY environment.yaml .

# Clean conda cache
RUN conda clean --all -y

# Create datanalytics_env conda environment
RUN conda env create -f environment.yaml

# Create gizmo environment directly with conda command (not from file)
RUN conda create -n gizmo python=3.11 pip -y

# Make conda activate command available
RUN echo "conda activate datanalytics_env" >> ~/.bashrc
ENV PATH /opt/conda/envs/datanalytics_env/bin:$PATH

# Copy all project files
COPY . /Datanalytics/

# Set proper permissions
RUN chmod +x /Datanalytics/datanalytics/gizmo/main.py

# Verify environments were created
RUN conda env list

# Expose port
EXPOSE 8000

# Copy entrypoint script
COPY entrypoint.sh /Datanalytics/entrypoint.sh

# Force LF line endings (convert CRLF to LF)
RUN sed -i 's/\r$//' /Datanalytics/entrypoint.sh

RUN chmod +x /Datanalytics/entrypoint.sh

# Set entrypoint
ENTRYPOINT ["/Datanalytics/entrypoint.sh"]

# Default command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
