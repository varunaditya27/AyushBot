"""Certificate management for mTLS/TLS in AyushBot Cloud API.

Handles:
- Client certificate validation
- Certificate expiry checking
- Certificate metrics logging
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.x509 import ExtensionNotFound

logger = logging.getLogger(__name__)


class CertificateManager:
    """Manages TLS/mTLS certificates for AyushBot Cloud."""

    def __init__(self, ca_cert_path: str, ca_key_path: Optional[str] = None):
        """Initialize certificate manager.

        Args:
            ca_cert_path: Path to CA certificate (PEM format)
            ca_key_path: Path to CA private key (PEM format, optional)
        """
        self.ca_cert_path = Path(ca_cert_path)
        self.ca_key_path = Path(ca_key_path) if ca_key_path else None

        # Load CA certificate
        if not self.ca_cert_path.exists():
            raise FileNotFoundError(f"CA certificate not found: {self.ca_cert_path}")

        with open(self.ca_cert_path, "rb") as f:
            self.ca_cert = x509.load_pem_x509_certificate(
                f.read(), default_backend()
            )

        logger.info(
            f"Loaded CA certificate: {self.ca_cert.subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)[0].value}"
        )

        # Load CA private key if provided (for certificate generation)
        self.ca_key = None
        if self.ca_key_path and self.ca_key_path.exists():
            with open(self.ca_key_path, "rb") as f:
                self.ca_key = serialization.load_pem_private_key(
                    f.read(), password=None, backend=default_backend()
                )
            logger.info("Loaded CA private key for certificate generation")

    def validate_client_cert(
        self, cert_pem: bytes, check_expiry: bool = True
    ) -> Tuple[bool, str, Optional[dict]]:
        """Validate client certificate.

        Basic validation checks:
        - Certificate is valid PEM
        - Certificate is signed by CA (by checking issuer)
        - Certificate has not expired
        - Certificate supports client authentication

        Args:
            cert_pem: Client certificate in PEM format
            check_expiry: Whether to check certificate expiry

        Returns:
            Tuple of (is_valid, error_message, cert_metadata)
        """
        try:
            # Parse certificate
            client_cert = x509.load_pem_x509_certificate(
                cert_pem, default_backend()
            )

            # Check expiry - handle both naive and aware datetimes
            if check_expiry:
                now = datetime.utcnow()
                not_after = client_cert.not_valid_after_utc
                not_before = client_cert.not_valid_before_utc
                
                # Make sure we're comparing compatible types
                if not_after.tzinfo is not None and now.tzinfo is None:
                    # Certificate has timezone info, make now aware
                    now = now.replace(tzinfo=not_after.tzinfo)
                
                if now > not_after:
                    return False, "Certificate expired", None
                if now < not_before:
                    return False, "Certificate not yet valid", None

            # Check issuer matches CA (basic chain validation)
            if client_cert.issuer != self.ca_cert.subject:
                logger.warning(
                    f"Certificate issuer mismatch: "
                    f"cert={client_cert.issuer.rfc4514_string()} "
                    f"vs ca={self.ca_cert.subject.rfc4514_string()}"
                )
                return (
                    False,
                    "Certificate not issued by trusted CA",
                    None,
                )

            # Extract certificate metadata
            try:
                cn = client_cert.subject.get_attributes_for_oid(
                    x509.oid.NameOID.COMMON_NAME
                )
                common_name = cn[0].value if cn else "Unknown"
            except IndexError:
                common_name = "Unknown"

            try:
                org = client_cert.subject.get_attributes_for_oid(
                    x509.oid.NameOID.ORGANIZATION_NAME
                )
                organization = org[0].value if org else "Unknown"
            except IndexError:
                organization = "Unknown"

            # Check for client auth EKU (if present)
            try:
                eku = client_cert.extensions.get_extension_for_class(
                    x509.ExtendedKeyUsage
                )
                has_client_auth = (
                    x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH in eku.value
                )
                if not has_client_auth:
                    logger.warning(
                        f"Certificate {common_name} missing CLIENT_AUTH EKU"
                    )
                    return (
                        False,
                        "Certificate does not support client authentication",
                        None,
                    )
            except ExtensionNotFound:
                logger.warning(
                    f"Certificate {common_name} missing EKU extension"
                )

            metadata = {
                "common_name": common_name,
                "organization": organization,
                "serial_number": str(client_cert.serial_number),
                "issuer": client_cert.issuer.rfc4514_string(),
                "not_valid_before": client_cert.not_valid_before_utc.isoformat(),
                "not_valid_after": client_cert.not_valid_after_utc.isoformat(),
                "fingerprint": client_cert.fingerprint(hashes.SHA256()).hex(),
            }

            logger.info(
                f"✓ Client certificate valid: CN={common_name}, "
                f"Org={organization}, Serial={client_cert.serial_number}"
            )

            return True, "", metadata

        except Exception as e:
            error_msg = f"Certificate validation error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None

    def get_cert_info(self, cert_pem: bytes) -> Optional[dict]:
        """Extract certificate information without validation.

        Args:
            cert_pem: Certificate in PEM format

        Returns:
            Dictionary with certificate details or None if invalid
        """
        try:
            cert = x509.load_pem_x509_certificate(cert_pem, default_backend())

            try:
                cn = cert.subject.get_attributes_for_oid(
                    x509.oid.NameOID.COMMON_NAME
                )
                common_name = cn[0].value if cn else "Unknown"
            except IndexError:
                common_name = "Unknown"

            return {
                "common_name": common_name,
                "serial_number": cert.serial_number,
                "issuer": cert.issuer.rfc4514_string(),
                "not_valid_before": cert.not_valid_before_utc.isoformat(),
                "not_valid_after": cert.not_valid_after_utc.isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to extract cert info: {str(e)}")
            return None

    def is_cert_expired(self, cert_pem: bytes) -> bool:
        """Check if certificate is expired.

        Args:
            cert_pem: Certificate in PEM format

        Returns:
            True if expired, False otherwise
        """
        try:
            cert = x509.load_pem_x509_certificate(cert_pem, default_backend())
            now = datetime.utcnow()
            not_after = cert.not_valid_after_utc
            
            # Handle timezone-aware datetimes
            if not_after.tzinfo is not None and now.tzinfo is None:
                now = now.replace(tzinfo=not_after.tzinfo)
            
            return now > not_after
        except Exception:
            return True

    def get_days_until_expiry(self, cert_pem: bytes) -> Optional[int]:
        """Calculate days until certificate expires.

        Args:
            cert_pem: Certificate in PEM format

        Returns:
            Number of days until expiry, or None if error
        """
        try:
            cert = x509.load_pem_x509_certificate(cert_pem, default_backend())
            now = datetime.utcnow()
            not_after = cert.not_valid_after_utc
            
            # Handle timezone-aware datetimes
            if not_after.tzinfo is not None and now.tzinfo is None:
                now = now.replace(tzinfo=not_after.tzinfo)
            
            delta = not_after - now
            return max(0, delta.days)
        except Exception:
            return None

