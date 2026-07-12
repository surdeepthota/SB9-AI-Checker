"""The five pipeline layers, in the LOCKED execution order.

Modules are named by function, not number, so the narrative survives any reordering:
    provenance  -> measurement -> forensics -> judgment -> action

Only `forensics.py` and part of `judgment.py` involve an actual AI/ML model. The other
three layers are deliberately deterministic — see each module's docstring for why.
"""
