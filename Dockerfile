FROM python:3.12-slim

LABEL io.modelcontextprotocol.server.name="io.github.perforce/p4mcp-server"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m mcpuser
# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Set environment variables
ENV PYTHONPATH=/app
ENV P4TICKETS=/home/mcpuser/.p4tickets

# Run the server
ENTRYPOINT ["python3", "-m", "src.main"]
CMD ["--transport", "stdio"]
