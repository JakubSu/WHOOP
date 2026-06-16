from __future__ import annotations

from django.test import SimpleTestCase

from whoop.exceptions import WhoopParseError
from whoop.whoop_api.parsers import parse_cycle, parse_paginated_response, parse_recovery, parse_sleep, parse_workout


class WhoopParserTests(SimpleTestCase):
    def test_parses_cycle_with_score(self) -> None:
        cycle = parse_cycle(
            {
                "id": 93845,
                "user_id": 10129,
                "created_at": "2022-04-24T11:25:44.774Z",
                "updated_at": "2022-04-24T14:25:44.774Z",
                "start": "2022-04-24T02:25:44.774Z",
                "end": "2022-04-24T10:25:44.774Z",
                "timezone_offset": "-05:00",
                "score_state": "SCORED",
                "score": {"strain": 5.2, "kilojoule": 8000.0, "average_heart_rate": 68, "max_heart_rate": 141},
            }
        )

        score = cycle.score
        self.assertIsNotNone(score)
        if score is None:
            self.fail("Expected cycle score to be present.")
        self.assertEqual(score.strain, 5.2)
        self.assertIsNotNone(cycle.created_at.tzinfo)

    def test_parses_recovery_optional_fields(self) -> None:
        recovery = parse_recovery(
            {
                "cycle_id": 93845,
                "sleep_id": "sleep-id",
                "user_id": 10129,
                "created_at": "2022-04-24T11:25:44.774Z",
                "updated_at": "2022-04-24T14:25:44.774Z",
                "score_state": "SCORED",
                "score": {
                    "user_calibrating": False,
                    "recovery_score": 44.0,
                    "resting_heart_rate": 64.0,
                    "hrv_rmssd_milli": 31.8,
                },
            }
        )

        score = recovery.score
        self.assertIsNotNone(score)
        if score is None:
            self.fail("Expected recovery score to be present.")
        self.assertEqual(score.recovery_score, 44.0)
        self.assertIsNone(score.spo2_percentage)

    def test_parses_sleep_and_workout_scores(self) -> None:
        sleep = parse_sleep(_sleep_payload())
        workout = parse_workout(_workout_payload())

        sleep_score = sleep.score
        workout_score = workout.score
        self.assertIsNotNone(sleep_score)
        self.assertIsNotNone(workout_score)
        if sleep_score is None:
            self.fail("Expected sleep score to be present.")
        if workout_score is None:
            self.fail("Expected workout score to be present.")
        self.assertEqual(sleep_score.sleep_performance_percentage, 98.0)
        self.assertEqual(workout_score.zone_durations.zone_three_milli, 900000)

    def test_parses_paginated_response(self) -> None:
        page = parse_paginated_response({"records": [_workout_payload()], "next_token": "next"}, parse_workout)

        self.assertEqual(page.next_token, "next")
        self.assertEqual(page.records[0].sport_name, "running")

    def test_missing_required_field_raises_parse_error(self) -> None:
        with self.assertRaises(WhoopParseError):
            parse_cycle({"id": 1})


def _sleep_payload() -> dict:
    return {
        "id": "sleep-id",
        "cycle_id": 93845,
        "user_id": 10129,
        "created_at": "2022-04-24T11:25:44.774Z",
        "updated_at": "2022-04-24T14:25:44.774Z",
        "start": "2022-04-24T02:25:44.774Z",
        "end": "2022-04-24T10:25:44.774Z",
        "timezone_offset": "-05:00",
        "nap": False,
        "score_state": "SCORED",
        "score": {
            "stage_summary": {
                "total_in_bed_time_milli": 30272735,
                "total_awake_time_milli": 1403507,
                "total_no_data_time_milli": 0,
                "total_light_sleep_time_milli": 14905851,
                "total_slow_wave_sleep_time_milli": 6630370,
                "total_rem_sleep_time_milli": 5879573,
                "sleep_cycle_count": 3,
                "disturbance_count": 12,
            },
            "sleep_needed": {
                "baseline_milli": 27395716,
                "need_from_sleep_debt_milli": 352230,
                "need_from_recent_strain_milli": 208595,
                "need_from_recent_nap_milli": -12312,
            },
            "sleep_performance_percentage": 98.0,
        },
    }


def _workout_payload() -> dict:
    return {
        "id": "workout-id",
        "user_id": 9012,
        "created_at": "2022-04-24T11:25:44.774Z",
        "updated_at": "2022-04-24T14:25:44.774Z",
        "start": "2022-04-24T02:25:44.774Z",
        "end": "2022-04-24T10:25:44.774Z",
        "timezone_offset": "-05:00",
        "sport_name": "running",
        "score_state": "SCORED",
        "score": {
            "strain": 8.2,
            "average_heart_rate": 123,
            "max_heart_rate": 146,
            "kilojoule": 1569.3,
            "percent_recorded": 100.0,
            "zone_durations": {
                "zone_zero_milli": 300000,
                "zone_one_milli": 600000,
                "zone_two_milli": 900000,
                "zone_three_milli": 900000,
                "zone_four_milli": 600000,
                "zone_five_milli": 300000,
            },
        },
    }
