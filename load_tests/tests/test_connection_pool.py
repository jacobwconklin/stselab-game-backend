"""Exercise the actual SQLAlchemy pool against disposable SQLite connections."""
import ast
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import os
from pathlib import Path
import sys
from threading import Barrier, Lock
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine, event
from sqlalchemy.exc import TimeoutError
from sqlalchemy.pool import QueuePool


BACKEND=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("pool_under_test",BACKEND/"database.py")
database=importlib.util.module_from_spec(spec)
spec.loader.exec_module(database)


class ConnectionPoolTests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine("sqlite://",poolclass=QueuePool,pool_size=2,
                                  max_overflow=0,pool_timeout=.08,pool_pre_ping=True,
                                  connect_args={"check_same_thread":False})
        database._engine=None
        database._engine_lock=Lock()
        self.factory=patch.object(database,"_create_game_engine",return_value=self.engine)
        self.create=self.factory.start()

    def tearDown(self):
        self.factory.stop()
        self.engine.dispose()
        database._engine=None

    def test_reuses_physical_connection_and_close_returns_it(self):
        opened=[]
        event.listen(self.engine,"connect",lambda dbapi,record:opened.append(dbapi))
        for _ in range(100):
            db=database.get_game_connection()
            self.assertIs(db.driver_connection,opened[0])
            db.close()
        self.assertEqual(len(opened),1)
        self.assertEqual(self.engine.pool.checkedout(),0)
        self.assertEqual(self.create.call_count,1)

    def test_exhaustion_is_bounded_then_recovers_after_return(self):
        first=database.get_game_connection()
        second=database.get_game_connection()
        try:
            started=time.monotonic()
            with self.assertRaises(TimeoutError):
                database.get_game_connection()
            self.assertGreaterEqual(time.monotonic()-started,.05)
            self.assertEqual(self.engine.pool.checkedout(),2)
            first.close()
            replacement=database.get_game_connection()
            replacement.close()
        finally:
            first.close()
            second.close()

    def test_connections_are_exclusive_between_threads(self):
        barrier=Barrier(2)
        def borrow():
            db=database.get_game_connection()
            try:
                identity=id(db.driver_connection)
                barrier.wait(timeout=2)
                return identity
            finally:
                db.close()
        with ThreadPoolExecutor(max_workers=2) as executor:
            results=list(executor.map(lambda _:borrow(),range(2)))
        self.assertNotEqual(results[0],results[1])
        self.assertEqual(self.create.call_count,1)
        self.assertEqual(self.engine.pool.checkedout(),0)

    def test_return_rolls_back_uncommitted_data_and_preserves_commits(self):
        db=database.get_game_connection()
        cursor=db.cursor()
        cursor.execute("CREATE TABLE entries (value INTEGER)")
        db.commit()
        cursor.execute("INSERT INTO entries VALUES (1)")
        cursor.close()
        db.close()  # Must roll back this unfinished insert.
        db=database.get_game_connection()
        cursor=db.cursor()
        cursor.execute("SELECT * FROM entries")
        self.assertEqual(cursor.fetchall(),[])
        cursor.execute("INSERT INTO entries VALUES (2)")
        db.commit()
        cursor.close()
        db.close()
        db=database.get_game_connection()
        cursor=db.cursor()
        cursor.execute("SELECT * FROM entries")
        self.assertEqual(cursor.fetchall(),[(2,)])
        cursor.close()
        db.close()

    def test_broken_idle_connection_is_replaced(self):
        db=database.get_game_connection()
        physical=db.driver_connection
        db.close()
        physical.close()  # Simulate the server dropping an idle connection.
        replacement=database.get_game_connection()
        self.assertIsNot(replacement.driver_connection,physical)
        replacement.close()

    def test_fork_reset_uses_new_pool_without_closing_parent_connections(self):
        db=database.get_game_connection()
        physical=db.driver_connection
        db.close()
        original=self.engine.pool
        database._reset_after_fork()
        self.assertIsNot(self.engine.pool,original)
        physical.execute("SELECT 1")  # Parent's connection remains valid.
        physical.close()

    def test_all_game_handlers_return_connections_even_if_cursor_cleanup_fails(self):
        closed=[]
        class Cursor:
            def execute(self,*args):pass
            def fetchone(self):return None
            def fetchall(self):return []
            def close(self):raise RuntimeError("Injected cursor-close failure")
        class Connection:
            def cursor(self,*args):return Cursor()
            def close(self):closed.append(True)
        namespace={"get_game_connection":Connection,"request":SimpleNamespace(json={}),
                   "jsonify":lambda data:data,
                   "pymysql":SimpleNamespace(cursors=SimpleNamespace(DictCursor=object))}
        for name in ("users.py","session.py"):
            tree=ast.parse((BACKEND/name).read_text(encoding="utf-8"))
            functions=[node for node in tree.body if isinstance(node,ast.FunctionDef)]
            exec(compile(ast.Module(body=functions,type_ignores=[]),name,"exec"),namespace)
            for node in functions:
                if node.name.startswith("_"):continue
                with self.subTest(handler=node.name),patch("builtins.print"):
                    before=len(closed)
                    try:namespace[node.name]()
                    except RuntimeError as exc:
                        self.assertEqual(str(exc),"Injected cursor-close failure")
                    self.assertEqual(len(closed),before+1)


class PoolConfigurationTests(unittest.TestCase):
    def test_mysql_engine_settings_and_reserved_password_characters(self):
        secrets=SimpleNamespace(VT_MYSQL_HOST="127.0.0.1",VT_MYSQL_PORT=3306,
            VT_MYSQL_USER="test",VT_MYSQL_PASSWORD="p@ss:/#word",VT_MYSQL_STSELAB_DB="test")
        with patch.dict(sys.modules,{"environmentSecrets":secrets}),patch.dict(os.environ,{},clear=True),\
             patch.object(database,"create_engine") as create:
            database._create_game_engine()
        url=create.call_args.args[0]
        options=create.call_args.kwargs
        self.assertEqual(url.drivername,"mysql+pymysql")
        self.assertEqual(url.password,secrets.VT_MYSQL_PASSWORD)
        self.assertEqual(options["pool_size"],16)
        self.assertEqual(options["max_overflow"],0)
        self.assertEqual(options["pool_timeout"],5)
        self.assertTrue(options["pool_pre_ping"])
        self.assertEqual(options["pool_reset_on_return"],"rollback")

    def test_invalid_pool_limits_fail_before_creating_an_engine(self):
        secrets=SimpleNamespace(VT_MYSQL_HOST="127.0.0.1",VT_MYSQL_PORT=3306,
            VT_MYSQL_USER="test",VT_MYSQL_PASSWORD="test",VT_MYSQL_STSELAB_DB="test")
        for key,value in (("STSE_DB_POOL_SIZE","0"),("STSE_DB_POOL_TIMEOUT","nan"),
                          ("STSE_DB_POOL_TIMEOUT","-1"),("STSE_DB_POOL_RECYCLE","0")):
            with self.subTest(setting=key),patch.dict(sys.modules,{"environmentSecrets":secrets}),\
                 patch.dict(os.environ,{key:value},clear=True),patch.object(database,"create_engine") as create:
                with self.assertRaises(ValueError):database._create_game_engine()
                create.assert_not_called()


if __name__=="__main__":
    unittest.main(verbosity=2)
