import json
import math
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.compose_plan import DIVERSITY_KEYS, POOLS, compose, shared_dimensions


SKILL_ROOT = Path(__file__).resolve().parents[1]
COMPOSER = SKILL_ROOT / "scripts" / "compose_plan.py"


def _compatibility_conflicts(plan):
    conflicts = []
    scene = plan["scene"]
    action = plan["action"]
    shot = plan["shot_distance"]
    lens = plan["lens"]
    camera_angle = plan["camera_angle"]
    foreground = plan["foreground"]
    lighting = plan["lighting"]

    compact_shot = str(shot).lower().replace(" ", "")
    if (
        lens == "200mm长焦"
        and ("30厘米" in compact_shot or "30cm" in compact_shot)
        and "全身" in compact_shot
    ):
        conflicts.append("lens/distance")
    if scene in {"盛夏荷塘", "傍晚海堤"} and lighting == "室内窗边漫射光":
        conflicts.append("scene/light")
    if action == "翻阅书页" and scene not in {"街角咖啡店", "旧书店窗边"}:
        conflicts.append("scene/action")
    if foreground == "荷叶虚化前景" and scene != "盛夏荷塘":
        conflicts.append("scene/lotus foreground")
    if foreground == "玻璃反光前景" and scene in {"盛夏荷塘", "傍晚海堤"}:
        conflicts.append("scene/glass foreground")

    compatible_shots = {
        "28mm广角": {"全身", "中景"},
        "50mm标准": {"中景", "近景"},
        "85mm中长焦": {"中景", "近景", "特写"},
        "200mm长焦": {"中景", "近景", "特写"},
    }
    if lens in compatible_shots and shot in {"全身", "中景", "近景", "特写"}:
        if shot not in compatible_shots[lens]:
            conflicts.append("lens/shot")
    if camera_angle == "侧后方跟拍" and action != "缓步前行":
        conflicts.append("camera/action")

    if plan["identity_policy"] == "high":
        if foreground == "枝叶遮挡前景":
            conflicts.append("identity/foreground")
        if shot in {"近景", "特写"} and camera_angle in {"低机位仰拍", "高机位俯拍"}:
            conflicts.append("identity/angle")
        if plan["photography_state"] == "轻微运动模糊":
            conflicts.append("identity/blur")
    return conflicts


