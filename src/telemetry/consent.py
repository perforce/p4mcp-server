import sys
import subprocess
import json
import uuid
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class TelemetryConsentManager:
    """Manages telemetry consent configuration and user interaction."""
    
    def __init__(self, config_path: Path = None):
        """Initialize the consent manager with optional custom config path."""
        self.consent_config_path = config_path or Path.home() / '.p4mcp_telemetry_consent.json'
    
    def get_consent(self) -> bool:
        """Get telemetry consent from user by launching the consent dialog."""
        try:
            if getattr(sys, 'frozen', False):
                # Find Python executable in the bundle or use system Python
                bundle_dir = Path(sys.executable).parent / "_internal"
                if sys.platform.startswith("win"):
                    consent_ui = bundle_dir / "consent" / "P4MCP.exe"
                else:
                    consent_ui = bundle_dir / "consent" / "P4MCP"

                subprocess.run([str(consent_ui)], check=True)
            else:
                subprocess.run([sys.executable, "-m", "src.telemetry.consent_ui"], check=True)
        except Exception as e:
            logger.error(f"Telemetry consent subprocess failed: {e}")

    def consent_config_exists(self) -> bool:
        """Check if telemetry consent config file exists."""
        if self.consent_config_path.exists():
            return True
        else:
            self.get_consent()
            return self.consent_config_path.exists()
    
    def is_consent_given(self) -> bool:
        """Check if user has consented to telemetry collection."""
        if not self.consent_config_exists():
            return False
        try:
            with open(self.consent_config_path, 'r') as f:
                consent_data = json.load(f)
                return consent_data.get('telemetry_consent', False)
        except (json.JSONDecodeError, IOError):
            logger.error("Failed to read or parse telemetry consent config file.")
            return False
    
    def reset_consent(self) -> bool:
        """Reset consent by removing the config file."""
        try:
            if self.consent_config_path.exists():
                self.consent_config_path.unlink()
                return True
            return True
        except Exception as e:
            logger.error(f"Failed to reset consent: {e}")
            return False
    
    def set_consent(self) -> bool:
        """Programmatically set consent without showing dialog."""
        try:
            if not self.consent_config_path.exists():
                consent_data = {
                    'user_id': str(uuid.uuid4()).upper(),  # Store user ID as a UUID
                    'dialog_shown': False
                }
            else:
                with open(self.consent_config_path, 'r') as f:
                    consent_data = json.load(f)
                with open(self.consent_config_path, 'w') as f:
                    json.dump(consent_data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to set consent: {e}")
            return False

# Global instance for backward compatibility
_default_manager = TelemetryConsentManager()

# Backward compatibility functions
def get_consent() -> bool:
    """Get telemetry consent from user."""
    return _default_manager.get_consent()

def consent_config_exist() -> bool:
    """Check if telemetry consent config file exists."""
    return _default_manager.consent_config_exists()

def is_consent_given() -> bool:
    """Check if user has consented to telemetry collection."""
    return _default_manager.is_consent_given()

def set_consent() -> bool:
    """Programmatically set consent without showing dialog."""
    return _default_manager.set_consent()
