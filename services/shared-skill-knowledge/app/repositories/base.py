from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


class ConflictError(Exception):
    """Raised when a database write violates a uniqueness or constraint rule."""


async def commit_or_conflict(session: AsyncSession, *objs, refresh_targets=()):
    """Persist pending objects, mapping IntegrityError to ConflictError."""
    for obj in objs:
        session.add(obj)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ConflictError from exc
    except Exception:
        await session.rollback()
        raise

    for target in refresh_targets:
        await session.refresh(target)
    return objs[0] if len(objs) == 1 else objs


async def delete_and_commit(session: AsyncSession, obj) -> None:
    """Delete an ORM entity and commit, rolling back on failure."""
    try:
        await session.delete(obj)
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ConflictError from exc
    except Exception:
        await session.rollback()
        raise


async def generate_prefixed_sequence_id(
    session: AsyncSession, column, prefix: str, offset: int = 0
) -> str:
    """Compute the next zero-padded canonical ID (e.g. SK-000001, RL-000001)."""
    stmt = select(column).where(column.like(f"{prefix}%"))
    result = await session.execute(stmt)
    max_num = 0
    prefix_len = len(prefix)
    for existing_id in result.scalars().all():
        num_part = existing_id[prefix_len:]
        if num_part.isdigit():
            max_num = max(max_num, int(num_part))
    return f"{prefix}{max_num + 1 + offset:06d}"
