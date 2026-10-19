"""Evals for the hhmi skill. Synthetic fixtures only (written to tmp_path);
no real FlyEM data is read here."""
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from hhmi_scripts import check_hhmi, csv_to_xml

ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDER = ROOT / "assets" / "HHMIJaneliaMap.xml"

NEURONS = """bodyId,type,instance
100,KC,KC_a
200,MBON,MBON01
300,PN,PN_x
400,,
"""
# totals: 100: 10+5+1=16; 200: 10+7=17; 300: 5+7+2=14; 400: 1+2=3
EDGES = """bodyId_pre,bodyId_post,weight
100,200,10
100,300,5
300,200,7
400,100,1
300,400,2
999,100,50
"""


def write_fixture(d: Path, neurons=NEURONS, edges=EDGES) -> Path:
    (d / csv_to_xml.NEURONS_CSV).write_text(neurons, encoding="utf-8")
    (d / csv_to_xml.EDGES_CSV).write_text(edges, encoding="utf-8")
    return d


def parse(p: Path):
    r = ET.parse(p).getroot()
    ids = [n.get("id") for n in r.iter("neuron")]
    cons = {(c.get("from"), c.get("to")): c.get("weight") for c in r.iter("connection")}
    return r, ids, cons


def test_placeholder_is_valid_three_ring():
    errs, s = check_hhmi.check(PLACEHOLDER)
    assert errs == []
    assert (s["neurons"], s["connections"], s["self_loops"]) == (3, 3, 0)
    assert "NOT HHMI Janelia FlyEM" in PLACEHOLDER.read_text()


def test_full_conversion_roundtrips_through_checker(tmp_path):
    src = write_fixture(tmp_path)
    out = tmp_path / "out.xml"
    stats = csv_to_xml.convert(src, out)
    root, ids, cons = parse(out)
    assert root.tag == "hemibrain"
    assert ids == ["100", "200", "300", "400"]  # CSV order without --limit
    assert len(cons) == 5 and cons[("100", "200")] == "10"
    assert stats["edges_unknown"] == 1  # 999 is not a traced neuron
    assert all(c.get("delayMs") is None for c in root.iter("connection"))
    assert check_hhmi.check(out)[0] == []


def test_min_weight_threshold(tmp_path):
    out = tmp_path / "o.xml"
    s = csv_to_xml.convert(write_fixture(tmp_path), out, min_weight=5)
    _, ids, cons = parse(out)
    assert set(cons) == {("100", "200"), ("100", "300"), ("300", "200")}
    assert s["edges_below_min"] == 2 and len(ids) == 4


def test_limit_keeps_top_n_by_total_weight_and_internal_edges(tmp_path):
    out = tmp_path / "o.xml"
    s = csv_to_xml.convert(write_fixture(tmp_path), out, limit=2)
    _, ids, cons = parse(out)
    assert ids == ["200", "100"]  # 17, 16
    assert cons == {("100", "200"): "10"}
    assert (s["neurons_out"], s["edges_out"]) == (2, 1)
    assert check_hhmi.check(out)[0] == []


def test_limit_larger_than_population(tmp_path):
    out = tmp_path / "o.xml"
    csv_to_xml.convert(write_fixture(tmp_path), out, limit=50)
    _, ids, cons = parse(out)
    assert ids == ["200", "100", "300", "400"] and len(cons) == 5


def test_limit_and_min_weight_combine(tmp_path):
    out = tmp_path / "o.xml"
    csv_to_xml.convert(write_fixture(tmp_path), out, min_weight=5, limit=3)
    _, ids, cons = parse(out)
    # after threshold: 200=17, 100=15, 300=12, 400=0
    assert ids == ["200", "100", "300"] and len(cons) == 3


def test_ids_are_xml_escaped(tmp_path):
    neurons = 'bodyId,type,instance\n"a&b",x,y\n"<q\'"">",x,y\n'
    edges = 'bodyId_pre,bodyId_post,weight\n"a&b","<q\'"">",3\n'
    out = tmp_path / "o.xml"
    csv_to_xml.convert(write_fixture(tmp_path, neurons, edges), out)
    raw = out.read_text()
    assert "a&amp;b" in raw and "&lt;q" in raw and "a&b" not in raw
    _, ids, cons = parse(out)
    assert ids == ["a&b", "<q'\">"]
    assert cons == {("a&b", "<q'\">"): "3"}
    assert check_hhmi.check(out)[0] == []


