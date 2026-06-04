"""P4.5 verification: schema diagram, profiling, and data-quality checks (read-only, no LLM)."""

from promptdb.data.profile import profile_db
from promptdb.data.quality import check_quality
from promptdb.data.schema_graph import mermaid_er


def test_schema_mermaid():
    m = mermaid_er()
    assert m.startswith("erDiagram")
    assert "Artist" in m
    assert "||--o{" in m  # at least one foreign-key relationship rendered


def test_profile_counts():
    data = {t["table"]: t for t in profile_db()}
    assert data["Customer"]["rows"] == 59
    assert data["Track"]["rows"] == 3503


def test_doctor_flags_high_null_column():
    issues = check_quality()
    assert any("Company" in i["issue"] for i in issues)
