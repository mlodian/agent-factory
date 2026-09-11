"""Present so pytest puts the project root on sys.path.

tests/ has no __init__.py, so in pytest's default import mode the directory it
inserts is tests/ itself, and `from src.load import ...` would fail. A conftest
at the root makes the root the inserted directory instead. Empty on purpose —
there are no shared fixtures; each test file builds the payload it needs.
"""
