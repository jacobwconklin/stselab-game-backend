"""Bounded, per-process game database connections; existing handlers keep raw SQL."""
import os
from threading import Lock

from sqlalchemy import URL, create_engine


_engine = None
_engine_lock = Lock()


def _create_game_engine():
    # Lazy import keeps connection creation out of startup and permits isolated tests.
    from environmentSecrets import (
        VT_MYSQL_HOST, VT_MYSQL_USER, VT_MYSQL_PASSWORD,
        VT_MYSQL_STSELAB_DB, VT_MYSQL_PORT,
    )

    size = int(os.environ.get("STSE_DB_POOL_SIZE", "16"))
    timeout = float(os.environ.get("STSE_DB_POOL_TIMEOUT", "5"))
    recycle = int(os.environ.get("STSE_DB_POOL_RECYCLE", "1800"))
    if size < 1 or not 0 < timeout < float("inf") or recycle < 1:
        raise ValueError("Pool size/recycle must be positive integers and timeout finite and positive")
    return create_engine(
        URL.create("mysql+pymysql", username=VT_MYSQL_USER, password=VT_MYSQL_PASSWORD,
                   host=VT_MYSQL_HOST, port=int(VT_MYSQL_PORT), database=VT_MYSQL_STSELAB_DB),
        pool_size=size, max_overflow=0, pool_timeout=timeout,
        pool_pre_ping=True, pool_recycle=recycle, pool_reset_on_return="rollback",
    )


def get_game_connection():
    """Borrow an exclusive DBAPI connection; close() returns it to the pool."""
    global _engine
    with _engine_lock:
        if _engine is None:
            _engine = _create_game_engine()
        engine = _engine
    return engine.raw_connection()


def _reset_after_fork():
    # Child workers must not reuse parent sockets or an inherited locked mutex.
    global _engine_lock
    _engine_lock = Lock()
    if _engine is not None:
        _engine.dispose(close=False)


if hasattr(os, "register_at_fork"):
    os.register_at_fork(after_in_child=_reset_after_fork)
