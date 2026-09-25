FROM python:3.12-slim

LABEL io.modelcontextprotocol.server.name="io.github.perforce/p4mcp-server"

# Install system dependencies
# gosu is used by the entrypoint to drop privileges from root to mcpuser at runtime.
RUN apt-get update && apt-get install -y \
    build-essential \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY p4mcp/ ./p4mcp/

# Create non-root user and setup permissions
RUN useradd -u 1000 -m -s /bin/bash mcpuser && \
    mkdir -p /app/logs && \
    chown -R mcpuser:mcpuser /app/logs
    
# Set environment variables
ENV PYTHONPATH=/app
# Default tickets path. The entrypoint may override this at runtime to
# /home/mcpuser/.p4tickets-runtime after copying a bind-mounted ticket.
ENV P4TICKETS=/home/mcpuser/.p4tickets

# Install the entrypoint that normalizes a bind-mounted p4tickets file for
# mcpuser and then drops privileges. The container intentionally starts as
# root (no trailing USER directive) so the entrypoint can perform the copy;
# it exec's the server as mcpuser via gosu, so the process runs non-root.
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Run the server
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["python3", "-m", "p4mcp.main", "--transport", "stdio"]