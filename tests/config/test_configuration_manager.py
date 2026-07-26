"""Unit tests for the Configuration Manager (WP-02).

Covers docs/910_Phase1_Core_Foundation_Specification.md#configuration-manager
and docs/920_Phase1_Work_Breakdown.md#wp-02--configuration-manager.
"""

from __future__ import annotations

import json

import pytest

from paios.config import (
    ConfigKeySchema,
    ConfigurationError,
    ConfigurationManager,
    UnknownConfigKeyError,
    env_var_name,
)


def make_manager(schema=None) -> ConfigurationManager:
    if schema is None:
        schema = {
            "kernel.bootTimeoutMs": ConfigKeySchema(value_type=int, required=False, default=30000),
            "storage.local.path": ConfigKeySchema(value_type=str, required=True),
        }
    return ConfigurationManager(schema)


class TestNotLoadedState:
    def test_is_loaded_false_before_load(self) -> None:
        manager = make_manager()
        assert manager.is_loaded() is False

    def test_get_returns_provided_default_before_load(self) -> None:
        manager = make_manager()
        assert manager.get("kernel.bootTimeoutMs", 999) == 999

    def test_get_required_raises_configuration_error_before_load(self) -> None:
        manager = make_manager()
        with pytest.raises(ConfigurationError):
            manager.get_required("storage.local.path")


class TestDefaults:
    def test_optional_key_uses_schema_default_when_absent(self) -> None:
        schema = {
            "kernel.bootTimeoutMs": ConfigKeySchema(value_type=int, required=False, default=30000),
        }
        manager = ConfigurationManager(schema)
        manager.load(env={})
        assert manager.is_loaded() is True
        assert manager.get("kernel.bootTimeoutMs") == 30000
        assert manager.get_required("kernel.bootTimeoutMs") == 30000

    def test_required_key_missing_from_all_sources_raises_configuration_error(self) -> None:
        schema = {
            "storage.local.path": ConfigKeySchema(value_type=str, required=True),
        }
        manager = ConfigurationManager(schema)
        with pytest.raises(ConfigurationError) as exc_info:
            manager.load(env={})
        assert exc_info.value.key == "storage.local.path"
        assert manager.is_loaded() is False


class TestFileSource:
    def test_file_value_overrides_default(self, tmp_path) -> None:
        config_file = tmp_path / "paios.config.json"
        config_file.write_text(json.dumps({"kernel.bootTimeoutMs": 5000}))
        schema = {
            "kernel.bootTimeoutMs": ConfigKeySchema(value_type=int, required=False, default=30000),
        }
        manager = ConfigurationManager(schema)
        manager.load(file_path=config_file, env={})
        assert manager.get("kernel.bootTimeoutMs") == 5000

    def test_missing_explicit_file_path_raises_configuration_error(self, tmp_path) -> None:
        schema = {
            "kernel.bootTimeoutMs": ConfigKeySchema(value_type=int, required=False, default=30000),
        }
        manager = ConfigurationManager(schema)
        with pytest.raises(ConfigurationError):
            manager.load(file_path=tmp_path / "does-not-exist.json", env={})

    def test_file_value_of_wrong_type_raises_configuration_error(self, tmp_path) -> None:
        config_file = tmp_path / "paios.config.json"
        config_file.write_text(json.dumps({"kernel.bootTimeoutMs": "not-a-number"}))
        schema = {
            "kernel.bootTimeoutMs": ConfigKeySchema(value_type=int, required=False, default=30000),
        }
        manager = ConfigurationManager(schema)
        with pytest.raises(ConfigurationError):
            manager.load(file_path=config_file, env={})

    def test_invalid_json_file_raises_configuration_error(self, tmp_path) -> None:
        config_file = tmp_path / "paios.config.json"
        config_file.write_text("{not valid json")
        schema = {
            "kernel.bootTimeoutMs": ConfigKeySchema(value_type=int, required=False, default=30000),
        }
        manager = ConfigurationManager(schema)
        with pytest.raises(ConfigurationError):
            manager.load(file_path=config_file, env={})


class TestEnvironmentSource:
    def test_env_var_name_maps_dotted_key(self) -> None:
        assert env_var_name("storage.local.path") == "PAIOS_STORAGE__LOCAL__PATH"

    def test_env_value_overrides_default(self) -> None:
        schema = {
            "kernel.bootTimeoutMs": ConfigKeySchema(value_type=int, required=False, default=30000),
        }
        manager = ConfigurationManager(schema)
        manager.load(env={"PAIOS_KERNEL__BOOTTIMEOUTMS": "12345"})
        assert manager.get("kernel.bootTimeoutMs") == 12345

    def test_env_bool_casting(self) -> None:
        schema = {
            "logging.enabled": ConfigKeySchema(value_type=bool, required=False, default=True),
        }
        manager = ConfigurationManager(schema)
        manager.load(env={"PAIOS_LOGGING__ENABLED": "false"})
        assert manager.get("logging.enabled") is False

    def test_env_invalid_int_raises_configuration_error(self) -> None:
        schema = {
            "kernel.bootTimeoutMs": ConfigKeySchema(value_type=int, required=False, default=30000),
        }
        manager = ConfigurationManager(schema)
        with pytest.raises(ConfigurationError):
            manager.load(env={"PAIOS_KERNEL__BOOTTIMEOUTMS": "not-an-int"})


class TestPrecedence:
    def test_environment_overrides_file_overrides_default(self, tmp_path) -> None:
        config_file = tmp_path / "paios.config.json"
        config_file.write_text(json.dumps({"kernel.bootTimeoutMs": 5000}))
        schema = {
            "kernel.bootTimeoutMs": ConfigKeySchema(value_type=int, required=False, default=30000),
        }

        default_only = ConfigurationManager(schema)
        default_only.load(env={})
        assert default_only.get("kernel.bootTimeoutMs") == 30000

        file_over_default = ConfigurationManager(schema)
        file_over_default.load(file_path=config_file, env={})
        assert file_over_default.get("kernel.bootTimeoutMs") == 5000

        env_over_file = ConfigurationManager(schema)
        env_over_file.load(file_path=config_file, env={"PAIOS_KERNEL__BOOTTIMEOUTMS": "1000"})
        assert env_over_file.get("kernel.bootTimeoutMs") == 1000


class TestUnknownKey:
    def test_get_unknown_key_raises(self) -> None:
        manager = make_manager()
        with pytest.raises(UnknownConfigKeyError):
            manager.get("does.not.exist")

    def test_get_required_unknown_key_raises(self) -> None:
        manager = make_manager()
        with pytest.raises(UnknownConfigKeyError):
            manager.get_required("does.not.exist")


class TestSchemaConstruction:
    def test_unsupported_value_type_rejected(self) -> None:
        with pytest.raises(ValueError):
            ConfigurationManager({"bad.key": ConfigKeySchema(value_type=list)})


class TestIsolation:
    def test_two_managers_do_not_share_state(self) -> None:
        schema = {
            "kernel.bootTimeoutMs": ConfigKeySchema(value_type=int, required=False, default=30000),
        }
        manager_a = ConfigurationManager(schema)
        manager_b = ConfigurationManager(schema)
        manager_a.load(env={"PAIOS_KERNEL__BOOTTIMEOUTMS": "1"})
        manager_b.load(env={})
        assert manager_a.get("kernel.bootTimeoutMs") == 1
        assert manager_b.get("kernel.bootTimeoutMs") == 30000
