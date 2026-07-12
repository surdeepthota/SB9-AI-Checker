"""PeachCheck: layered trust pipeline for AI-media provenance and SB 9 disclosure checks.

Pipeline order (see layers/ package): provenance -> measurement -> forensics -> judgment -> action.
Each layer only appends to the TrustReport defined in schema.py; nothing reads ahead.
"""
