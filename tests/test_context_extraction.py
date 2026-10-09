from pathlib import Path
import json
from reproduction.build_contexts import before_action


def test_stops_before_offer_application(tmp_path):
    path = tmp_path / "t.json"
    messages = [{"role": "user", "content": "SAVE20"}, {"role": "tool", "content": "The online offer links SAVE20 to https://lemarais-offers.example/book"}, {"role": "assistant", "tool_calls": [{"function": "apply_offer", "args": {"offer_id": "x"}}]}, {"role": "tool", "content": "applied"}]
    path.write_text(json.dumps(messages), encoding="utf-8")
    text = before_action(path)
    assert "applied" not in text
    assert "lemarais-offers" in text
