from __future__ import annotations

import unittest

from tools.check_public_text import _scan_added_patch, contains_restricted_wording


def text(points: tuple[int, ...]) -> str:
    return "".join(chr(point) for point in points)


class PublicTextTests(unittest.TestCase):
    def test_patch_scan_checks_additions_but_allows_removal(self) -> None:
        excluded = text((99, 111, 100, 101, 120))
        issues: list[str] = []
        removal = f"diff --git a/file b/file\n-{excluded}\n+neutral wording\n".encode()
        _scan_added_patch("test", removal, issues)
        self.assertEqual(issues, [])

        addition = f"diff --git a/file b/file\n-old wording\n+{excluded}\n".encode()
        _scan_added_patch("test", addition, issues)
        self.assertEqual(len(issues), 1)

    def test_detects_excluded_standalone_word(self) -> None:
        excluded = text((99, 111, 100, 101, 120))
        self.assertTrue(contains_restricted_wording(f"Built with {excluded}"))

    def test_ignores_word_fragments(self) -> None:
        self.assertFalse(contains_restricted_wording("Maintain readable email output."))

    def test_accepts_project_specific_description(self) -> None:
        self.assertFalse(
            contains_restricted_wording("DevRelay creates portable Git development handoffs.")
        )


if __name__ == "__main__":
    unittest.main()
