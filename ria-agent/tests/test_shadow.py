"""Shadow mode takes no actions, and its report finds what matters (Steps 15-16)."""

import tempfile
import unittest
from datetime import date

from ria_agent.classifier import Classifier
from ria_agent.crm import CrmTask, FixtureCrm
from ria_agent.log_store import LogStore
from ria_agent.receipts import READ, VERIFIED
from ria_agent.shadow import Observation, ShadowRunner, build_report
from ria_agent.whitelist import Whitelist

TODAY = date(2026, 9, 4)


def an_observation(**overrides) -> Observation:
    base = dict(task_id="RT-1", template="Statement Retrieval",
                workflow="statement_retrieval", confidence=0.99, basis="template",
                plan={"account": "1234-5678", "period": "2026-08"}, receipt_id="r1")
    base.update(overrides)
    return Observation(**base)


class RunningInShadow(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.store = LogStore(self._dir.name)
        self.addCleanup(self.store.close)
        self.crm = FixtureCrm.from_bundled_fixtures()
        self.runner = ShadowRunner(
            self.crm, Classifier(), self.store,
            operator="Ant", role="para_planner", model_version="claude-x-1")

    def test_every_open_task_is_observed(self):
        observations = self.runner.run(today=TODAY)
        self.assertEqual(len(observations), len(self.crm.open_tasks()))

    def test_every_observation_is_receipted(self):
        self.runner.run(today=TODAY)
        self.assertEqual(self.store.count(), len(self.crm.open_tasks()))

    def test_nothing_but_reads_are_recorded(self):
        self.runner.run(today=TODAY)
        for receipt in self.store.query():
            self.assertEqual(receipt.action_type, READ)
            self.assertEqual(receipt.outcome, VERIFIED)

    def test_the_runner_holds_nothing_that_could_act(self):
        surface = {name for name in dir(self.runner) if not name.startswith("_")}
        self.assertEqual(surface & {"navigate", "click", "write", "file", "submit"}, set())

    def test_the_receipt_carries_the_resolved_plan_not_just_a_label(self):
        self.runner.observe(self.crm.task("RT-4503"), TODAY)
        receipt = self.store.query(crm_task_id="RT-4503")[0]
        plan = next(e.value for e in receipt.evidence if isinstance(e.value, dict))
        self.assertEqual(plan["workflow"], "statement_retrieval")
        self.assertEqual(plan["account"], "8443-1468")
        self.assertEqual(plan["period"], "2026-08")

    def test_every_extracted_value_carries_its_source(self):
        self.runner.observe(self.crm.task("RT-4503"), TODAY)
        receipt = self.store.query(crm_task_id="RT-4503")[0]
        for piece in receipt.evidence:
            if piece.kind == "extracted_value":
                self.assertTrue(piece.source_location)

    def test_confidence_is_logged_on_every_observation(self):
        self.runner.run(today=TODAY)
        for receipt in self.store.query():
            self.assertIsNotNone(receipt.confidence)

    def test_instruction_shaped_notes_are_receipted_not_obeyed(self):
        self.runner.observe(self.crm.task("RT-4570"), TODAY)
        receipt = self.store.query(crm_task_id="RT-4570")[0]
        blob = " ".join(str(piece.value) for piece in receipt.evidence)
        self.assertIn("instruction-shaped text ignored", blob)
        plan = next(e.value for e in receipt.evidence if isinstance(e.value, dict))
        self.assertEqual(plan["workflow"], "statement_retrieval")

    def test_an_unrecognised_task_is_observed_rather_than_forced(self):
        observation = self.runner.observe(self.crm.task("RT-4560"), TODAY)
        self.assertFalse(observation.recognised)


class Scoring(unittest.TestCase):
    def test_nothing_labelled_means_nothing_concluded(self):
        report = build_report([an_observation()], {})
        self.assertEqual(report.totals.labelled, 0)
        self.assertIsNone(report.totals.confidently_wrong_rate)
        self.assertIn("nothing can be concluded", report.summary())
        self.assertEqual(report.unlabelled, ["RT-1"])

    def test_a_correct_classification_scores_correct(self):
        report = build_report([an_observation()],
                              {"RT-1": {"workflow": "statement_retrieval"}})
        self.assertEqual(report.totals.correct, 1)
        self.assertEqual(report.totals.confidently_wrong, 0)

    def test_a_confident_wrong_answer_is_counted_as_such(self):
        report = build_report([an_observation(confidence=0.99)],
                              {"RT-1": {"workflow": "document_filing"}})
        self.assertEqual(report.totals.confidently_wrong, 1)
        self.assertEqual(report.totals.quietly_wrong, 0)

    def test_an_unsure_wrong_answer_is_counted_separately(self):
        report = build_report([an_observation(confidence=0.4)],
                              {"RT-1": {"workflow": "document_filing"}})
        self.assertEqual(report.totals.confidently_wrong, 0)
        self.assertEqual(report.totals.quietly_wrong, 1)

    def test_unrecognised_is_not_counted_as_wrong(self):
        report = build_report([an_observation(workflow="unrecognised", confidence=0.0)],
                              {"RT-1": {"workflow": "document_filing"}})
        self.assertEqual(report.totals.unrecognised, 1)
        self.assertEqual(report.totals.confidently_wrong, 0)

    def test_the_right_workflow_pointed_at_the_wrong_account_is_caught(self):
        report = build_report(
            [an_observation()],
            {"RT-1": {"workflow": "statement_retrieval", "account": "9999-0000"}})
        self.assertEqual(report.totals.correct, 1)
        self.assertEqual(report.totals.resolution_wrong, 1)

    def test_the_right_workflow_with_the_wrong_period_is_caught(self):
        report = build_report(
            [an_observation()],
            {"RT-1": {"workflow": "statement_retrieval", "period": "2026-07"}})
        self.assertEqual(report.totals.resolution_wrong, 1)

    def test_a_label_without_a_target_does_not_score_resolution(self):
        report = build_report([an_observation()],
                              {"RT-1": {"workflow": "statement_retrieval"}})
        self.assertEqual(report.totals.resolution_wrong, 0)

    def test_scores_are_reported_per_template(self):
        observations = [
            an_observation(task_id="a", template="Good"),
            an_observation(task_id="b", template="Bad", workflow="document_filing"),
        ]
        labels = {"a": {"workflow": "statement_retrieval"},
                  "b": {"workflow": "statement_retrieval"}}
        report = build_report(observations, labels)
        self.assertEqual(report.by_template["Good"].confidently_wrong, 0)
        self.assertEqual(report.by_template["Bad"].confidently_wrong, 1)


class Whitelisting(unittest.TestCase):
    def _report(self, good=20, bad=0, template="Statement Retrieval"):
        observations, labels = [], {}
        for index in range(good):
            observations.append(an_observation(task_id=f"g{index}", template=template))
            labels[f"g{index}"] = {"workflow": "statement_retrieval"}
        for index in range(bad):
            observations.append(an_observation(
                task_id=f"b{index}", template=template, workflow="document_filing"))
            labels[f"b{index}"] = {"workflow": "statement_retrieval"}
        return build_report(observations, labels)

    def test_a_clean_template_with_enough_samples_is_whitelisted(self):
        self.assertIn("Statement Retrieval",
                      self._report(good=20).clean_templates(min_samples=20))

    def test_a_single_confident_error_disqualifies_a_template(self):
        report = self._report(good=99, bad=1)
        self.assertEqual(report.by_template["Statement Retrieval"].confidently_wrong, 1)
        self.assertNotIn("Statement Retrieval", report.clean_templates(min_samples=20))

    def test_an_aggregate_cannot_hide_a_broken_template(self):
        # 99 clean of one template, 3 of another that is always wrong. The
        # aggregate rate is ~3%, but the broken template must not be whitelisted.
        observations, labels = [], {}
        for index in range(99):
            observations.append(an_observation(task_id=f"g{index}", template="Good"))
            labels[f"g{index}"] = {"workflow": "statement_retrieval"}
        for index in range(3):
            observations.append(an_observation(
                task_id=f"b{index}", template="Broken", workflow="document_filing"))
            labels[f"b{index}"] = {"workflow": "statement_retrieval"}
        report = build_report(observations, labels)
        self.assertLess(report.totals.confidently_wrong_rate, 0.05)
        clean = report.clean_templates(min_samples=3)
        self.assertIn("Good", clean)
        self.assertNotIn("Broken", clean)

    def test_too_few_samples_is_not_whitelisted(self):
        self.assertNotIn("Statement Retrieval",
                         self._report(good=5).clean_templates(min_samples=20))

    def test_misresolution_alone_disqualifies_a_template(self):
        observations = [an_observation(task_id=f"g{i}") for i in range(20)]
        labels = {f"g{i}": {"workflow": "statement_retrieval"} for i in range(20)}
        labels["g0"] = {"workflow": "statement_retrieval", "account": "9999-0000"}
        report = build_report(observations, labels)
        self.assertEqual(report.totals.confidently_wrong, 0)
        self.assertNotIn("Statement Retrieval", report.clean_templates(min_samples=20))

    def test_a_whitelist_can_be_built_from_a_report(self):
        whitelist = Whitelist.from_report(self._report(good=20), min_samples=20)
        self.assertIn("Statement Retrieval", whitelist)


if __name__ == "__main__":
    unittest.main()
