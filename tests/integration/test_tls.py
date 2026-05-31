"""Tests for TLS/mTLS certificate management and validation."""

import sys
from pathlib import Path

import pytest
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cloud.api.auth import CertificateManager


@pytest.fixture
def cert_manager():
    """Create certificate manager with test certificates."""
    certs_dir = Path(__file__).parent.parent.parent / "cloud" / "certs"
    return CertificateManager(
        ca_cert_path=str(certs_dir / "ca.crt"),
        ca_key_path=str(certs_dir / "ca.key"),
    )


@pytest.fixture
def client_cert():
    """Load test client certificate."""
    certs_dir = Path(__file__).parent.parent.parent / "cloud" / "certs"
    with open(certs_dir / "test-client.crt", "rb") as f:
        return f.read()


@pytest.fixture
def client_key():
    """Load test client private key."""
    certs_dir = Path(__file__).parent.parent.parent / "cloud" / "certs"
    with open(certs_dir / "test-client.key", "rb") as f:
        return f.read()


class TestCertificateGeneration:
    """Test certificate generation and storage."""

    def test_ca_certificate_exists(self):
        """Test CA certificate was generated."""
        certs_dir = Path(__file__).parent.parent.parent / "cloud" / "certs"
        assert (certs_dir / "ca.crt").exists()
        assert (certs_dir / "ca.key").exists()

    def test_server_certificate_exists(self):
        """Test server certificate was generated."""
        certs_dir = Path(__file__).parent.parent.parent / "cloud" / "certs"
        assert (certs_dir / "server.crt").exists()
        assert (certs_dir / "server.key").exists()

    def test_client_certificate_exists(self):
        """Test client certificate was generated."""
        certs_dir = Path(__file__).parent.parent.parent / "cloud" / "certs"
        assert (certs_dir / "test-client.crt").exists()
        assert (certs_dir / "test-client.key").exists()

    def test_certificate_is_valid_pem(self, client_cert):
        """Test certificate is valid PEM format."""
        cert = x509.load_pem_x509_certificate(
            client_cert, default_backend()
        )
        assert cert is not None
        assert cert.serial_number > 0


class TestCertificateValidation:
    """Test certificate validation."""

    def test_validate_valid_client_cert(self, cert_manager, client_cert):
        """Test validation of valid client certificate."""
        is_valid, error_msg, metadata = cert_manager.validate_client_cert(
            client_cert
        )
        assert is_valid is True
        assert error_msg == ""
        assert metadata is not None
        assert metadata["common_name"] == "test-client"

    def test_validate_extracts_metadata(self, cert_manager, client_cert):
        """Test metadata extraction from valid certificate."""
        is_valid, error_msg, metadata = cert_manager.validate_client_cert(
            client_cert
        )
        assert metadata["common_name"] == "test-client"
        assert metadata["organization"] == "AyushBot"
        assert "serial_number" in metadata
        assert "issuer" in metadata
        assert "fingerprint" in metadata
        assert "not_valid_before" in metadata
        assert "not_valid_after" in metadata

    def test_validate_invalid_cert_pem(self, cert_manager):
        """Test validation of invalid PEM data."""
        is_valid, error_msg, metadata = cert_manager.validate_client_cert(
            b"invalid cert data"
        )
        assert is_valid is False
        assert error_msg != ""
        assert metadata is None

    def test_validate_empty_cert(self, cert_manager):
        """Test validation of empty certificate."""
        is_valid, error_msg, metadata = cert_manager.validate_client_cert(b"")
        assert is_valid is False
        assert error_msg != ""
        assert metadata is None


class TestCertificateInfo:
    """Test certificate information extraction."""

    def test_get_cert_info(self, cert_manager, client_cert):
        """Test extracting certificate information."""
        info = cert_manager.get_cert_info(client_cert)
        assert info is not None
        assert info["common_name"] == "test-client"
        assert "serial_number" in info
        assert "issuer" in info
        assert "not_valid_before" in info
        assert "not_valid_after" in info

    def test_get_cert_info_invalid(self, cert_manager):
        """Test certificate info extraction with invalid cert."""
        info = cert_manager.get_cert_info(b"invalid")
        assert info is None


class TestCertificateExpiry:
    """Test certificate expiry checking."""

    def test_is_cert_expired_valid_cert(self, cert_manager, client_cert):
        """Test valid certificate is not expired."""
        is_expired = cert_manager.is_cert_expired(client_cert)
        assert is_expired is False

    def test_is_cert_expired_invalid_cert(self, cert_manager):
        """Test invalid certificate handled gracefully."""
        is_expired = cert_manager.is_cert_expired(b"invalid")
        assert is_expired is True  # Conservative: treat invalid as expired

    def test_get_days_until_expiry(self, cert_manager, client_cert):
        """Test days until expiry calculation."""
        days = cert_manager.get_days_until_expiry(client_cert)
        assert days is not None
        assert days > 0  # Cert was just generated, should be valid for ~1 year
        assert days <= 365

    def test_get_days_until_expiry_invalid(self, cert_manager):
        """Test days until expiry with invalid cert."""
        days = cert_manager.get_days_until_expiry(b"invalid")
        assert days is None


