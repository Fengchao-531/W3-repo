import pytest
from source_relocation.defenses import (
    ActionDefense, DefenseSetupError, InputDefense, DEFENSES, trained_settings,
)


def test_six_real_adapter_names():
    assert DEFENSES == (
        "none", "sandwich", "struq", "secalign",
        "perplexity", "datasentinel", "causalarmor",
    )


def test_missing_trained_checkout_fails(monkeypatch):
    monkeypatch.delenv("W3_STRUQ_REPO", raising=False)
    with pytest.raises(DefenseSetupError):
        trained_settings("struq")


def test_sandwich_executes_after_untrusted_artifact():
    agentdojo = pytest.importorskip("agentdojo.types")
    text = agentdojo.text_content_block_from_string
    defense = InputDefense(
        "sandwich", original_task="Book the hotel",
        artifact_description="An online offer lists SAVE20.",
    )
    messages = [
        {"role": "system", "content": [text("Complete the task")]},
        {"role": "user", "content": [text("Book the hotel. An online offer lists SAVE20.")]},
        {"role": "tool", "content": [text("Offers found")], "tool_call_id": "one"},
    ]
    _, _, _, updated, _ = defense.query("Book", None, None, messages, {})
    assert updated[0] == messages[0]
    assert "Please always remember that your task is: Book the hotel" in updated[1]["content"][0]["content"]
    assert updated[2]["content"][0]["content"].endswith("Book the hotel")
    assert "Please always remember" not in messages[1]["content"][0]["content"]


def test_none_action_defense_is_identity():
    d = ActionDefense("none")
    messages = [{"role": "assistant", "tool_calls": None, "content": []}]
    result = d.query("task", None, None, messages, {})
    assert result[3] is messages


def test_datasentinel_filters_only_offer_and_tool(monkeypatch):
    agentdojo = pytest.importorskip("agentdojo.types")
    from source_relocation import defenses
    from types import SimpleNamespace

    class MockDetector:
        def __init__(self, config):
            self.config = config

        def detect(self, value):
            return int("SAVE20" in value or "injection" in value)

    monkeypatch.setenv("W3_DATASENTINEL_CONFIG", "example.json")
    monkeypatch.setenv("W3_DATASENTINEL_CHECKPOINT", "tuned")
    monkeypatch.setattr(defenses, "upstream_import",
                        lambda root, name: SimpleNamespace(
                            DataSentinelDetector=MockDetector,
                            open_config=lambda path: {"params": {}},
                        ))
    d = InputDefense(
        "datasentinel", original_task="Book the hotel",
        artifact_description="SAVE20 offer",
    )
    text = agentdojo.text_content_block_from_string
    messages = [
        {"role": "system", "content": [text("system")]},
        {"role": "user", "content": [text("Book the hotel. SAVE20 offer")]},
        {"role": "tool", "content": [text("injection attempt")]},
    ]
    output = d.query("", None, None, messages, {})[3]
    assert "Book the hotel." in output[1]["content"][0]["content"]
    assert "Offer removed by datasentinel" in output[1]["content"][0]["content"]
    assert "Tool observation removed by datasentinel" in output[2]["content"][0]["content"]
    assert len(d.events) == 2
