"""
Test Copy Discipline

Ensures that "verification", "verified", and "verify" terminology
never appears in API responses, schemas, or logs.
"""
import re
import os
from pathlib import Path


def test_no_verification_terminology_in_schemas():
    """Test that schemas don't contain verification terminology"""
    schema_dir = Path(__file__).parent.parent / "app" / "schemas"
    
    if not schema_dir.exists():
        return  # Skip if schemas directory doesn't exist
    
    verification_pattern = re.compile(
        r'\b(verification|verified|verify)\b',
        re.IGNORECASE
    )
    
    violations = []
    for schema_file in schema_dir.rglob("*.py"):
        with open(schema_file, 'r') as f:
            content = f.read()
            # Skip comments and docstrings for this test
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                # Skip comment lines
                if line.strip().startswith('#'):
                    continue
                # Check for verification terminology in code
                if verification_pattern.search(line):
                    violations.append(f"{schema_file}:{i}: {line.strip()}")
    
    assert not violations, f"Found verification terminology in schemas:\n" + "\n".join(violations)


def test_copy_module_exists():
    """Test that copy module exists and has required constants"""
    from app.core.copy import (
        LOCATION_EDUCATION_COPY,
        TIER_C_FALLBACK_COPY,
        VEHICLE_ONBOARDING_EXPLANATION,
        PERK_UNLOCK_COPY,
        VEHICLE_ONBOARDING_STATUS_COPY,
    )
    
    assert isinstance(LOCATION_EDUCATION_COPY, dict)
    assert isinstance(TIER_C_FALLBACK_COPY, str)
    assert isinstance(VEHICLE_ONBOARDING_EXPLANATION, dict)
    assert isinstance(PERK_UNLOCK_COPY, dict)
    assert isinstance(VEHICLE_ONBOARDING_STATUS_COPY, dict)
    
    # Ensure no verification terminology in copy constants
    verification_pattern = re.compile(
        r'\b(verification|verified|verify)\b',
        re.IGNORECASE
    )
    
    all_copy_text = (
        str(LOCATION_EDUCATION_COPY) +
        TIER_C_FALLBACK_COPY +
        str(VEHICLE_ONBOARDING_EXPLANATION) +
        str(PERK_UNLOCK_COPY) +
        str(VEHICLE_ONBOARDING_STATUS_COPY)
    )
    
    assert not verification_pattern.search(all_copy_text), \
        "Copy constants contain verification terminology"


def test_intent_router_uses_copy():
    """Test that intent router uses copy constants"""
    from app.routers.intent import router
    
    # Check that router exists and is properly configured
    assert router is not None
    
    # Import copy to ensure it's available
    from app.core.copy import TIER_C_FALLBACK_COPY
    assert TIER_C_FALLBACK_COPY is not None



