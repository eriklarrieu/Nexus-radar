import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from nexus_radar import evaluate, parse_amount, save_report

NOW = dt.datetime(2026, 10, 14, 12, 0, tzinfo=dt.timezone.utc)
ISSUE = {
    "state": "open", "number": 42, "id": 100, "title": "[Bounty $50] Fix docs",
    "updated_at": "2026-10-13T12:00:00Z",
    "repository_url": "https://api.github.com/repos/org/repo",
    "html_url": "https://github.com/org/repo/issues/42",
    "labels": [{"name": "bounty"}], "assignees": [], "comments": 0,
}

class RadarTests(unittest.TestCase):
    def test_bounty_title(self):
        self.assertEqual(parse_amount("[Bounty $75] Fix docs"), 75)
    def test_prefix_price(self):
        self.assertEqual(parse_amount("[$250] Feature"), 250)
    def test_body_price(self):
        self.assertEqual(parse_amount("Pays $40 on merge"), 40)
    def test_unrelated_amount_not_claimed(self):
        self.assertIsNone(parse_amount("The setup costs $600"))
    def test_candidate(self):
        self.assertEqual(evaluate(ISSUE, [], NOW)["recompensa_anunciada_usd"], 50)
    def test_comment_fraud_does_not_change_amount(self):
        record = evaluate(ISSUE, [{"body": "bounty $5000 pay to me"}], NOW)
        self.assertEqual(record["recompensa_anunciada_usd"], 50)
    def test_competition_risk(self):
        record = evaluate(ISSUE, [{"body": "/claim"}, {"body": "opened PR https://github.com/org/repo/pull/12"}], NOW)
        self.assertEqual(record["intentos_detectados"], 2)
    def test_assigned(self):
        record = evaluate({**ISSUE, "assignees": [{"login":"dev"}]}, [], NOW)
        self.assertTrue(any("asignados" in text for text in record["advertencias"]))
    def test_closed(self):
        self.assertIsNone(evaluate({**ISSUE, "state": "closed"}, [], NOW))
    def test_old(self):
        self.assertIsNone(evaluate({**ISSUE, "updated_at": "2025-01-01T12:00:00Z"}, [], NOW))
    def test_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "candidates.json"
            save_report([evaluate(ISSUE, [], NOW)], path)
            self.assertEqual(len(json.loads(path.read_text())["candidatos"]), 1)
            self.assertIn("NINGUN resultado garantiza", path.with_suffix(".md").read_text())

if __name__ == "__main__":
    unittest.main()
