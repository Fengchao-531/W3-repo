import io
import tokenize
from pathlib import Path


def test_no_code_comments():
    root = Path(__file__).resolve().parents[1]
    folders = ("src", "reproduction", "plotting", "experiments", "analysis", "tests")
    for directory in folders:
        for path in (root / directory).rglob("*.py"):
            tokens = tokenize.tokenize(io.BytesIO(path.read_bytes()).readline)
            assert not any(token.type == tokenize.COMMENT for token in tokens), str(path)
