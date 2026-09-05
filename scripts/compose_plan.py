"""Compose reproducible candid-photography plan records using only the standard library."""

from __future__ import annotations

import argparse
import json
import math
import random
import secrets
import sys
from typing import Any


VERSION = "4"
MAX_COUNT = 100
MAX_WEIGHT = 100
MAX_ATTEMPTS = 100
MAX_COMPATIBILITY_PASSES = 8

POOLS = {
    "expression": ["自然微笑", "专注侧望", "放松平静", "回眸一瞬"],
    "wardrobe": ["亚麻衬衫与半身裙", "针织上衣与牛仔裤", "轻薄连衣裙", "宽松风衣"],
    "scene": ["盛夏荷塘", "街角咖啡店", "旧书店窗边", "傍晚海堤"],
    "action": ["整理发梢", "缓步前行", "翻阅书页", "望向远处"],
    "shot_distance": ["全身", "中景", "近景", "特写"],
    "lens": ["28mm广角", "50mm标准", "85mm中长焦", "200mm长焦"],
    "camera_angle": ["平视", "低机位仰拍", "高机位俯拍", "侧后方跟拍"],
    "composition": ["三分法留白", "中央对称", "框景构图", "对角线构图"],
    "foreground": ["荷叶虚化前景", "玻璃反光前景", "枝叶遮挡前景", "无明显前景"],
    "lighting": ["柔和阴天光", "午后侧逆光", "室内窗边漫射光", "傍晚金色侧光"],
    "color_scheme": ["低饱和青绿与米白", "暖棕与墨蓝", "灰粉与奶油白", "日落橙与深蓝"],
    "photography_state": ["自然抓拍颗粒感", "轻微运动模糊", "真实胶片质感", "纪实瞬间感"],
}

DIVERSITY_KEYS = (
    "scene",
    "action",
    "shot_distance",
    "lens",
    "camera_angle",
    "composition",
    "foreground",
    "lighting",
)

REFERENCE_ONLY_KEYS = {"identity_anchors"}
CONTROL_KEYS = set(POOLS) | REFERENCE_ONLY_KEYS

SCENE_LIGHT_FALLBACK = {
    "盛夏荷塘": "柔和阴天光",
    "傍晚海堤": "傍晚金色侧光",
}
LIGHT_SCENE_FALLBACK = {"室内窗边漫射光": "旧书店窗边"}
SCENE_ACTION_FALLBACK = {
    "盛夏荷塘": "整理发梢",
    "傍晚海堤": "望向远处",
}
SCENE_FOREGROUND_FALLBACK = {
    "街角咖啡店": "玻璃反光前景",
    "旧书店窗边": "玻璃反光前景",
    "傍晚海堤": "无明显前景",
}
LENS_SHOTS = {
    "28mm广角": {"全身", "中景"},
    "50mm标准": {"中景", "近景"},
    "85mm中长焦": {"中景", "近景", "特写"},
    "200mm长焦": {"中景", "近景", "特写"},
}
SHOT_LENS_FALLBACK = {
    "全身": "28mm广角",
    "中景": "50mm标准",
    "近景": "85mm中长焦",
    "特写": "85mm中长焦",
}
LENS_SHOT_FALLBACK = {
    "28mm广角": "中景",
    "50mm标准": "近景",
    "85mm中长焦": "近景",
    "200mm长焦": "近景",
}


def _require_object(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def _validate_text_mapping(
    mapping: dict[str, Any], name: str, allowed_keys: set[str]
) -> None:
    unknown_keys = sorted(set(mapping) - allowed_keys)
    if unknown_keys:
        raise ValueError(f"Unknown {name} keys: {', '.join(unknown_keys)}")
    for key, value in mapping.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name}.{key} must be a non-empty string")


def _is_close_full_body(value: Any) -> bool:
    compact = str(value).lower().replace(" ", "")
    return ("30厘米" in compact or "30cm" in compact) and "全身" in compact


def _is_hard_lens_distance_conflict(fields: dict[str, Any]) -> bool:
    return fields.get("lens") == "200mm长焦" and _is_close_full_body(
        fields.get("shot_distance")
    )


def _validate_locks(locks: dict[str, Any]) -> None:
    _validate_text_mapping(locks, "lock", set(POOLS))
    if _is_hard_lens_distance_conflict(locks):
        conflict = tuple(
            sorted(
                (
                    ("lens", locks["lens"]),
                    ("shot_distance", locks["shot_distance"]),
                )
            )
        )
        raise ValueError(f"Hard conflict: {conflict}")