def test_duplicate_csv_pairs_are_summed_not_duplicated(tmp_path):
    edges = "bodyId_pre,bodyId_post,weight\n100,200,4\n100,200,6\n"
    out = tmp_path / "o.xml"
    csv_to_xml.convert(write_fixture(tmp_path, edges=edges), out)
    _, _, cons = parse(out)
    assert cons == {("100", "200"): "10"}
    assert check_hhmi.check(out)[0] == []


def test_cli_exit_codes(tmp_path):
    src = write_fixture(tmp_path)
    out = tmp_path / "cli.xml"
    r = subprocess.run([sys.executable, "-P", str(ROOT / "hhmi_scripts" / "csv_to_xml.py"),
                        str(src), "-o", str(out), "--limit", "3"],
                       capture_output=True, text=True)
    assert r.returncode == 0 and "neurons_out=3" in r.stderr
    r = subprocess.run([sys.executable, "-P", str(ROOT / "hhmi_scripts" / "check_hhmi.py"), str(out)],
                       capture_output=True, text=True)
    assert r.returncode == 0 and "[+] OK" in r.stdout and "neurons=3" in r.stdout
    r = subprocess.run([sys.executable, "-P", str(ROOT / "hhmi_scripts" / "csv_to_xml.py"),
                        str(tmp_path / "missing")], capture_output=True, text=True)
    assert r.returncode == 1


BAD = {
    "wrong_root": '<graph><neuron id="A"/></graph>',
    "doctype": '<!DOCTYPE x [<!ENTITY e SYSTEM "file:///etc/passwd">]><hemibrain><neuron id="&e;"/></hemibrain>',
    "malformed": "<hemibrain><neuron id='A'></hemibrain>",
    "dup_id": '<hemibrain><neuron id="A"/><neuron id=" A "/></hemibrain>',
    "empty_id": '<hemibrain><neuron id=""/></hemibrain>',
    "unknown_from": '<hemibrain><neuron id="A"/><connection from="Z" to="A" weight="1"/></hemibrain>',
    "unknown_to": '<hemibrain><neuron id="A"/><connection from="A" to="Z" weight="1"/></hemibrain>',
    "missing_weight": '<hemibrain><neuron id="A"/><connection from="A" to="A"/></hemibrain>',
    "nan_weight": '<hemibrain><neuron id="A"/><connection from="A" to="A" weight="NaN"/></hemibrain>',
    "inf_weight": '<hemibrain><neuron id="A"/><connection from="A" to="A" weight="Infinity"/></hemibrain>',
    "text_weight": '<hemibrain><neuron id="A"/><connection from="A" to="A" weight="lots"/></hemibrain>',
    "zero_delay": '<hemibrain><neuron id="A"/><connection from="A" to="A" weight="1" delayMs="0"/></hemibrain>',
    "neg_delay": '<hemibrain><neuron id="A"/><connection from="A" to="A" weight="1" delayMs="-2"/></hemibrain>',
    "dup_pair": '<hemibrain><neuron id="A"/><neuron id="B"/>'
                '<connection from="A" to="B" weight="1"/><connection from="A" to="B" weight="2"/></hemibrain>',
}


@pytest.mark.parametrize("name", sorted(BAD))
def test_check_rejects_bad_files(tmp_path, name, capsys):
    p = tmp_path / f"{name}.xml"
    p.write_text(BAD[name], encoding="utf-8")
    errs, _ = check_hhmi.check(p)
    assert errs, name
    assert check_hhmi.main([str(p)]) == 1
    assert "[!] INVALID" in capsys.readouterr().out


def test_check_accepts_self_loop_negative_weight_and_delay(tmp_path):
    p = tmp_path / "ok.xml"
    p.write_text('<hemibrain><neuron id="A"/><neuron id="B"/>'
                 '<connection from="A" to="A" weight="-0.5" delayMs="2.5"/>'
                 '<connection from="A" to="B" weight="1"/></hemibrain>')
    errs, s = check_hhmi.check(p)
    assert errs == [] and s["self_loops"] == 1 and s["negative_weights"] == 1
    assert s["default_delay"] == 1


def test_check_missing_file(tmp_path):
    assert check_hhmi.main([str(tmp_path / "nope.xml")]) == 1


def test_package_is_not_named_scripts():
    import hhmi_scripts
    assert Path(hhmi_scripts.__file__).parent == ROOT / "hhmi_scripts"
    assert not (ROOT / "scripts").exists()
