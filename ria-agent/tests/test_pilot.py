"""Pilot scoring against the plan's four criteria (Steps 49-50)."""

import tempfile
import unittest
from pathlib import Path

from ria_agent.health import Baselines
from ria_agent.log_store import LogStore
from ria_agent.pilot import HumanAnswer, load_answers, save_answers, score
from ria_agent.receipts import (
    Evidence, PENDING_APPROVAL, READ, Receipt, VERIFIED, WRITE,
)

WORKFLOW = "statement_retrieval"


def a_run(index: int, minutes: float = 0.5, **overrides) -> Receipt:
    start = f"2026-09-04T09:{index:02d}:00+00:00"
    end_minute = index + int(minutes)
    base = dict(
        human_owner="Ant", role="para_planner", crm_task_id=f"RT-{index}",
        workflow_id=WORKFLOW, step_id="retrieve_statement", system_touched="schwab",
        action_type=READ, target_identifier="1234-5678", outcome=PENDING_APPROVAL,
        timestamp_start=start,
        timestamp_end=f"2026-09-04T09:{min(end_minute, 59):02d}:{int((minutes % 1) * 60):02d}+00:00",
        model_version="claude-x-1", evidence=[Evidence("file_hash", f"h{index}")],
    )
    base.update(overrides)
    return Receipt(**base)


def answered(value=True, by="Bea"):
    return HumanAnswer("q", answered=value, answered_by=by, answered_on="2026-10-02")


def unanswered():
    return HumanAnswer("Has anyone actually checked?")


class PilotTestCase(unittest.TestCase):
    def setUp(self):
        self.directory = Path(tempfile.mkdtemp())
        self.log = LogStore(self.directory / "log")
        self.addCleanup(self.log.close)
        for index in range(10):
            self.log.append(a_run(index))

    def score(self, baselines=None, readable=None, prefers=None):
        return score(
            self.log, workflow_id=WORKFLOW, person="Ant",
            baselines=baselines or Baselines(),
            log_is_readable=readable or answered(),
            person_prefers_it=prefers or answered(by="Ant"))


class Criteria(PilotTestCase):
    def test_ten_runs_are_counted(self):
        self.assertEqual(self.score().completed, 10)

    def test_zero_unapproved_writes_passes(self):
        result = self.score()
        criterion = next(c for c in result.criteria if "unapproved" in c.name)
        self.assertTrue(criterion.passed)

    def test_an_unapproved_write_cannot_even_be_stored(self):
        """Constitution II is enforced at the data layer, not only the executor."""
        from ria_agent.receipts import InvalidReceipt

        with self.assertRaises(InvalidReceipt):
            self.log.append(a_run(11, action_type=WRITE, outcome=VERIFIED,
                                  before_state={"a": 1}, after_state={"a": 2},
                                  auto_executed=False, references_receipt_id=None))

    def test_an_unapproved_write_that_got_in_anyway_fails_the_pilot(self):
        """Defence in depth: a receipt that bypassed validation is still caught.

        The validator refuses to store one, so the only way this appears is
        something writing to the database directly. The pilot still notices.
        """
        import json

        smuggled = a_run(11, action_type=WRITE, outcome=VERIFIED,
                         before_state={"a": 1}, after_state={"a": 2},
                         auto_executed=False, references_receipt_id=None,
                         evidence=[Evidence("field_values", {"a": 2})])
        self.log._insert(smuggled, json.dumps(smuggled.to_dict(), sort_keys=True),
                         "2026-09-04T09:30:00+00:00")

        result = self.score()
        criterion = next(c for c in result.criteria if "unapproved" in c.name)
        self.assertFalse(criterion.passed)
        self.assertIn("stop the pilot", criterion.detail)
        self.assertEqual(result.invalid_receipts, 1)

    def test_all_four_criteria_are_reported(self):
        self.assertEqual(len(self.score().criteria), 4)


