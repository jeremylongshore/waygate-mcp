import copy
import unittest

from ci.benchmark.verify import EXPECTED, verify_report


class BenchmarkReportTests(unittest.TestCase):
    def setUp(self):
        self.report = {
            "benchmarks": [
                {"name": name, "stats": {"min": 1, "mean": 2, "max": 3, "rounds": 10}}
                for name in EXPECTED
            ]
        }

    def test_measured_report_passes(self):
        self.assertEqual(verify_report(self.report)["measurements"], 2)

    def test_empty_missing_duplicate_and_unexpected_cases_fail(self):
        for rows in [
            [],
            self.report["benchmarks"][:1],
            [self.report["benchmarks"][0]] * 2,
            [{"name": "unrelated"}],
        ]:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                verify_report({"benchmarks": rows})

    def test_invalid_or_absent_statistics_fail(self):
        for key in ("min", "max", "mean", "rounds"):
            for value in (None, 0, -1, True, "1", float("nan"), float("inf")):
                report = copy.deepcopy(self.report)
                report["benchmarks"][0]["stats"][key] = value
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    verify_report(report)

    def test_inconsistent_statistics_fail(self):
        self.report["benchmarks"][0]["stats"]["mean"] = 4
        with self.assertRaises(ValueError):
            verify_report(self.report)