class ComposePlanTests(unittest.TestCase):
    def test_same_seed_reproduces_complete_result(self):
        request = {
            "count": 4,
            "seed": 314159,
            "locks": {"scene": "盛夏荷塘"},
            "biases": {"action": {"绕过水边石阶": 4.5}},
        }
        self.assertEqual(compose(request), compose(request))

    def test_different_seeds_change_plans(self):
        first = compose({"count": 4, "seed": 314159})["plans"]
        second = compose({"count": 4, "seed": 314160})["plans"]
        self.assertNotEqual(first, second)

    def test_hard_lock_is_never_replaced(self):
        result = compose({"count": 5, "seed": 7, "locks": {"lens": "28mm广角"}})
        self.assertEqual({plan["lens"] for plan in result["plans"]}, {"28mm广角"})

    def test_unknown_lock_key_is_rejected(self):
        with self.assertRaisesRegex(ValueError, r"Unknown lock keys: weather"):
            compose({"locks": {"weather": "rain"}})

    def test_locked_physical_conflict_is_rejected(self):
        with self.assertRaisesRegex(ValueError, r"Hard conflict.*lens.*shot_distance"):
            compose(
                {
                    "locks": {
                        "lens": "200mm长焦",
                        "shot_distance": "摄影机距离人物30厘米拍摄全身",
                    }
                }
            )

    def test_batch_normally_differs_on_four_dimensions(self):
        plans = compose({"count": 8, "seed": 23})["plans"]
        for index, plan in enumerate(plans):
            for prior in plans[:index]:
                self.assertLessEqual(shared_dimensions(plan, prior), 4)

    def test_exhausted_locked_space_returns_warning(self):
        locks = {key: values[0] for key, values in POOLS.items() if key in DIVERSITY_KEYS}
        result = compose({"count": 2, "seed": 2, "locks": locks})
        self.assertTrue(result["warnings"])

    def test_custom_string_bias_can_be_selected_reproducibly(self):
        locks = {"expression": "自然微笑", "wardrobe": "亚麻衬衫与半身裙"}
        request = {
            "count": 1,
            "seed": 2,
            "locks": locks,
            "biases": {"scene": "屋顶菜园"},
        }
        self.assertEqual(compose(request)["plans"][0]["scene"], "屋顶菜园")
        self.assertEqual(compose(request), compose(request))

    def test_custom_weighted_bias_can_be_selected(self):
        locks = {"expression": "自然微笑", "wardrobe": "亚麻衬衫与半身裙"}
        result = compose(
            {
                "count": 1,
                "seed": 1,
                "locks": locks,
                "biases": {"scene": {"屋顶菜园": 100}},
            }
        )
        self.assertEqual(result["plans"][0]["scene"], "屋顶菜园")

    def test_unknown_bias_key_is_rejected(self):
        with self.assertRaisesRegex(ValueError, r"Unknown bias keys: weather"):
            compose({"biases": {"weather": "rain"}})

    def test_invalid_bias_shapes_and_weights_are_rejected(self):
        bad_biases = (
            ({"scene": ["盛夏荷塘"]}, "string or an object"),
            ({"scene": {"": 1}}, "non-empty strings"),
            ({"scene": {"屋顶菜园": True}}, "finite number"),
            ({"scene": {"屋顶菜园": "heavy"}}, "finite number"),
            ({"scene": {"屋顶菜园": -0.1}}, "between 0 and 100"),
            ({"scene": {"屋顶菜园": math.nan}}, "finite number"),
            ({"scene": {"屋顶菜园": math.inf}}, "finite number"),
            ({"scene": {"屋顶菜园": 100.01}}, "between 0 and 100"),
        )
        for biases, message in bad_biases:
            with self.subTest(biases=biases):
                with self.assertRaisesRegex(ValueError, message):
                    compose({"biases": biases})

    def test_zero_weight_excludes_a_pool_value(self):
        result = compose(
            {
                "count": 20,
                "seed": 11,
                "biases": {"scene": {"盛夏荷塘": 0}},
            }
        )
        self.assertNotIn("盛夏荷塘", {plan["scene"] for plan in result["plans"]})

    def test_count_limit_accepts_100_and_rejects_101(self):
        self.assertEqual(len(compose({"count": 100, "seed": 9})["plans"]), 100)
        with self.assertRaisesRegex(ValueError, r"count must be between 0 and 100"):
            compose({"count": 101})

    def test_seed_314159_never_returns_pond_with_indoor_window_light(self):
        plans = compose({"count": 10, "seed": 314159})["plans"]
        bad_pairs = [
            plan
            for plan in plans
            if plan["scene"] == "盛夏荷塘" and plan["lighting"] == "室内窗边漫射光"
        ]
        self.assertEqual(bad_pairs, [])

    def test_scene_light_repair_changes_only_unprotected_field_and_is_reported(self):
        locks = {key: values[0] for key, values in POOLS.items() if key != "lighting"}
        locks.update(
            {
                "scene": "盛夏荷塘",
                "shot_distance": "中景",
                "lens": "50mm标准",
                "camera_angle": "平视",
                "foreground": "荷叶虚化前景",
                "action": "整理发梢",
            }
        )
        result = compose(
            {
                "count": 1,
                "seed": 2,
                "locks": locks,
                "biases": {"lighting": {"室内窗边漫射光": 100}},
            }
        )
        self.assertEqual(result["plans"][0]["scene"], "盛夏荷塘")
        self.assertEqual(result["plans"][0]["lighting"], "柔和阴天光")
        self.assertEqual(result["repairs"][0]["field"], "lighting")

    def test_seed_zero_rechecks_light_after_protected_foreground_changes_scene(self):
        result = compose(
            {
                "count": 1,
                "seed": 0,
                "locks": {"foreground": "荷叶虚化前景"},
                "biases": {
                    "scene": {"街角咖啡店": 100},
                    "lighting": {"室内窗边漫射光": 100},
                },
            }
        )
        plan = result["plans"][0]
        self.assertEqual(plan["scene"], "盛夏荷塘")
        self.assertEqual(plan["foreground"], "荷叶虚化前景")
        self.assertEqual(plan["lighting"], "柔和阴天光")
        self.assertEqual(
            [repair["field"] for repair in result["repairs"]],
            ["scene", "lighting"],
        )
        self.assertEqual(result["warnings"], [])

    def test_scene_repairs_clearly_incompatible_action_and_foreground(self):
        locks = {
            key: values[0]
            for key, values in POOLS.items()
            if key not in {"action", "foreground"}
        }
        locks.update(
            {
                "scene": "傍晚海堤",
                "shot_distance": "中景",
                "lens": "50mm标准",
                "camera_angle": "平视",
                "lighting": "傍晚金色侧光",
            }
        )
        result = compose(
            {
                "count": 1,
                "seed": 2,
                "locks": locks,
                "biases": {
                    "action": {"翻阅书页": 100},
                    "foreground": {"荷叶虚化前景": 100},
                },
            }
        )
        plan = result["plans"][0]
        self.assertEqual(plan["action"], "望向远处")
        self.assertEqual(plan["foreground"], "无明显前景")
        self.assertEqual({repair["field"] for repair in result["repairs"]}, {"action", "foreground"})

    def test_lens_shot_camera_relationship_is_repaired_before_return(self):
        locks = {key: values[0] for key, values in POOLS.items() if key != "lens"}
        locks.update(
            {
                "scene": "街角咖啡店",
                "action": "整理发梢",
                "shot_distance": "特写",
                "camera_angle": "低机位仰拍",
                "foreground": "玻璃反光前景",
                "lighting": "柔和阴天光",
            }
        )
        result = compose(
            {
                "count": 1,
                "seed": 2,
                "locks": locks,
                "biases": {"lens": {"28mm广角": 100}},
            }
        )
        self.assertEqual(result["plans"][0]["lens"], "85mm中长焦")
        self.assertIn("lens", {repair["field"] for repair in result["repairs"]})

    def test_high_identity_repairs_occlusion_and_distorting_camera_choices(self):
        locks = {
            key: values[0]
            for key, values in POOLS.items()
            if key not in {"shot_distance", "lens", "camera_angle", "foreground"}
        }
        locks.update(
            {
                "scene": "街角咖啡店",
                "action": "整理发梢",
                "lighting": "柔和阴天光",
            }
        )
        result = compose(
            {
                "count": 1,
                "seed": 2,
                "identity_policy": "high",
                "locks": locks,
                "biases": {
                    "shot_distance": {"特写": 100},
                    "lens": {"28mm广角": 100},
                    "camera_angle": {"低机位仰拍": 100},
                    "foreground": {"枝叶遮挡前景": 100},
                },
            }
        )
        plan = result["plans"][0]
        self.assertEqual(plan["lens"], "85mm中长焦")
        self.assertEqual(plan["camera_angle"], "平视")
        self.assertEqual(plan["foreground"], "玻璃反光前景")
        self.assertEqual(plan["identity_policy"], "high")

    def test_high_identity_repair_cannot_reintroduce_pond_glass_conflict(self):
        locks = {key: values[0] for key, values in POOLS.items() if key != "foreground"}
        locks.update(
            {
                "scene": "盛夏荷塘",
                "action": "整理发梢",
                "shot_distance": "中景",
                "lens": "50mm标准",
                "camera_angle": "平视",
                "lighting": "柔和阴天光",
                "photography_state": "自然抓拍颗粒感",
            }
        )
        result = compose(
            {
                "count": 1,
                "seed": 0,
                "identity_policy": "high",
                "locks": locks,
                "biases": {"foreground": {"枝叶遮挡前景": 100}},
            }
        )
        plan = result["plans"][0]
        self.assertEqual(plan["scene"], "盛夏荷塘")
        self.assertEqual(plan["foreground"], "荷叶虚化前景")
        self.assertEqual(
            [repair["field"] for repair in result["repairs"]],
            ["foreground", "foreground"],
        )
        self.assertEqual(result["warnings"], [])

    def test_every_returned_plan_is_compatible_or_has_an_unresolved_warning(self):
        requests = (
            {"count": 10, "seed": 0, "identity_policy": "high"},
            {
                "count": 1,
                "seed": 5,
                "reference_controls": {
                    "lens": "200mm长焦",
                    "shot_distance": "摄影机距离人物30厘米拍摄全身",
                },
            },
        )
        for request in requests:
            result = compose(request)
            for plan_number, plan in enumerate(result["plans"], start=1):
                conflicts = _compatibility_conflicts(plan)
                warning_prefix = (
                    f"Plan {plan_number} has an unresolved compatibility conflict"
                )
                has_unresolved_warning = any(
                    warning_prefix in warning for warning in result["warnings"]
                )
                with self.subTest(request=request, plan=plan_number, conflicts=conflicts):
                    self.assertTrue(not conflicts or has_unresolved_warning)

    def test_reference_controls_are_in_final_plans_and_normalized_request(self):
        controls = {
            "composition": "人物位于画面右侧三分之一",
            "lighting": "傍晚逆光",
            "color_scheme": "暖灰、奶油白、暗琥珀、炭灰",
            "identity_anchors": "椭圆脸、平直发际线、银色圈形耳环",
        }
        references = {"A": ["identity"], "B": ["composition"], "C": ["lighting"]}
        result = compose(
            {
                "count": 2,
                "seed": 5,
                "mode": "generate",
                "model": "seedream",
                "aspect_ratio": "4:5",
                "reference_controls": controls,
                "references": references,
                "identity_policy": "high",
            }
        )
        for plan in result["plans"]:
            for key, value in controls.items():
                self.assertEqual(plan[key], value)
        self.assertEqual(
            result["normalized_request"],
            {
                "count": 2,
                "mode": "generate",
                "subject": "韩国 INS 风成年女性",
                "aspect_ratio": "4:5",
                "model": "seedream",
                "seed": 5,
                "locks": {},
                "biases": {},
                "references": references,
                "reference_controls": controls,
                "identity_policy": "high",
            },
        )

    def test_lock_wins_reference_control_conflict_and_warning_reports_it(self):
        result = compose(
            {
                "count": 1,
                "seed": 5,
                "locks": {"lighting": "柔和阴天光"},
                "reference_controls": {"lighting": "傍晚逆光"},
            }
        )
        self.assertEqual(result["plans"][0]["lighting"], "柔和阴天光")
        self.assertTrue(any("lighting" in warning and "reference" in warning for warning in result["warnings"]))

    def test_incompatible_reference_controls_are_preserved_and_reported(self):
        result = compose(
            {
                "count": 1,
                "seed": 5,
                "reference_controls": {
                    "lens": "200mm长焦",
                    "shot_distance": "摄影机距离人物30厘米拍摄全身",
                },
            }
        )
        plan = result["plans"][0]
        self.assertEqual(plan["lens"], "200mm长焦")
        self.assertEqual(plan["shot_distance"], "摄影机距离人物30厘米拍摄全身")
        self.assertTrue(any("unresolved" in warning for warning in result["warnings"]))

    def test_unknown_reference_control_key_is_rejected(self):
        with self.assertRaisesRegex(ValueError, r"Unknown reference control keys: weather"):
            compose({"reference_controls": {"weather": "rain"}})

    def test_cli_reports_validation_errors_without_traceback(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(COMPOSER),
                "--request-json",
                '{"count":101,"biases":{"scene":{"屋顶菜园":101}}}',
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stdout, "")
        self.assertIn("count must be between 0 and 100", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_cli_rejects_extreme_integer_weight_without_traceback(self):
        request_json = json.dumps(
            {"biases": {"scene": {"屋顶菜园": 10**1000}}},
            ensure_ascii=False,
        )
        completed = subprocess.run(
            [sys.executable, str(COMPOSER), "--request-json", request_json],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stdout, "")
        self.assertIn("weight must be between 0 and 100", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)


if __name__ == "__main__":
    unittest.main()