class TimeCriterion(PilotTestCase):
    def test_without_a_manual_baseline_it_is_undecided(self):
        criterion = self.score().criteria[0]
        self.assertIsNone(criterion.passed)
        self.assertIn("nothing to compare", criterion.detail)

    def test_without_a_review_time_it_is_still_undecided(self):
        """F-38: agent step time alone is not the number that matters."""
        criterion = self.score(Baselines({WORKFLOW: 6.0})).criteria[0]
        self.assertIsNone(criterion.passed)
        self.assertIn("F-38", criterion.detail)

    def test_a_real_saving_passes(self):
        result = self.score(Baselines({WORKFLOW: 6.0}, {WORKFLOW: 1.5}))
        self.assertTrue(result.criteria[0].passed)
        self.assertGreater(result.time_saved, 0.5)

    def test_review_time_eating_the_saving_fails(self):
        result = self.score(Baselines({WORKFLOW: 6.0}, {WORKFLOW: 5.0}))
        self.assertFalse(result.criteria[0].passed)
        self.assertLess(result.time_saved, 0.5)

    def test_the_detail_shows_both_halves(self):
        criterion = self.score(Baselines({WORKFLOW: 6.0}, {WORKFLOW: 1.5})).criteria[0]
        self.assertIn("agent", criterion.detail)
        self.assertIn("review", criterion.detail)


class HumanCriteria(PilotTestCase):
    def test_an_unanswered_question_is_undecided_not_failed(self):
        result = self.score(prefers=unanswered())
        criterion = result.criteria[3]
        self.assertIsNone(criterion.passed)
        self.assertIn("not answered", criterion.detail)

    def test_an_undecided_pilot_does_not_pass(self):
        result = self.score(Baselines({WORKFLOW: 6.0}, {WORKFLOW: 1.0}),
                            prefers=unanswered())
        self.assertFalse(result.passed)
        self.assertIn("need a person to answer", result.summary())

    def test_a_no_answer_fails_rather_than_being_ignored(self):
        result = self.score(Baselines({WORKFLOW: 6.0}, {WORKFLOW: 1.0}),
                            prefers=answered(False, by="Ant"))
        self.assertFalse(result.passed)

    def test_an_answer_records_who_gave_it(self):
        criterion = self.score(readable=answered(by="a stranger")).criteria[2]
        self.assertIn("a stranger", criterion.detail)

    def test_an_answer_without_a_name_does_not_count(self):
        criterion = self.score(
            readable=HumanAnswer("q", answered=True, answered_by="")).criteria[2]
        self.assertIsNone(criterion.passed)

    def test_a_receipt_without_evidence_fails_before_anyone_is_asked(self):
        self.log.append(a_run(11, evidence=[], outcome="stopped_no_change",
                              stop_reason="timeout", stop_next_step="Retry."))
        # A stop may carry no evidence; a completed run may not.
        self.log.append(Receipt(
            human_owner="Ant", role="para_planner", crm_task_id="RT-12",
            workflow_id=WORKFLOW, step_id="retrieve_statement",
            system_touched="schwab", action_type=READ, target_identifier="x",
            outcome=PENDING_APPROVAL, model_version="claude-x-1", evidence=[]))
        criterion = self.score().criteria[2]
        self.assertFalse(criterion.passed)

    def test_all_four_met_passes(self):
        result = self.score(Baselines({WORKFLOW: 6.0}, {WORKFLOW: 1.0}))
        self.assertTrue(result.passed)
        self.assertIn("All four criteria met", result.summary())


class Answers(unittest.TestCase):
    def test_a_missing_file_yields_unanswered_questions(self):
        answers = load_answers(Path(tempfile.mkdtemp()) / "none.json")
        self.assertEqual(set(answers), {"log_is_readable", "person_prefers_it"})
        self.assertFalse(any(answer.recorded for answer in answers.values()))

    def test_answers_round_trip(self):
        path = Path(tempfile.mkdtemp()) / "answers.json"
        answers = load_answers(path)
        answers["person_prefers_it"] = HumanAnswer(
            "q", answered=True, answered_by="Ant", answered_on="2026-10-02")
        save_answers(path, answers)
        self.assertTrue(load_answers(path)["person_prefers_it"].recorded)

    def test_baselines_keep_both_numbers(self):
        path = Path(tempfile.mkdtemp()) / "baselines.json"
        Baselines({WORKFLOW: 6.0}, {WORKFLOW: 1.5}).save(path)
        reloaded = Baselines.load(path)
        self.assertEqual(reloaded.get(WORKFLOW), 6.0)
        self.assertEqual(reloaded.review(WORKFLOW), 1.5)

    def test_an_older_flat_baselines_file_still_loads(self):
        path = Path(tempfile.mkdtemp()) / "baselines.json"
        path.write_text('{"statement_retrieval": 6.0}')
        self.assertEqual(Baselines.load(path).get(WORKFLOW), 6.0)
        self.assertIsNone(Baselines.load(path).review(WORKFLOW))


if __name__ == "__main__":
    unittest.main()
