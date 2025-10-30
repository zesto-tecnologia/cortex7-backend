"""Password hashing and verification using bcrypt."""

import bcrypt


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with cost factor 12.

    Args:
        password: Plain text password to hash

    Returns:
        Hashed password string suitable for database storage

    Example:
        >>> hashed = hash_password("MyP@ssw0rd!")
        >>> # Store hashed in database
    """
    # bcrypt requires bytes input
    password_bytes = password.encode('utf-8')

    # Generate salt and hash with cost factor 12
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)

    # Return as string for database storage
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.

    Args:
        plain_password: Plain text password from user input
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise

    Example:
        >>> is_valid = verify_password("MyP@ssw0rd!", stored_hash)
    """
    try:
        # bcrypt requires bytes input
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')

        # Verify password
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


def needs_rehash(hashed_password: str) -> bool:
    """
    Check if a password hash needs to be updated (e.g., due to deprecated scheme).

    For bcrypt, we check if cost factor is less than 12.

    Args:
        hashed_password: Hashed password from database

    Returns:
        True if password should be rehashed, False otherwise
    """
    try:
        # Extract cost factor from hash (format: $2b$12$...)
        parts = hashed_password.split('$')
        if len(parts) >= 3:
            current_cost = int(parts[2])
            return current_cost < 12
        return False
    except Exception:
        return False