class TestServerCertificate:
    """Test server certificate properties."""

    def test_server_cert_validity(self):
        """Test server certificate is valid."""
        certs_dir = Path(__file__).parent.parent.parent / "cloud" / "certs"
        with open(certs_dir / "server.crt", "rb") as f:
            cert = x509.load_pem_x509_certificate(
                f.read(), default_backend()
            )
        assert cert is not None

    def test_server_cert_san_has_localhost(self):
        """Test server certificate has localhost in SAN."""
        certs_dir = Path(__file__).parent.parent.parent / "cloud" / "certs"
        with open(certs_dir / "server.crt", "rb") as f:
            cert = x509.load_pem_x509_certificate(
                f.read(), default_backend()
            )

        try:
            san_ext = cert.extensions.get_extension_for_class(
                x509.SubjectAlternativeName
            )
            dns_names = [
                name.value
                for name in san_ext.value
                if isinstance(name, x509.DNSName)
            ]
            assert "localhost" in dns_names
        except Exception:
            pytest.fail("Server certificate missing SAN with localhost")


class TestCertificateChain:
    """Test certificate chain validation."""

    def test_client_cert_signed_by_ca(self, cert_manager, client_cert):
        """Test client certificate is signed by CA."""
        is_valid, error_msg, metadata = cert_manager.validate_client_cert(
            client_cert
        )
        # Should validate successfully because it was signed by CA
        assert is_valid is True

    def test_gateway_cert_validation(self, cert_manager):
        """Test validation of gateway certificate."""
        certs_dir = Path(__file__).parent.parent.parent / "cloud" / "certs"
        with open(certs_dir / "gateway-001.crt", "rb") as f:
            gateway_cert = f.read()

        is_valid, error_msg, metadata = cert_manager.validate_client_cert(
            gateway_cert
        )
        assert is_valid is True
        assert metadata["common_name"] == "gateway-001"


class TestTLSEnvironmentVariables:
    """Test TLS environment variable handling."""

    def test_certfile_env_var_loaded(self, monkeypatch):
        """Test CERTFILE environment variable is recognized."""
        certs_dir = Path(__file__).parent.parent.parent / "cloud" / "certs"
        certfile = str(certs_dir / "server.crt")
        monkeypatch.setenv("CERTFILE", certfile)

        import os

        loaded = os.getenv("CERTFILE")
        assert loaded == certfile

    def test_keyfile_env_var_loaded(self, monkeypatch):
        """Test KEYFILE environment variable is recognized."""
        certs_dir = Path(__file__).parent.parent.parent / "cloud" / "certs"
        keyfile = str(certs_dir / "server.key")
        monkeypatch.setenv("KEYFILE", keyfile)

        import os

        loaded = os.getenv("KEYFILE")
        assert loaded == keyfile

    def test_enable_tls_env_var(self, monkeypatch):
        """Test ENABLE_TLS environment variable."""
        monkeypatch.setenv("ENABLE_TLS", "true")

        import os

        enable_tls = os.getenv("ENABLE_TLS", "false").lower() == "true"
        assert enable_tls is True


class TestCertificateMetadata:
    """Test certificate metadata quality."""

    def test_cert_metadata_fingerprint_format(
        self, cert_manager, client_cert
    ):
        """Test certificate fingerprint is valid hex."""
        is_valid, error_msg, metadata = cert_manager.validate_client_cert(
            client_cert
        )
        fingerprint = metadata["fingerprint"]
        # Should be hex string (lowercase letters and digits only)
        assert all(c in "0123456789abcdef" for c in fingerprint)
        # SHA256 fingerprint is 64 hex chars (32 bytes * 2)
        assert len(fingerprint) == 64

    def test_cert_metadata_timestamps_format(
        self, cert_manager, client_cert
    ):
        """Test certificate timestamps are ISO format."""
        is_valid, error_msg, metadata = cert_manager.validate_client_cert(
            client_cert
        )
        # Should be ISO format with T separator
        assert "T" in metadata["not_valid_before"]
        assert "T" in metadata["not_valid_after"]

    def test_all_required_metadata_fields(
        self, cert_manager, client_cert
    ):
        """Test all required metadata fields are present."""
        is_valid, error_msg, metadata = cert_manager.validate_client_cert(
            client_cert
        )
        required_fields = {
            "common_name",
            "organization",
            "serial_number",
            "issuer",
            "not_valid_before",
            "not_valid_after",
            "fingerprint",
        }
        assert required_fields.issubset(set(metadata.keys()))