def _validate_biases(biases: dict[str, Any]) -> None:
    unknown_keys = sorted(set(biases) - set(POOLS))
    if unknown_keys:
        raise ValueError(f"Unknown bias keys: {', '.join(unknown_keys)}")

    for key, bias in biases.items():
        if isinstance(bias, str):
            if not bias.strip():
                raise ValueError(f"biases.{key} must be a non-empty string")
            continue
        if not isinstance(bias, dict):
            raise ValueError(f"biases.{key} must be a string or an object of value weights")
        for value, weight in bias.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"biases.{key} values must be non-empty strings")
            if not isinstance(weight, (int, float)) or isinstance(weight, bool):
                raise ValueError(f"biases.{key}.{value} weight must be a finite number")
            if isinstance(weight, float) and not math.isfinite(weight):
                raise ValueError(f"biases.{key}.{value} weight must be a finite number")
            if weight < 0 or weight > MAX_WEIGHT:
                raise ValueError(
                    f"biases.{key}.{value} weight must be between 0 and {MAX_WEIGHT}"
                )

        effective = {value: 1.0 for value in POOLS[key]}
        effective.update(bias)
        if not any(weight > 0 for weight in effective.values()):
            raise ValueError(f"biases.{key} must leave at least one positive weight")


def _choice_for(key: str, biases: dict[str, Any], randomizer: random.Random) -> str:
    values = list(POOLS[key])
    weights = [1.0] * len(values)
    bias = biases.get(key)

    if isinstance(bias, str):
        if bias in values:
            weights[values.index(bias)] += 2.0
        else:
            values.append(bias)
            weights.append(3.0)
    elif isinstance(bias, dict):
        for value, weight in bias.items():
            if value in values:
                weights[values.index(value)] = float(weight)
            else:
                values.append(value)
                weights.append(float(weight))

    return randomizer.choices(values, weights=weights, k=1)[0]


def _make_plan(
    randomizer: random.Random,
    locks: dict[str, Any],
    reference_controls: dict[str, Any],
    biases: dict[str, Any],
) -> dict[str, Any]:
    plan = {
        key: (
            locks[key]
            if key in locks
            else reference_controls[key]
            if key in reference_controls
            else _choice_for(key, biases, randomizer)
        )
        for key in POOLS
    }
    for key in REFERENCE_ONLY_KEYS:
        if key in reference_controls:
            plan[key] = reference_controls[key]
    return plan


def _append_unique(items: list[str], message: str) -> None:
    if message not in items:
        items.append(message)


def _replace_unprotected(
    plan: dict[str, Any],
    field: str,
    replacement: str,
    reason: str,
    protected: set[str],
    plan_number: int,
    repairs: list[dict[str, Any]],
    warnings: list[str],
) -> bool:
    previous = plan[field]
    if previous == replacement:
        return True
    if field in protected:
        _append_unique(
            warnings,
            f"Plan {plan_number} has an unresolved compatibility conflict ({reason}); "
            f"protected {field}={previous!r} was retained.",
        )
        return False
    plan[field] = replacement
    repairs.append(
        {
            "plan": plan_number,
            "field": field,
            "from": previous,
            "to": replacement,
            "reason": reason,
        }
    )
    return True


def _repair_pair(
    plan: dict[str, Any],
    first_field: str,
    first_replacement: str,
    second_field: str,
    second_replacement: str,
    reason: str,
    protected: set[str],
    plan_number: int,
    repairs: list[dict[str, Any]],
    warnings: list[str],
) -> None:
    if first_field not in protected:
        _replace_unprotected(
            plan,
            first_field,
            first_replacement,
            reason,
            protected,
            plan_number,
            repairs,
            warnings,
        )
    elif second_field not in protected:
        _replace_unprotected(
            plan,
            second_field,
            second_replacement,
            reason,
            protected,
            plan_number,
            repairs,
            warnings,
        )
    else:
        _append_unique(
            warnings,
            f"Plan {plan_number} has an unresolved compatibility conflict ({reason}); "
            f"protected {first_field}={plan[first_field]!r} and "
            f"{second_field}={plan[second_field]!r} were retained.",
        )


