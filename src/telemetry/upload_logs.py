import os
import json
import requests
import logging

logger = logging.getLogger(__name__)

end_point="https://api.p4mcp.perforce.com"

def upload_logs(file_path, end_point=end_point, chunk_size=500):
    """Upload log file to logstash in NDJSON format."""

    if not end_point:
        logger.error("No server URL provided for log upload.")
        return False

    if not os.path.exists(file_path):
        logger.error(f"Error: File '{file_path}' not found")
        return False

    try:
        with open(file_path, 'r') as file:
            chunk = []
            for line in file:
                line = line.strip()
                if not line:
                    continue
                try:
                    doc = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning(f"Skipping invalid JSON line: {line}")
                    continue

                chunk.append(json.dumps(doc))

                if len(chunk) >= chunk_size :
                    try:
                        send_request(end_point, chunk)
                    except Exception as e:
                        logger.error(f"Failed to send log chunk: {e}")   
                    chunk = []

            # Send any remaining lines
            if chunk:
                try:
                    send_request(end_point, chunk)
                except Exception as e:
                    logger.error(f"Failed to send final log chunk: {e}")


        # Delete the file after successful upload
        os.remove(file_path)
        logger.info(f"Successfully uploaded and deleted log file: {file_path}")
        logger.info("Log upload completed successfully.")
        return True

    except requests.exceptions.ConnectionError:
        logger.error("Error: Cannot connect to server. Is it running?")
        return False
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return False


def send_request(end_point, chunk, auth=None):
    """Send log request and check for errors"""
    ndjson_data = "\n".join(chunk) + "\n"
    
    try:
        response = requests.post(
            end_point,
            data=ndjson_data,
            headers={'Content-Type': 'application/x-ndjson'},
            auth=auth
        )

        if response.status_code != 200:
            logger.error(f"Log upload failed: {response.status_code} {response.text}")
            return False

        # Check if response has content before trying to parse JSON
        if not response.text.strip():
            logger.error("Empty response received from server")
            return False

        try:
            resp_json = response.json()
        except json.JSONDecodeError as e:
            # Handle cases where server returns plain text like "ok"
            if response.text.strip().lower() in ['ok', 'success', 'accepted']:
                logger.info(f"Log upload successful (plain text response): {response.text.strip()}")
                return True
            else:
                logger.error(f"Invalid JSON response: {e}. Response text: {response.text[:200]}...")
                return False

        if resp_json.get("errors"):
            # Some docs failed
            logger.error(f"Log upload contained errors: {resp_json}")
            return False
        
        logger.info(f"Log upload successful: {resp_json}")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in send_request: {e}")
        return False
