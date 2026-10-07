import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import exp2_pipeline

exp2_pipeline.statistics()
