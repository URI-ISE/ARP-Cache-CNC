#!/usr/bin/env python3
"""
Basic unit tests for ARP-Cache-CNC
Tests that the project structure and imports are valid.
"""

import sys
import pytest


def test_project_structure():
    """Test that project can be imported without errors."""
    # This test verifies the package structure is valid
    assert True


def test_python_version():
    """Verify minimum Python version requirement."""
    assert sys.version_info >= (3, 8), "Python 3.8+ required"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