def _repair_compatibility_pass(
    plan: dict[str, Any],
    protected: set[str],
    identity_policy: str,
    plan_number: int,
) -> tuple[list[dict[str, Any]], list[str]]:
    repairs: list[dict[str, Any]] = []
    warnings: list[str] = []

    if _is_hard_lens_distance_conflict(plan):
        _repair_pair(
            plan,
            "shot_distance",
            "近景",
            "lens",
            "28mm广角",
            "200mm at 30 cm cannot frame a full body",
            protected,
            plan_number,
            repairs,
            warnings,
        )

    scene = plan["scene"]
    light = plan["lighting"]
    if scene in {"盛夏荷塘", "傍晚海堤"} and light == "室内窗边漫射光":
        _repair_pair(
            plan,
            "lighting",
            SCENE_LIGHT_FALLBACK[scene],
            "scene",
            LIGHT_SCENE_FALLBACK[light],
            "outdoor scene cannot use indoor window light",
            protected,
            plan_number,
            repairs,
            warnings,
        )

    scene = plan["scene"]
    if plan["action"] == "翻阅书页" and scene in SCENE_ACTION_FALLBACK:
        _repair_pair(
            plan,
            "action",
            SCENE_ACTION_FALLBACK.get(scene, "整理发梢"),
            "scene",
            "旧书店窗边",
            "page-turning needs a scene that plausibly contains reading material",
            protected,
            plan_number,
            repairs,
            warnings,
        )

    scene = plan["scene"]
    foreground = plan["foreground"]
    if foreground == "荷叶虚化前景" and scene != "盛夏荷塘":
        _repair_pair(
            plan,
            "foreground",
            SCENE_FOREGROUND_FALLBACK.get(scene, "无明显前景"),
            "scene",
            "盛夏荷塘",
            "lotus-leaf foreground requires a lotus-pond scene",
            protected,
            plan_number,
            repairs,
            warnings,
        )
    elif foreground == "玻璃反光前景" and scene in {"盛夏荷塘", "傍晚海堤"}:
        _repair_pair(
            plan,
            "foreground",
            "荷叶虚化前景" if scene == "盛夏荷塘" else "无明显前景",
            "scene",
            "街角咖啡店",
            "glass-reflection foreground needs a motivated glass surface",
            protected,
            plan_number,
            repairs,
            warnings,
        )

    lens = plan["lens"]
    shot = plan["shot_distance"]
    if lens in LENS_SHOTS and shot in SHOT_LENS_FALLBACK and shot not in LENS_SHOTS[lens]:
        _repair_pair(
            plan,
            "lens",
            SHOT_LENS_FALLBACK[shot],
            "shot_distance",
            LENS_SHOT_FALLBACK[lens],
            "lens character and shot distance are incompatible",
            protected,
            plan_number,
            repairs,
            warnings,
        )

    if plan["camera_angle"] == "侧后方跟拍" and plan["action"] != "缓步前行":
        _repair_pair(
            plan,
            "camera_angle",
            "平视",
            "action",
            "缓步前行",
            "a following camera position needs a moving action",
            protected,
            plan_number,
            repairs,
            warnings,
        )

    if identity_policy == "high":
        if plan["foreground"] == "枝叶遮挡前景":
            _replace_unprotected(
                plan,
                "foreground",
                "玻璃反光前景",
                "high identity protection avoids facial obstruction",
                protected,
                plan_number,
                repairs,
                warnings,
            )
        if plan["shot_distance"] in {"近景", "特写"} and plan["camera_angle"] in {
            "低机位仰拍",
            "高机位俯拍",
        }:
            _repair_pair(
                plan,
                "camera_angle",
                "平视",
                "shot_distance",
                "中景",
                "high identity protection avoids extreme close-view angle distortion",
                protected,
                plan_number,
                repairs,
                warnings,
            )
        if plan["photography_state"] == "轻微运动模糊":
            _replace_unprotected(
                plan,
                "photography_state",
                "自然抓拍颗粒感",
                "high identity protection keeps identity anchors sharp",
                protected,
                plan_number,
                repairs,
                warnings,
            )

    return repairs, warnings


