from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from inspection_records_search import config
from inspection_records_search.infrastructure import repository_factory
from inspection_records_search.shared.errors import ConfigurationError
from pyinstaller_build import prepare_bundled_env
from dotenv import dotenv_values


class RuntimeProfileTests(unittest.TestCase):
    def test_postgres_starts_without_loading_access_dependencies(self) -> None:
        # Fresh interpreter: fail even if an excluded package happens to be installed.
        script = '''
import importlib.abc
import sys
from unittest.mock import MagicMock, patch
sys.path.insert(0, "src")
class BlockAccess(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in {"pyodbc", "pypyodbc", "win32com"} or fullname.endswith("access_gateway"):
            raise AssertionError("Access import attempted: " + fullname)
sys.meta_path.insert(0, BlockAccess())
from inspection_records_search import app
from inspection_records_search.infrastructure.postgres_repository import PostgresInspectionRepository
with patch("inspection_records_search.config.load_env"), patch.dict("os.environ", {
    "DB_BACKEND": "postgres", "POSTGRES_CONNECTION_URL": "postgresql://test"
}, clear=True):
    bridge = app._build_bridge()
    assert isinstance(bridge._svc._repository, PostgresInspectionRepository)
    assert bridge._bootstrap.startup_error is None
    with patch.object(app.webview, "create_window", return_value=MagicMock()) as create, patch.object(app.webview, "start") as start:
        assert app.main() == 0
        assert "検査員別照会" in create.call_args.kwargs["html"]
        assert start.call_args.kwargs["gui"] == "edgechromium"
'''
        result = subprocess.run([sys.executable, "-c", script], cwd=ROOT,
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_frozen_postgres_defaults_and_rejects_access(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "database_backend.txt").write_text("postgres", encoding="utf-8")
            with (patch.object(sys, "frozen", True, create=True),
                  patch.object(sys, "_MEIPASS", directory, create=True),
                  patch.object(config, "load_env"), patch.dict(os.environ, {}, clear=True)):
                self.assertEqual(config.get_database_backend(), "postgres")
                with patch.dict(os.environ, {"DB_BACKEND": "access"}):
                    self.assertFalse(config.validate_database_settings()[0])
                    with self.assertRaises(ConfigurationError):
                        repository_factory.create_inspection_repository()

    def test_missing_dsn_and_invalid_backend_do_not_fallback(self) -> None:
        with patch.object(config, "load_env"), patch.dict(os.environ, {}, clear=True):
            for backend in ("postgres", "invalid"):
                with self.subTest(backend=backend), patch.dict(os.environ, {"DB_BACKEND": backend}):
                    with self.assertRaises(ConfigurationError):
                        repository_factory.create_inspection_repository()

    def test_access_selection_still_creates_access_repository(self) -> None:
        # Use a fake optional module so this test also runs in a PostgreSQL-only venv.
        from types import ModuleType
        optional = ModuleType("inspection_records_search.infrastructure.access_gateway")
        from unittest.mock import Mock
        optional.AccessInspectionRepository = Mock()
        with (patch.object(config, "load_env"),
              patch.dict(os.environ, {"DB_BACKEND": "access", "ACCESS_DB_PATH": "test.accdb"}, clear=True),
              patch.object(repository_factory, "validate_access_db_path", return_value=(True, "")),
              patch.dict(sys.modules, {optional.__name__: optional})):
            repository_factory.create_inspection_repository()
            optional.AccessInspectionRepository.assert_called_once_with("test.accdb")

    def test_postgres_bundled_settings_keep_values_and_remove_access(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".env").write_text(
                "DB_BACKEND=access\nACCESS_DB_PATH=private.accdb\n"
                "BUILD_TEST_HOST=test\nPOSTGRES_CONNECTION_URL='postgresql://${BUILD_TEST_HOST}'\nEXPORT_DIR='C:\\output'\n"
                "DATABASE_BACKEND=access\n", encoding="utf-8")
            bundled = prepare_bundled_env(root, "postgres")
            values = dotenv_values(bundled)
            self.assertEqual(values["DB_BACKEND"], "postgres")
            self.assertEqual(values["POSTGRES_CONNECTION_URL"], "postgresql://test")
            self.assertEqual(values["EXPORT_DIR"], "C:\\output")
            self.assertNotIn("ACCESS_DB_PATH", values)
            self.assertNotIn("DATABASE_BACKEND", values)
            self.assertNotIn("BUILD_TEST_HOST", values)
            self.assertEqual(prepare_bundled_env(root, "access"), root / ".env")


if __name__ == "__main__":
    unittest.main()
