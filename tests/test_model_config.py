"""harness/model_config.py: scoped, self-restoring models.json edits."""

import json

import pytest

from harness.model_config import ModelConfigError, bumped_max_tokens

FIXTURE = {
    "providers": {
        "omlx": {
            "baseUrl": "http://127.0.0.1:8001/v1",
            "models": [
                {"id": "gemma-4-12B-it-MLX-8bit", "maxTokens": 8192},
                {"id": "Qwen3.6-27B-8bit", "maxTokens": 32768},
            ],
        }
    }
}


@pytest.fixture
def models_json(tmp_path):
    path = tmp_path / "models.json"
    path.write_text(json.dumps(FIXTURE, indent=2) + "\n")
    return path


def test_bumps_for_the_block_and_restores_after(models_json):
    with bumped_max_tokens("gemma-4-12B-it-MLX-8bit", 32768, models_json):
        bumped = json.loads(models_json.read_text())
        assert bumped["providers"]["omlx"]["models"][0]["maxTokens"] == 32768
        # The untouched model entry is unaffected.
        assert bumped["providers"]["omlx"]["models"][1]["maxTokens"] == 32768

    restored = json.loads(models_json.read_text())
    assert restored["providers"]["omlx"]["models"][0]["maxTokens"] == 8192


def test_restores_the_exact_original_bytes_not_a_reformatted_equivalent(models_json):
    original_bytes = models_json.read_text()
    with bumped_max_tokens("gemma-4-12B-it-MLX-8bit", 32768, models_json):
        pass
    assert models_json.read_text() == original_bytes


def test_restores_even_when_the_caller_raises(models_json):
    with pytest.raises(RuntimeError), bumped_max_tokens("gemma-4-12B-it-MLX-8bit", 32768, models_json):
        raise RuntimeError("boom")

    restored = json.loads(models_json.read_text())
    assert restored["providers"]["omlx"]["models"][0]["maxTokens"] == 8192


def test_a_no_op_bump_does_not_touch_the_file(models_json):
    original_bytes = models_json.read_text()
    with bumped_max_tokens("Qwen3.6-27B-8bit", 32768, models_json):
        # Already 32768 -- must not rewrite (and must not restore-clobber
        # anything either, since nothing changed).
        assert models_json.read_text() == original_bytes
    assert models_json.read_text() == original_bytes


def test_refuses_an_unknown_model(models_json):
    with pytest.raises(ModelConfigError), bumped_max_tokens("does-not-exist", 32768, models_json):
        pass


def test_nested_bumps_of_different_models_both_restore(models_json):
    with bumped_max_tokens("gemma-4-12B-it-MLX-8bit", 16384, models_json):
        with bumped_max_tokens("Qwen3.6-27B-8bit", 8192, models_json):
            data = json.loads(models_json.read_text())
            assert data["providers"]["omlx"]["models"][0]["maxTokens"] == 16384
            assert data["providers"]["omlx"]["models"][1]["maxTokens"] == 8192
        # Inner restore must not have clobbered the outer bump.
        data = json.loads(models_json.read_text())
        assert data["providers"]["omlx"]["models"][0]["maxTokens"] == 16384
        assert data["providers"]["omlx"]["models"][1]["maxTokens"] == 32768

    data = json.loads(models_json.read_text())
    assert data["providers"]["omlx"]["models"][0]["maxTokens"] == 8192
    assert data["providers"]["omlx"]["models"][1]["maxTokens"] == 32768
