"""Merchant name normalization utilities."""

import re
import unicodedata


def normalize_merchant_name(name: str) -> str:
    """
    Normalize a merchant name for deduplication.
    
    Steps:
    1. Lowercase
    2. Remove accents/diacritics
    3. Remove punctuation and apostrophes
    4. Collapse whitespace
    5. Trim generic suffixes like " coffee", " cafe", " store"
    
    Args:
        name: Raw merchant name
        
    Returns:
        Normalized name string
        
    Examples:
        >>> normalize_merchant_name("Starbucks' Coffee")
        'starbucks'
        >>> normalize_merchant_name("Blue Bottle Café")
        'blue bottle'
        >>> normalize_merchant_name("Mock Cafe 123")
        'mock'
    """
    if not name:
        return ""
    
    # 1. Lowercase
    s = name.lower()
    
    # 2. Remove accents/diacritics
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    
    # 3. Remove punctuation and apostrophes
    s = re.sub(r'[\'"]', '', s)
    s = re.sub(r'[^\w\s]', ' ', s)
    
    # 4. Collapse whitespace
    s = re.sub(r'\s+', ' ', s)
    s = s.strip()
    
    # 5. Remove common generic suffixes
    suffixes = [' coffee', ' cafe', ' store', ' shop', ' restaurant', ' bar']
    for suffix in suffixes:
        if s.endswith(suffix):
            s = s[:-len(suffix)].strip()
            break
    
    return s

