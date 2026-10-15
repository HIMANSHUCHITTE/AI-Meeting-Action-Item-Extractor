"""
MeetMind AI - Comprehensive Unit & Scenario Test Suite
Tests validation, date handling, duplicate detection, schema integrity, and error guards.
"""

import unittest
import json
import pandas as pd
from datetime import datetime
import meeting_extractor as me


class TestMeetMindAILogic(unittest.TestCase):

    def test_empty_transcript_validation(self):
        """Test rejection of empty and whitespace-only transcripts."""
        valid, msg = me.validate_transcript_input("")
        self.assertFalse(valid)
        self.assertIn("empty", msg.lower())

        valid, msg = me.validate_transcript_input("   \n\t  ")
        self.assertFalse(valid)
        self.assertIn("empty", msg.lower())

        valid, msg = me.validate_transcript_input("Too short")
        self.assertFalse(valid)
        self.assertIn("short", msg.lower())

    def test_iso_date_validation(self):
        """Test ISO YYYY-MM-DD date validation."""
        self.assertTrue(me.is_valid_iso_date("2026-10-20"))
        self.assertTrue(me.is_valid_iso_date("2026-02-28"))
        self.assertFalse(me.is_valid_iso_date("2026-02-30"))  # Invalid leap date
        self.assertFalse(me.is_valid_iso_date("tomorrow"))
        self.assertFalse(me.is_valid_iso_date("10/20/2026"))
        self.assertFalse(me.is_valid_iso_date(None))

    def test_missing_owner_detection(self):
        """Test handling and warnings when owner is missing or unassigned."""
        raw_items = [
            {
                "task": "Arrange client review meeting",
                "owner": None,
                "deadline": "2026-10-25",
                "status": "Pending",
                "confidence": 88,
                "evidence": "Someone needs to arrange the next client review"
            }
        ]
        transcript = "Someone needs to arrange the next client review, but we haven't assigned an owner."
        validated = me.validate_and_clean_action_items(raw_items, transcript)
        
        self.assertEqual(len(validated), 1)
        self.assertEqual(validated[0]["owner"], "Unassigned")
        self.assertTrue(any("Missing owner" in w for w in validated[0]["warnings"]))

    def test_missing_deadline_detection(self):
        """Test handling when deadline is omitted."""
        raw_items = [
            {
                "task": "Review API documentation",
                "owner": "Rahul",
                "deadline": None,
                "status": "Pending",
                "confidence": 90,
                "evidence": "Rahul: I will review the API docs."
            }
        ]
        transcript = "Rahul: I will review the API docs."
        validated = me.validate_and_clean_action_items(raw_items, transcript)
        
        self.assertIsNone(validated[0]["deadline"])
        self.assertTrue(any("No deadline specified" in w for w in validated[0]["warnings"]))

    def test_completed_task_status(self):
        """Test that completed tasks preserve Completed status and are not forced to Pending."""
        raw_items = [
            {
                "task": "Deploy login page",
                "owner": "Rahul",
                "deadline": "2026-10-10",
                "status": "Completed",
                "confidence": 99,
                "evidence": "The login page is already completed."
            }
        ]
        transcript = "Rahul: The login page is already completed."
        validated = me.validate_and_clean_action_items(raw_items, transcript)
        
        self.assertEqual(validated[0]["status"], "Completed")

    def test_duplicate_detection(self):
        """Test detection and marking of near-duplicate action items without deleting either."""
        raw_items = [
            {
                "task": "Prepare the monthly project report",
                "owner": "Amit",
                "deadline": "2026-10-20",
                "status": "Pending",
                "confidence": 92,
                "evidence": "Amit will prepare report"
            },
            {
                "task": "Prepare monthly project report",
                "owner": "Amit",
                "deadline": "2026-10-20",
                "status": "Pending",
                "confidence": 91,
                "evidence": "Amit prepares report"
            }
        ]
        transcript = "Amit will prepare the report."
        validated = me.validate_and_clean_action_items(raw_items, transcript)
        
        self.assertEqual(len(validated), 2)  # Neither was silently deleted
        self.assertTrue(any("duplicate" in w.lower() for w in validated[0]["warnings"]))
        self.assertTrue(any("duplicate" in w.lower() for w in validated[1]["warnings"]))

    def test_relative_deadline_flagging(self):
        """Test that relative deadlines without ISO resolution are preserved and flagged."""
        raw_items = [
            {
                "task": "Share integration progress with team",
                "owner": "Rahul",
                "deadline": "tomorrow",
                "status": "Pending",
                "confidence": 85,
                "evidence": "Rahul, please share the integration progress tomorrow."
            }
        ]
        transcript = "Priya: Rahul, please share the integration progress tomorrow."
        validated = me.validate_and_clean_action_items(raw_items, transcript)
        
        self.assertEqual(validated[0]["deadline"], "tomorrow")
        self.assertTrue(any("requires confirmation" in w for w in validated[0]["warnings"]))

    def test_api_key_configuration_check(self):
        """Test distinguishing configured API key from empty/placeholder."""
        is_cfg, msg = me.check_api_configuration("")
        self.assertFalse(is_cfg)
        
        is_cfg, msg = me.check_api_configuration("your_gemini_api_key_here")
        self.assertFalse(is_cfg)
        
        is_cfg, msg = me.check_api_configuration("AIzaSyValidFormatSampleKey123")
        self.assertTrue(is_cfg)

    def test_csv_json_export_structure(self):
        """Test CSV and JSON export transformation from pandas DataFrame."""
        rows = [
            {
                "ID": 1,
                "Task": "Prepare project report",
                "Owner": "Amit",
                "Deadline": "2026-10-20",
                "Status": "Pending",
                "Confidence (%)": 95,
                "Review Warnings": "None"
            }
        ]
        df = pd.DataFrame(rows)
        csv_str = df.to_csv(index=False)
        self.assertIn("Prepare project report", csv_str)
        self.assertIn("Amit", csv_str)

        json_export = {
            "meeting_summary": "Summary text",
            "action_items": df.to_dict(orient="records")
        }
        json_str = json.dumps(json_export)
        parsed = json.loads(json_str)
        self.assertEqual(len(parsed["action_items"]), 1)
        self.assertEqual(parsed["action_items"][0]["Owner"], "Amit")


if __name__ == "__main__":
    unittest.main()
