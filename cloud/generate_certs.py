"""Generate self-signed certificates for local testing and development.

This script creates:
1. CA root certificate (ca.crt, ca.key)
2. Server certificate (server.crt, server.key)
3. Client certificate (client.crt, client.key)

Usage:
    python generate_certs.py [--output-dir ./certs]
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID, ExtensionOID


def generate_private_key(key_size: int = 2048) -> rsa.RSAPrivateKey:
    """Generate RSA private key."""
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
    )


def save_private_key(private_key: rsa.RSAPrivateKey, filepath: Path) -> None:
    """Save private key to file."""
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    filepath.write_bytes(pem)
    filepath.chmod(0o600)  # Restrict permissions
    print(f"✓ Saved private key: {filepath}")


def save_certificate(certificate: x509.Certificate, filepath: Path) -> None:
    """Save certificate to file."""
    pem = certificate.public_bytes(serialization.Encoding.PEM)
    filepath.write_bytes(pem)
    filepath.chmod(0o644)
    print(f"✓ Saved certificate: {filepath}")


def generate_ca_certificate(output_dir: Path) -> tuple:
    """Generate CA root certificate and private key."""
    print("\n📜 Generating CA root certificate...")

    # Generate CA private key
    ca_key = generate_private_key()

    # Generate CA certificate
    ca_subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "IN"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Maharashtra"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Pune"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "AyushBot"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Security"),
            x509.NameAttribute(NameOID.COMMON_NAME, "AyushBot CA"),
        ]
    )

    ca_cert = (
        x509.CertificateBuilder()
        .subject_name(ca_subject)
        .issuer_name(ca_subject)  # Self-signed
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=3650))  # 10 years
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_cert_sign=True,
                crl_sign=True,
                key_encipherment=False,
                content_commitment=False,
                data_encipherment=False,
                key_agreement=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .sign(ca_key, hashes.SHA256())
    )

    # Save CA files
    save_private_key(ca_key, output_dir / "ca.key")
    save_certificate(ca_cert, output_dir / "ca.crt")

    return ca_key, ca_cert


def generate_server_certificate(
    ca_key: rsa.RSAPrivateKey,
    ca_cert: x509.Certificate,
    output_dir: Path,
) -> tuple:
    """Generate server certificate signed by CA."""
    print("\n🖥️  Generating server certificate...")

    # Generate server private key
    server_key = generate_private_key()

    # Generate server certificate
    server_subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "IN"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Maharashtra"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Pune"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "AyushBot"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "API"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ]
    )

    server_cert = (
        x509.CertificateBuilder()
        .subject_name(server_subject)
        .issuer_name(ca_cert.issuer)  # Signed by CA
        .public_key(server_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=365))  # 1 year
        .add_extension(
            x509.SubjectAlternativeName(
                [
                    x509.DNSName("localhost"),
                    x509.DNSName("127.0.0.1"),
                    x509.DNSName("*.local"),
                    x509.IPAddress(
                        __import__("ipaddress").IPv4Address("127.0.0.1")
                    ),
                ]
            ),
            critical=False,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                key_cert_sign=False,
                key_agreement=False,
                content_commitment=False,
                data_encipherment=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage(
                [x509.oid.ExtendedKeyUsageOID.SERVER_AUTH]
            ),
            critical=True,
        )
        .sign(ca_key, hashes.SHA256())
    )

    # Save server files
    save_private_key(server_key, output_dir / "server.key")
    save_certificate(server_cert, output_dir / "server.crt")

    return server_key, server_cert


def generate_client_certificate(
    ca_key: rsa.RSAPrivateKey,
    ca_cert: x509.Certificate,
    output_dir: Path,
    client_name: str = "test-client",
) -> tuple:
    """Generate client certificate signed by CA."""
    print(f"\n🔐 Generating client certificate ({client_name})...")

    # Generate client private key
    client_key = generate_private_key()

    # Generate client certificate
    client_subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "IN"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Maharashtra"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Pune"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "AyushBot"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Gateway"),
            x509.NameAttribute(NameOID.COMMON_NAME, client_name),
        ]
    )

    client_cert = (
        x509.CertificateBuilder()
        .subject_name(client_subject)
        .issuer_name(ca_cert.issuer)  # Signed by CA
        .public_key(client_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=365))  # 1 year
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                key_cert_sign=False,
                key_agreement=False,
                content_commitment=True,
                data_encipherment=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage(
                [x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH]
            ),
            critical=True,
        )
        .sign(ca_key, hashes.SHA256())
    )

    # Save client files
    save_private_key(client_key, output_dir / f"{client_name}.key")
    save_certificate(client_cert, output_dir / f"{client_name}.crt")

    return client_key, client_cert


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Generate self-signed certificates for AyushBot"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent / "certs",
        help="Output directory for certificates",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing certificates",
    )

    args = parser.parse_args()
    output_dir = args.output_dir

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check for existing certificates
    if not args.force:
        existing = list(output_dir.glob("*.crt"))
        if existing:
            print(f"⚠️  Certificates already exist in {output_dir}")
            print("Use --force to overwrite")
            return

    print(f"🔑 Generating self-signed certificates in {output_dir}")

    # Generate CA
    ca_key, ca_cert = generate_ca_certificate(output_dir)

    # Generate server certificate
    server_key, server_cert = generate_server_certificate(
        ca_key, ca_cert, output_dir
    )

    # Generate client certificates
    generate_client_certificate(
        ca_key, ca_cert, output_dir, client_name="test-client"
    )
    generate_client_certificate(
        ca_key, ca_cert, output_dir, client_name="gateway-001"
    )

    # Print summary
    print("\n✅ Certificate generation complete!")
    print("\n📁 Generated files:")
    for cert_file in sorted(output_dir.glob("*")):
        print(f"   {cert_file.name}")

    print(
        "\n📌 Certificate Details:"
        "\n   CA: Valid for 10 years"
        "\n   Server: Valid for 1 year (localhost, 127.0.0.1, *.local)"
        "\n   Client: Valid for 1 year (test-client, gateway-001)"
    )

    print(
        "\n🛡️  To use these certificates:"
        "\n   1. Copy certs/ directory to deployment server"
        "\n   2. Set CERTFILE and KEYFILE env vars to server.crt/server.key"
        "\n   3. Use ca.crt for client certificate validation"
    )


if __name__ == "__main__":
    main()
