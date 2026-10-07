import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import rq2_exp2_pipeline

rq2_exp2_pipeline.build_dataset()
