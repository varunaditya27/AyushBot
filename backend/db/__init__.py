# =============================================================================
# AyushBot Backend — Database Package
# =============================================================================
#
# This package manages all persistent data storage on the PHC gateway using
# SQLite (via SQLAlchemy ORM). SQLite is chosen because:
#   - Zero-config, serverless — ideal for embedded deployment on RPi 4
#   - Single-file database — easy backup and recovery
#   - ACID transactions — data integrity for clinical records
# =============================================================================
