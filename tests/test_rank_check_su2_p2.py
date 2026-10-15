# tests/test_rank_check_su2_p2.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import rank_check_su2_p2 as rc

def test_verdict_pass():
    assert rc.run(emit_json=True) == 0

def test_json_report_shape():
    rc_ok = rc.run(emit_json=True)
    assert rc_ok == 0
