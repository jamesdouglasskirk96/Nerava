"""
Nova facade layer for wallet currency conversion.

Nova is a user-facing currency concept that wraps the internal cents-based storage.
Currently 1:1 with cents, but conversion is isolated to allow future changes.
"""


def cents_to_nova(cents: int) -> int:
    """
    Convert cents to Nova.
    
    Args:
        cents: Amount in cents (integer)
    
    Returns:
        Amount in Nova (integer)
    
    Note:
        Currently 1:1 conversion. This can be changed in the future
        without affecting database schema or business logic.
    """
    return cents


def nova_to_cents(nova: int) -> int:
    """
    Convert Nova to cents.
    
    Args:
        nova: Amount in Nova (integer)
    
    Returns:
        Amount in cents (integer)
    
    Note:
        Currently 1:1 conversion. This can be changed in the future
        without affecting database schema or business logic.
    """
    return nova

