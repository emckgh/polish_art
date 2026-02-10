"""UUID utility functions."""

from src.constants import UUIDConstants


def format_uuid_with_hyphens(uuid_str: str) -> str:
    """
    Convert UUID string without hyphens to standard format with hyphens.
    
    Args:
        uuid_str: UUID string (with or without hyphens)
        
    Returns:
        UUID string in standard format (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
    """
    # Remove any existing hyphens
    clean_uuid = uuid_str.replace('-', '')
    
    # If not 32 characters, return as-is
    if len(clean_uuid) != UUIDConstants.UUID_LENGTH_WITHOUT_HYPHENS:
        return uuid_str
    
    # Insert hyphens at proper positions
    return (
        f"{clean_uuid[:UUIDConstants.HYPHEN_POSITION_1]}-"
        f"{clean_uuid[UUIDConstants.HYPHEN_POSITION_1:UUIDConstants.HYPHEN_POSITION_2]}-"
        f"{clean_uuid[UUIDConstants.HYPHEN_POSITION_2:UUIDConstants.HYPHEN_POSITION_3]}-"
        f"{clean_uuid[UUIDConstants.HYPHEN_POSITION_3:UUIDConstants.HYPHEN_POSITION_4]}-"
        f"{clean_uuid[UUIDConstants.HYPHEN_POSITION_4:]}"
    )


def remove_uuid_hyphens(uuid_str: str) -> str:
    """
    Remove hyphens from UUID string.
    
    Args:
        uuid_str: UUID string in any format
        
    Returns:
        UUID string without hyphens
    """
    return uuid_str.replace('-', '')
