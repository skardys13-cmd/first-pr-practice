"""Exact identifier matching (Constitution V, F-17, F-21)."""

import unittest

from ria_agent.matching import (
    accounts_equal, contains_account, find_account, identifier_groups,
    normalise_account, resolve_sole_account,
)


class Equality(unittest.TestCase):
    def test_identical_accounts_agree(self):
        self.assertTrue(accounts_equal("1234-5678", "1234-5678"))

    def test_formatting_does_not_change_identity(self):
        for other in ("1234 5678", "12345678", "1234/5678", "1234.5678"):
            with self.subTest(other=other):
                self.assertTrue(accounts_equal("1234-5678", other))

    def test_different_accounts_do_not_agree(self):
        self.assertFalse(accounts_equal("1234-5678", "1234-5679"))

    def test_a_prefix_is_not_a_match(self):
        self.assertFalse(accounts_equal("1234", "1234-5678"))

    def test_a_substring_is_not_a_match(self):
        self.assertFalse(accounts_equal("1234-5678", "51234-56789"))

    def test_empty_matches_nothing_including_empty(self):
        self.assertFalse(accounts_equal("", ""))
        self.assertFalse(accounts_equal("", "1234"))

    def test_case_is_ignored_for_alphanumeric_accounts(self):
        self.assertTrue(accounts_equal("ab12-cd34", "AB12CD34"))

    def test_normalisation_strips_only_separators(self):
        self.assertEqual(normalise_account("1234-5678"), "12345678")
        self.assertEqual(normalise_account(" ab-12 "), "AB12")


class TextSearch(unittest.TestCase):
    def test_finds_the_account_in_a_document(self):
        self.assertTrue(contains_account("Account 1234-5678 statement", "1234-5678"))

    def test_finds_it_written_without_separators(self):
        self.assertTrue(contains_account("acct 12345678 period", "1234-5678"))

    def test_finds_it_across_a_line_break(self):
        self.assertTrue(contains_account("Acct No. 1234 5678\nPeriod: Aug", "1234-5678"))

    def test_finds_the_right_one_among_several(self):
        text = "Accounts: 1234-5678, 1234-5679"
        self.assertTrue(contains_account(text, "1234-5679"))
        self.assertFalse(contains_account(text, "1234-5670"))

    def test_a_longer_account_containing_ours_is_not_a_match(self):
        self.assertFalse(contains_account("Account 91234-56780", "1234-5678"))

    def test_an_account_that_extends_ours_is_not_a_match(self):
        self.assertFalse(contains_account("Account 1234-5678-9012", "1234-5678"))

    def test_a_trailing_fragment_is_not_a_match(self):
        self.assertFalse(contains_account("ending 5678", "1234-5678"))

    def test_a_letter_glued_to_the_front_is_not_a_match(self):
        self.assertFalse(contains_account("x1234-5678", "1234-5678"))

    def test_empty_inputs_find_nothing(self):
        self.assertFalse(contains_account("", "1234-5678"))
        self.assertFalse(contains_account("1234-5678", ""))

    def test_identifiers_are_split_at_real_boundaries(self):
        self.assertEqual(
            identifier_groups("Accounts: 1234-5678, 1234-5679 at Schwab"),
            ["Accounts", "12345678", "12345679", "at", "Schwab"])


class Resolution(unittest.TestCase):
    def test_finding_a_named_account_among_linked_ones(self):
        match = find_account("1234-5678", ["1234-5678", "9999-0000"])
        self.assertTrue(match.found)
        self.assertEqual(match.value, "1234-5678")

    def test_a_named_account_that_is_not_linked_is_not_found(self):
        self.assertFalse(find_account("5555-0000", ["1234-5678"]).found)

    def test_the_same_account_written_twice_is_not_an_ambiguity(self):
        match = find_account("1234 5678", ["1234-5678", "12345678"])
        self.assertTrue(match.found)
        self.assertFalse(match.ambiguous)

    def test_one_linked_account_resolves(self):
        self.assertEqual(resolve_sole_account(["1234-5678"]).value, "1234-5678")

    def test_two_linked_accounts_are_ambiguous_not_a_choice(self):
        match = resolve_sole_account(["1234-5678", "1234-5679"])
        self.assertFalse(match.found)
        self.assertTrue(match.ambiguous)
        self.assertIn("2 are linked", match.reason)

    def test_no_linked_account_is_not_an_ambiguity(self):
        match = resolve_sole_account([])
        self.assertFalse(match.found)
        self.assertFalse(match.ambiguous)

    def test_duplicates_of_one_account_still_resolve(self):
        self.assertEqual(resolve_sole_account(["1234-5678", "1234 5678"]).value, "1234-5678")


if __name__ == "__main__":
    unittest.main()
