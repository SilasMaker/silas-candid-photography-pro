import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.compose_plan import compose


class AuthoredShotsTests(unittest.TestCase):
    def request(self):
        return {
            "count": 2,
            "seed": 91,
            "locks": {
                "scene": "同一个书房",
                "wardrobe": "原有衬衫与长裤",
                "lens": "50mm标准",
                "shot_distance": "中景",
                "camera_angle": "平视",
                "composition": "三分法留白",
                "foreground": "无明显前景",
                "lighting": "室内窗边漫射光",
            },
            "shots": [
                {
                    "action": "左肘支桌托腮，头略抬，右手笔尖悬停",
                    "expression": "眼睛看向窗外左上方，眉心微收，正在思考",
                },
                {
                    "action": "左手稳住罐身，右手旋盖，肩膀随用力微收",
                    "expression": "头略侧倾，向旁人平视求助，眉头皱起嘴角绷紧",
                },
            ],
        }

    def test_ordered_beats_survive_composition_without_mutating_request(self):
        request = self.request()
        before = copy.deepcopy(request)
        result = compose(request)
        self.assertEqual(request, before)
        for plan, shot in zip(result["plans"], request["shots"]):
            for key, value in shot.items():
                self.assertEqual(plan[key], value)
        self.assertEqual(result["normalized_request"]["shots"], request["shots"])

    def test_same_camera_and_room_can_have_distinct_performances(self):
        result = compose(self.request())
        self.assertEqual(result["warnings"], [])
        self.assertNotEqual(result["plans"][0]["action"], result["plans"][1]["action"])

    def test_new_background_cannot_disguise_an_identical_performance(self):
        request = self.request()
        del request["locks"]["scene"]
        request["shots"][1] = dict(request["shots"][0])
        request["shots"][0]["scene"] = "客厅"
        request["shots"][1]["scene"] = "阳台"
        result = compose(request)
        self.assertTrue(any("performance" in w for w in result["warnings"]))

    def test_global_wardrobe_and_pose_locks_win_and_report_shot_conflicts(self):
        request = self.request()
        request["locks"]["action"] = "保持原图低头读书姿势"
        request["shots"][0]["wardrobe"] = "改穿运动服"
        result = compose(request)
        for plan in result["plans"]:
            self.assertEqual(plan["wardrobe"], "原有衬衫与长裤")
            self.assertEqual(plan["action"], "保持原图低头读书姿势")
        self.assertTrue(any("shot" in w.lower() and "wardrobe" in w for w in result["warnings"]))
        self.assertTrue(any("shot" in w.lower() and "action" in w for w in result["warnings"]))

    def test_reference_controls_win_over_authored_camera(self):
        request = self.request()
        request["reference_controls"] = {"composition": "人物偏左", "identity_anchors": "同一人物"}
        del request["locks"]["composition"]
        request["shots"][0]["composition"] = "人物偏右"
        result = compose(request)
        self.assertEqual(result["plans"][0]["composition"], "人物偏左")
        self.assertEqual(result["plans"][0]["identity_anchors"], "同一人物")
        self.assertTrue(any("shot" in w.lower() and "composition" in w for w in result["warnings"]))

    def test_authored_conflict_is_preserved_and_reported(self):
        request = {"count": 1, "seed": 7, "shots": [{
            "action": "站立", "expression": "平静直视",
            "scene": "盛夏荷塘", "lighting": "室内窗边漫射光",
        }]}
        result = compose(request)
        self.assertEqual(result["plans"][0]["scene"], "盛夏荷塘")
        self.assertEqual(result["plans"][0]["lighting"], "室内窗边漫射光")
        self.assertTrue(any("compatibility conflict" in w for w in result["warnings"]))

    def test_authored_shot_can_repair_unprotected_lens(self):
        result = compose({"count": 1, "seed": 7, "shots": [{
            "action": "全身舒适站姿伸展，双脚稳定承重", "expression": "目光追随平举指尖",
            "shot_distance": "全身",
        }], "biases": {"lens": {"28mm广角": 0, "50mm标准": 0, "85mm中长焦": 100, "200mm长焦": 0}}})
        self.assertEqual(result["plans"][0]["shot_distance"], "全身")
        self.assertEqual(result["plans"][0]["lens"], "28mm广角")
        self.assertTrue(any(r["field"] == "lens" for r in result["repairs"]))

    def test_shots_validate_count_fields_and_required_beat_pair(self):
        for shots in (None, {}, [], [{}], [{"action": "走路"}],
                      [{"action": "走路", "expression": " "}],
                      [{"action": "走路", "expression": "微笑", "weather": "晴"}]):
            with self.subTest(shots=shots):
                with self.assertRaises(ValueError):
                    compose({"count": 1, "shots": shots})

    def test_same_seed_reproduces_authored_batch(self):
        request = self.request()
        self.assertEqual(compose(request), compose(request))

    def test_reading_in_custom_study_is_not_replaced_by_hair_touching(self):
        result = compose({"count": 1, "seed": 7, "locks": {
            "scene": "家中书房", "action": "翻阅书页",
        }})
        self.assertEqual(result["plans"][0]["scene"], "家中书房")
        self.assertEqual(result["plans"][0]["action"], "翻阅书页")
        self.assertFalse(any("page-turning" in w for w in result["warnings"]))

    def test_cli_preserves_authored_beats(self):
        script = Path(__file__).resolve().parents[1] / "scripts" / "compose_plan.py"
        request = self.request()
        completed = subprocess.run(
            [sys.executable, "-B", str(script), "--request-json", json.dumps(request)],
            capture_output=True, text=True, check=True,
        )
        result = json.loads(completed.stdout)
        self.assertEqual(result["plans"][1]["expression"], request["shots"][1]["expression"])


if __name__ == "__main__":
    unittest.main()