def _compatibility_conflicts(
    plan: dict[str, Any], identity_policy: str
) -> list[tuple[str, tuple[str, ...]]]:
    conflicts: list[tuple[str, tuple[str, ...]]] = []

    if _is_hard_lens_distance_conflict(plan):
        conflicts.append(
            (
                "200mm at 30 cm cannot frame a full body",
                ("lens", "shot_distance"),
            )
        )

    scene = plan["scene"]
    light = plan["lighting"]
    if scene in {"盛夏荷塘", "傍晚海堤"} and light == "室内窗边漫射光":
        conflicts.append(
            (
                "outdoor scene cannot use indoor window light",
                ("scene", "lighting"),
            )
        )

    if plan["action"] == "翻阅书页" and scene in SCENE_ACTION_FALLBACK:
        conflicts.append(
            (
                "page-turning needs a scene that plausibly contains reading material",
                ("scene", "action"),
            )
        )

    foreground = plan["foreground"]
    if foreground == "荷叶虚化前景" and scene != "盛夏荷塘":
        conflicts.append(
            (
                "lotus-leaf foreground requires a lotus-pond scene",
                ("scene", "foreground"),
            )
        )
    elif foreground == "玻璃反光前景" and scene in {"盛夏荷塘", "傍晚海堤"}:
        conflicts.append(
            (
                "glass-reflection foreground needs a motivated glass surface",
                ("scene", "foreground"),
            )
        )

    lens = plan["lens"]
    shot = plan["shot_distance"]
    if lens in LENS_SHOTS and shot in SHOT_LENS_FALLBACK and shot not in LENS_SHOTS[lens]:
        conflicts.append(
            (
                "lens character and shot distance are incompatible",
                ("lens", "shot_distance"),
            )
        )

    if plan["camera_angle"] == "侧后方跟拍" and plan["action"] != "缓步前行":
        conflicts.append(
            (
                "a following camera position needs a moving action",
                ("camera_angle", "action"),
            )
        )

    if identity_policy == "high":
        if foreground == "枝叶遮挡前景":
            conflicts.append(
                (
                    "high identity protection avoids facial obstruction",
                    ("foreground",),
                )
            )
        if shot in {"近景", "特写"} and plan["camera_angle"] in {
            "低机位仰拍",
            "高机位俯拍",
        }:
            conflicts.append(
                (
                    "high identity protection avoids extreme close-view angle distortion",
                    ("shot_distance", "camera_angle"),
                )
            )
        if plan["photography_state"] == "轻微运动模糊":
            conflicts.append(
                (
                    "high identity protection keeps identity anchors sharp",
                    ("photography_state",),
                )
            )

    return conflicts


def _repair_compatibility(
    plan: dict[str, Any],
    protected: set[str],
    identity_policy: str,
    plan_number: int,
) -> tuple[list[dict[str, Any]], list[str]]:
    repairs: list[dict[str, Any]] = []
    warnings: list[str] = []
    converged = False

    for _ in range(MAX_COMPATIBILITY_PASSES):
        before = tuple(plan[key] for key in POOLS)
        pass_repairs, pass_warnings = _repair_compatibility_pass(
            plan, protected, identity_policy, plan_number
        )
        repairs.extend(pass_repairs)
        for warning in pass_warnings:
            _append_unique(warnings, warning)
        if tuple(plan[key] for key in POOLS) == before:
            converged = True
            break

    if not converged:
        _append_unique(
            warnings,
            f"Plan {plan_number} compatibility repair did not converge after "
            f"{MAX_COMPATIBILITY_PASSES} passes; final invariants are reported below.",
        )

    for reason, fields in _compatibility_conflicts(plan, identity_policy):
        warning_prefix = (
            f"Plan {plan_number} has an unresolved compatibility conflict ({reason})"
        )
        if any(warning.startswith(warning_prefix) for warning in warnings):
            continue
        values = " and ".join(f"{field}={plan[field]!r}" for field in fields)
        _append_unique(
            warnings,
            f"{warning_prefix}; final {values} were retained.",
        )

    return repairs, warnings


def shared_dimensions(a: dict, b: dict) -> int:
    """Return how many of the eight diversity dimensions two plans share."""
    return sum(key in a and key in b and a[key] == b[key] for key in DIVERSITY_KEYS)


def _is_diverse(candidate: dict[str, Any], plans: list[dict[str, Any]]) -> bool:
    return all(shared_dimensions(candidate, plan) <= 4 for plan in plans)


