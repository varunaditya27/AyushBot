"""AyushBot Cloud — Smoke Test

Verifies that all required dependencies are installed and importable.
Run this to confirm the development environment is properly set up.

Usage:
    python smoke_test.py
"""

import sys
from importlib import import_module
from pathlib import Path
from typing import List, Tuple

# Add parent directory to path so cloud module can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_import(module_name: str) -> Tuple[bool, str]:
    """Test if a module can be imported.
    
    Args:
        module_name: Name of the module to import
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        import_module(module_name)
        return True, f"✓ {module_name}"
    except ImportError as e:
        return False, f"✗ {module_name}: {str(e)}"


def run_smoke_tests() -> bool:
    """Run all smoke tests.
    
    Returns:
        True if all tests pass, False otherwise
    """
    print("\n" + "=" * 70)
    print("  AyushBot Cloud — Smoke Test")
    print("=" * 70)
    
    # Core dependencies
    core_deps = [
        "flwr",
        "fastapi",
        "uvicorn",
        "pydantic",
        "sqlalchemy",
        "psycopg2",
        "streamlit",
        "plotly",
        "pandas",
        "numpy",
        "scipy",
        "xgboost",
        "cryptography",
        "jose",
        "yaml",
        "httpx",
        "structlog",
        "prometheus_client",
        "influxdb_client",
    ]
    
    # Local cloud modules
    local_modules = [
        "cloud",
        "cloud.fl_server",
        "cloud.analytics",
        "cloud.api",
        "cloud.auth",
        "cloud.infra",
        "cloud.config",
    ]
    
    all_passed = True
    
    print("\n📦 Checking Core Dependencies:")
    print("-" * 70)
    for dep in core_deps:
        success, message = test_import(dep)
        print(message)
        if not success:
            all_passed = False
    
    print("\n📂 Checking Local Cloud Modules:")
    print("-" * 70)
    for mod in local_modules:
        success, message = test_import(mod)
        print(message)
        if not success:
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("  ✓ All smoke tests PASSED")
        print("=" * 70)
        return True
    else:
        print("  ✗ Some smoke tests FAILED")
        print("=" * 70)
        return False


def main() -> int:
    """Main entry point."""
    if run_smoke_tests():
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
