#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Void-QCH plugin."""

from .base import Plugin


class VoidQCHPlugin(Plugin):
    name = "void_qch"
    description = "phi-harmonic chemical precision ladder"
    soft = True

    def check(self, strict: bool = False):
        result = {"name": self.name, "passed": True, "message": ""}
        try:
            from quantum.cdp_convergence.void_qch import LADDER, PROGRESSION

            for name, expected in PROGRESSION.items():
                measured = LADDER.get(name)
                if measured is None:
                    raise Exception(f"Missing rung {name}")
                if abs(measured - expected) > 0.001:
                    raise Exception(f"Rung {name}: measured {measured}, expected {expected}")
            result["message"] = "All phi-rungs within tolerance"
        except Exception as e:
            result["passed"] = False
            result["message"] = f"Void-QCH check failed: {e}"
        return result
