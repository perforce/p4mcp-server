FROM python:3.12-slim

LABEL io.modelcontextprotocol.server.name="io.github.perforce/p4mcp-server"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Create non-root user and setup permissions
RUN useradd -u 1000 -m -s /bin/bash mcpuser && \
    mkdir -p /app/logs && \
    chown -R mcpuser:mcpuser /app/logs
    
# Set environment variables
ENV PYTHONPATH=/app
ENV P4TICKETS=/home/mcpuser/.p4tickets
 
# Switch to non-root user
USER mcpuser

# Run the serve
ENTRYPOINT ["python3", "-m", "src.main"]
CMD ["--transport", "stdio"]