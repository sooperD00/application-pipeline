"""
Password hashing (argon2id) and user authentication.

argon2id is the OWASP recommendation since 2019 — memory-hard, so GPU
farms can't parallelize cracking cheaply (ADR-011). The argon2-cffi
library handles salt generation, parameter tuning, and hash format
internally. We just call hash() and verify().
"""

import re
import uuid

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.config import settings
from app.models.enums import ProviderStatus, ProviderType, UserRole
from app.models.provider import Provider
from app.models.user import User

ph = PasswordHasher()


# ── Password helpers ──────────────────────────────────────────────


def hash_password(password: str) -> str:
    """Hash a plaintext password with argon2id."""
    return ph.hash(password)


def verify_password(password: str, hash: str) -> bool:
    """Check a plaintext password against an argon2id hash.

    Returns False on mismatch (no exception propagation).
    """
    try:
        return ph.verify(hash, password)
    except VerifyMismatchError:
        return False


# length is the single biggest factor in password strength per NIST guidelines.
# Complexity rules (mixed case, digits) can be layered on if policy requires.
def validate_password(password: str) -> None:
    """Raise ValueError if password doesn't meet minimum requirements."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")

# ── User lookups ──────────────────────────────────────────────────


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Case-insensitive email lookup."""
    result = await db.execute(select(User).where(User.email == email.lower()))
    return result.scalars().first()

# ── Registration ──────────────────────────────────────────────────

# TODO: One registration function per role that has its own companion table.
# register_provider lives here. If we add facility managers, ODHA staff, etc.
# (ADR-009), write register_facility_manager / register_staff here — don't
# generalize this function. Each role has different required fields.

async def register_provider(
    db: AsyncSession,
    email: str,
    password: str,
    display_name: str,
    provider_type: ProviderType,
) -> tuple[User, Provider]:
    """Create User (role=PROVIDER) + Provider in one transaction.

    Auto-login happens at the route layer (session creation + cookies).
    Status is PENDING unless AUTO_APPROVE is set (conference mode).

    Returns (user, provider). Caller commits.
    Raises ValueError if email already taken.
    """
    validate_password(password)

    existing = await get_user_by_email(db, email)
    if existing:
        raise ValueError("Email already registered")

    user = User(
        id=uuid.uuid4(),
        email=email.lower(),
        password_hash=hash_password(password),
        role=UserRole.PROVIDER,
    )
    db.add(user)
    await db.flush()

    slug = _make_slug(display_name)
    status = (
        ProviderStatus.APPROVED if settings.auto_approve else ProviderStatus.PENDING
    )

    provider = Provider(
        id=uuid.uuid4(),
        user_id=user.id,
        display_name=display_name,
        slug=slug,
        provider_type=provider_type,
        status=status,
        auto_approved=settings.auto_approve,
    )
    db.add(provider)
    await db.flush()

    return user, provider


# ── Authentication ────────────────────────────────────────────────


async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> User | None:
    """Verify email + password. Returns User if valid, None otherwise.

    Spends time hashing a dummy password on user-not-found so response
    time doesn't reveal whether the email exists. Not critical at FindMyHygienist's
    scale, but it's free.
    """
    user = await get_user_by_email(db, email)
    if user is None:
        ph.hash("timing-dummy")
        return None
    if not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


# ── Slug ──────────────────────────────────────────────────────────


def _make_slug(display_name: str) -> str:
    """'Ginger Davidson' → 'ginger-davidson-a1b2c3'.

    Appends a 6-char hex suffix from uuid4 to guarantee uniqueness
    without a DB round-trip. The URL already has the provider UUID
    (/providers/{slug}/{id}), so the slug is for readability/SEO,
    not for lookup.
    """
    base = re.sub(r"[^a-z0-9]+", "-", display_name.lower()).strip("-")
    suffix = uuid.uuid4().hex[:6]
    return f"{base}-{suffix}"
