"""Configuration and source-aligned synthetic choices; no application imports."""
from __future__ import annotations

import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT.parent.parent / "frontend"
GOLF_ROUNDS = {1, 3, 6, 7, 8, 9}
ARM_ROUNDS = {12, 13, 14, 15}
PROFILES = ("full", "golf-only", "arm-only", "departures")
ALL_ENDPOINTS = {
    "player/host", "player/join", "player/roundResult", "player/armRoundResult",
    "player/freeRoamResult", "player/freeRoamSurvey", "player/diceResult",
    "player/remove", "player/allResults", "session/status", "session/players",
    "session/advance", "session/jumptoarmmission", "session/roundresults",
    "session/finalresults", "session/armroundresults", "session/armfinalresults",
    "session/surveyssubmitted", "session/end",
}


def inside(path: str | Path) -> Path:
    result = Path(path).resolve()
    if not result.is_relative_to(ROOT):
        raise ValueError(f"Generated files must stay inside {ROOT}: {result}")
    return result


def settings(path: str | Path | None = None, **overrides) -> dict:
    result = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    if path:
        custom = json.loads(Path(path).read_text(encoding="utf-8"))
        result["timings"].update(custom.pop("timings", {}))
        result.update(custom)
    result.update({k:v for k,v in overrides.items() if v is not None})
    for key in ("speed", "poll_seconds", "request_timeout", "max_session_seconds"):
        if not isinstance(result[key], (float, int)) or not math.isfinite(result[key]) or result[key] <= 0:
            raise ValueError(f"{key} must be a finite positive number")
    if not 0 <= result["archive_probability"] <= 1:
        raise ValueError("archive_probability must be between 0 and 1")
    if result["max_pending_polls"] < 1:
        raise ValueError("max_pending_polls must be positive")
    for key, values in result["timings"].items():
        if len(values) != 3 or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in values) or not 0 <= values[0] <= values[1] <= values[2]:
            raise ValueError(f"timings.{key} must be [minimum, mode, maximum] seconds")
    return result


def delay(config: dict, rng: random.Random, key: str, pace: float = 1) -> float:
    low, mode, high = config["timings"][key]
    return rng.triangular(low, high, mode) * pace / config["speed"]


def host_plays_dice(player_id: str) -> bool:
    return sum(map(ord, player_id)) % 2 == 0


def registration(rng: random.Random, run_id: str, index: int) -> dict:
    data = dict(name=f"LT-{run_id}-{index}", color=f"#{rng.randrange(0x1000000):06x}",
                participationReason="Synthetic performance test", gender="Prefer not to say",
                age=rng.randint(18,65), residence="United States", ethnicity="Prefer not to say",
                isCollegeStudent=rng.random()<0.65, university="Load Test University",
                degreeProgram="Synthetic Engineering", yearsInProgram=rng.randint(1,5),
                highschoolEducation="Yes: General education", bachelorsEducation="Current: Engineering",
                mastersEducation="", doctorateEducation="", otherEducation="", otherEducationName="")
    for key in ("riskAnalysisExperience", "supplierExperience", "proposalOrStatementOfWorkExperience",
                "bidsForRequestsExperience", "systemArchitectureExperience", "golfExperience",
                "systemsEngineeringExpertise", "statementOfWorkExpertise"):
        data[key] = str(rng.randint(1,7))
    return data


def reasoning(rng: random.Random) -> str:
    sentence = rng.choice([
        "I compared the component choices and balanced the expected performance against the total cost. ",
        "I selected this combination after reviewing the previous results and the current round objective. ",
        "I preferred specialized solvers for some tasks and a general solver where coordination seemed useful. ",
    ])
    return ("Synthetic load test response. " + sentence * rng.randint(1,4))[:900]


def dice_payload(rng: random.Random, player_id: str, onboarding: bool) -> dict:
    costs={6:2,8:3,10:4,12:5,20:6}
    remaining=8
    dice=[]
    while remaining >= 2:
        affordable=[d for d,c in costs.items() if c<=remaining]
        d=rng.choice(affordable)
        dice.append(d)
        remaining-=costs[d]
    if sum(dice)<12:
        dice=[6,6,6,6]
    distribution={0:1}
    for sides in dice:
        updated={}
        for total, count in distribution.items():
            for value in range(1,sides+1):
                updated[total+value]=updated.get(total+value,0)+count
        distribution=updated
    score=100*sum(count for total,count in distribution.items() if total>=12)/math.prod(dice)
    return {**{f"d{d}":dice.count(d) for d in (4,6,8,10,12,20)}, "playerId":player_id,
            "onboarding":onboarding,"score":score,"reasoning":reasoning(rng),
            **{key:"" for key in ("finalReasoning","reasoning2","reasoning3","reasoning4","reasoning5")}}