def _normalized_request(request: dict[str, Any]) -> dict[str, Any]:
    count = request.get("count", 10)
    if (
        not isinstance(count, int)
        or isinstance(count, bool)
        or count < 0
        or count > MAX_COUNT
    ):
        raise ValueError(f"count must be between 0 and {MAX_COUNT}")

    locks = _require_object(request.get("locks", {}), "locks")
    _validate_locks(locks)
    biases = _require_object(request.get("biases", {}), "biases")
    _validate_biases(biases)
    reference_controls = _require_object(
        request.get("reference_controls", {}), "reference_controls"
    )
    _validate_text_mapping(reference_controls, "reference control", CONTROL_KEYS)

    seed = request.get("seed")
    if seed is None:
        seed = secrets.randbits(63)
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("seed must be an integer")

    mode = request.get("mode", "prompt")
    if not isinstance(mode, str) or mode.lower() not in {"prompt", "generate"}:
        raise ValueError("mode must be prompt or generate")
    model = request.get("model", "generic")
    if not isinstance(model, str) or not model.strip():
        raise ValueError("model must be a non-empty string")
    subject = request.get("subject", "韩国 INS 风成年女性")
    if not isinstance(subject, str) or not subject.strip():
        raise ValueError("subject must be a non-empty string")
    aspect_ratio = request.get("aspect_ratio", "unspecified")
    if not isinstance(aspect_ratio, str) or not aspect_ratio.strip():
        raise ValueError("aspect_ratio must be a non-empty string")
    identity_policy = request.get("identity_policy", "balanced")
    if identity_policy not in {"balanced", "high"}:
        raise ValueError("identity_policy must be balanced or high")
    references = request.get("references", {})
    if not isinstance(references, (dict, list)):
        raise ValueError("references must be an object or array")

    shots = request.get("shots")
    if "shots" in request:
        if not isinstance(shots, list) or len(shots) != count:
            raise ValueError("shots must be an array with exactly count entries")
        for index, shot in enumerate(shots, start=1):
            _require_object(shot, f"shot {index}")
            _validate_text_mapping(shot, f"shot {index}", set(POOLS))
            if not {"action", "expression"} <= set(shot):
                raise ValueError(f"shot {index} requires action and expression")

    normalized = {
        "count": count,
        "mode": mode.lower(),
        "subject": subject,
        "aspect_ratio": aspect_ratio,
        "model": model.lower(),
        "seed": seed,
        "locks": dict(locks),
        "biases": dict(biases),
        "references": references.copy(),
        "reference_controls": dict(reference_controls),
        "identity_policy": identity_policy,
    }
    if shots is not None:
        normalized["shots"] = [dict(shot) for shot in shots]
    return normalized


def compose(request: dict) -> dict:
    """Return a normalized request plus final reproducible photography plans."""
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    normalized = _normalized_request(request)
    count = normalized["count"]
    locks = normalized["locks"]
    biases = normalized["biases"]
    reference_controls = normalized["reference_controls"]
    identity_policy = normalized["identity_policy"]
    randomizer = random.Random(normalized["seed"])
    protected = set(locks) | set(reference_controls)
    shots = normalized.get("shots")

    warnings: list[str] = []
    for key in sorted(set(locks) & set(reference_controls)):
        if locks[key] != reference_controls[key]:
            warnings.append(
                f"Reference control conflict for {key}: user lock {locks[key]!r} "
                f"overrides reference value {reference_controls[key]!r}."
            )

    plans: list[dict[str, Any]] = []
    repairs: list[dict[str, Any]] = []
    for plan_index in range(count):
        shot = shots[plan_index] if shots is not None else {}
        for key in sorted(set(shot) & protected):
            effective = locks.get(key, reference_controls.get(key))
            if shot[key] != effective:
                warnings.append(
                    f"Shot {plan_index + 1} control conflict for {key}: "
                    f"shared lock/reference {effective!r} overrides shot {shot[key]!r}."
                )
        # A shot is one authored performance, not independently sampled limbs.
        # Shared user/reference controls outrank it; compatibility cannot erase it.
        plan_controls = {**shot, **reference_controls}
        plan_protected = protected | set(shot)
        candidate: dict[str, Any] | None = None
        candidate_repairs: list[dict[str, Any]] = []
        candidate_warnings: list[str] = []
        for _ in range(MAX_ATTEMPTS):
            candidate = _make_plan(randomizer, locks, plan_controls, biases)
            candidate_repairs, candidate_warnings = _repair_compatibility(
                candidate, plan_protected, identity_policy, plan_index + 1
            )
            if shots is not None or _is_diverse(candidate, plans):
                break
        else:
            warnings.append(
                f"Plan {plan_index + 1} could not meet the four-dimension diversity target "
                f"after {MAX_ATTEMPTS} attempts; retained protected controls."
            )

        assert candidate is not None
        if shots is not None and any(
            all(candidate[key] == prior[key] for key in ("action", "expression"))
            for prior in plans
        ):
            warnings.append(
                f"Plan {plan_index + 1} repeats an authored performance "
                "(action and expression); changing the background is not performance diversity."
            )
        candidate["subject"] = normalized["subject"]
        candidate["identity_policy"] = identity_policy
        plans.append(candidate)
        repairs.extend(candidate_repairs)
        for warning in candidate_warnings:
            _append_unique(warnings, warning)

    return {
        "version": VERSION,
        "seed": normalized["seed"],
        "normalized_request": normalized,
        "plans": plans,
        "repairs": repairs,
        "warnings": warnings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compose deterministic final photography plans as JSON."
    )
    parser.add_argument("--request-json", required=True, help="JSON request object")
    args = parser.parse_args(argv)
    try:
        request = json.loads(args.request_json)
        result = compose(request)
    except (json.JSONDecodeError, ValueError, OverflowError) as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
