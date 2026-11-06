# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Skill checks for the CB2514 male-cns identification record."""
import json
from pathlib import Path

import cb2514_opd as opd

SKILL = Path(__file__).resolve().parents[1]
REPO = SKILL.parents[1]


def test_context_matches_neuron_index():
    context = json.loads((SKILL / "assets" / "context.json").read_text(encoding="utf-8"))
    index = opd.build_neuron_index(REPO)
    assert context["body_ids"] == index["bodyIds"]
    assert context["dataset_id"] == "male-cns:v1.0"
    assert context["cell_type"] == "CB2514"
    assert context["laterality"] == {"L": 3, "R": 2}
    assert context["edges_included"] is False
    assert context["pvlp_r_chart_membership_unverified"] is True
    assert context["hhmi_jenalia_pom_fabricated"] is False
    assert not (REPO / "docs" / "hhmi_jenalia.pom").exists()
    blocked = opd.validate_distillation_input(None, REPO)
    assert blocked["missing_prerequisites"] == context["distillation_required_when_absent"]
