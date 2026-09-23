from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from pathlib import Path
import json
import re

BASE = Path(__file__).resolve().parent

CONFIG_PATH = BASE / "data" / "course_config.json"
KNOWLEDGE_PATH = BASE / "data" / "week3_knowledge_base.json"
ENCYCLOPEDIA_PATH = BASE / "data" / "week3_concept_encyclopedia.json"
ASSESSMENT_RUBRIC_PATH = BASE / "data" / "week3_assessment_rubric.json"
ASSESSMENT_SCAFFOLDS_PATH = BASE / "data" / "week3_assessment_scaffolds.json"

app = FastAPI(
    title="Business Analytics LMS — Week 3 Prototype"
)

app.mount(
    "/static",
    StaticFiles(directory=BASE / "static"),
    name="static"
)

templates = Jinja2Templates(
    directory=str(BASE / "templates")
)


def load_json(path: Path):
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def load_config():
    return load_json(CONFIG_PATH)


def load_knowledge():
    return load_json(KNOWLEDGE_PATH)


def load_encyclopedia():
    return load_json(ENCYCLOPEDIA_PATH)


def load_assessment_rubric():
    return load_json(ASSESSMENT_RUBRIC_PATH)


def load_assessment_scaffolds():
    return load_json(ASSESSMENT_SCAFFOLDS_PATH)


def save_config(config: dict):
    with CONFIG_PATH.open("w", encoding="utf-8") as file:
        json.dump(config, file, indent=2, ensure_ascii=False)


class ChatRequest(BaseModel):
    activity_id: str
    message: str
    mode: str = "practice"
    chat_type: str = "activity"


class ConfigRequest(BaseModel):
    config: dict


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


@app.get("/api/config")
def get_config():
    return load_config()


@app.put("/api/config")
def update_config(payload: ConfigRequest):
    save_config(payload.config)

    return {
        "ok": True,
        "message": "Saved to data/course_config.json"
    }


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9%$+.-]+", " ", text)
    return " ".join(text.split())


def direct_answer_request(message: str, knowledge: dict) -> bool:
    normalized_message = normalize(message)

    for phrase in knowledge["direct_answer_detection"]["phrases"]:
        if normalize(phrase) in normalized_message:
            return True

    return False


def find_encyclopedia_concepts(message: str, encyclopedia: dict):
    normalized_message = normalize(message)
    matches = []

    for concept in encyclopedia.get("concepts", []):
        aliases = concept.get("aliases", [])
        aliases = aliases + [concept.get("term", "")]

        matched_aliases = []

        for alias in aliases:
            normalized_alias = normalize(alias)

            if normalized_alias and normalized_alias in normalized_message:
                matched_aliases.append(alias)

        if matched_aliases:
            matches.append(
                {
                    "concept": concept,
                    "matched_aliases": matched_aliases,
                    "longest_match": max(
                        len(normalize(alias))
                        for alias in matched_aliases
                    )
                }
            )

    matches.sort(
        key=lambda item: item["longest_match"],
        reverse=True
    )

    return matches


def find_case_facts(message: str, knowledge: dict):
    normalized_message = normalize(message)
    matches = []

    for fact in knowledge["case"]["allowed_case_facts"]:
        fact_text = normalize(fact["statement"])

        fact_words = [
            word for word in fact_text.split()
            if len(word) >= 4 or any(character.isdigit() for character in word)
        ]

        hit_count = sum(
            1 for word in fact_words
            if word in normalized_message
        )

        if hit_count >= 2:
            matches.append(fact)

    return matches


def get_activity_knowledge(activity_id: str, knowledge: dict):
    activity_mapping = {
        "case": "case_conversation",
        "entry": "entry_check",
        "investigation": "assessment_1_choose_investigation",
        "evidence": "assessment_2_evidence_trail",
        "causation": "causation_challenge",
        "critique": "assessment_3_catch_problem",
        "memo": "module_end_diagnostic_memo",
        "reflection": "reflection_completion"
    }

    knowledge_key = activity_mapping.get(activity_id)

    if not knowledge_key:
        return {}

    return knowledge.get("activities", {}).get(
        knowledge_key,
        {}
    )


def contains_any(message: str, terms: list[str]) -> bool:
    normalized_message = normalize(message)

    return any(
        normalize(term) in normalized_message
        for term in terms
        if normalize(term)
    )


def evaluate_simulated_response(
    message: str,
    activity_knowledge: dict,
    knowledge: dict
):
    normalized_message = normalize(message)

    criteria = activity_knowledge.get(
        "required_elements",
        activity_knowledge.get("acceptable_elements", [])
    )

    matched_criteria = []

    signal_groups = {
        "finding": [
            "finding",
            "descriptive",
            "observation",
            "observed",
            "what happened",
            "result"
        ],
        "explanation": [
            "explanation",
            "hypothesis",
            "cause",
            "causal",
            "why",
            "reason"
        ],
        "causal_caution": [
            "cannot prove",
            "does not prove",
            "not prove",
            "association",
            "observational",
            "uncertainty",
            "alternative",
            "limitation",
            "not enough evidence"
        ],
        "comparison": [
            "compare",
            "comparison",
            "segment",
            "support contact",
            "tenure",
            "new customer",
            "premium",
            "standard"
        ],
        "evidence": [
            "evidence",
            "support",
            "weaken",
            "qualify",
            "resolution",
            "outage",
            "support cases",
            "billing",
            "19.7",
            "18.9",
            "14 800",
            "14800",
            "31 hours",
            "38"
        ],
        "memo": [
            "diagnostic question",
            "evidence",
            "uncertainty",
            "alternative",
            "consistent with",
            "strongest supported",
            "may have contributed"
        ]
    }

    for criterion in criteria:
        criterion_lower = criterion.lower()

        if (
            "finding" in criterion_lower
            or "descriptive" in criterion_lower
        ) and contains_any(normalized_message, signal_groups["finding"]):
            matched_criteria.append(criterion)

        elif (
            "explanation" in criterion_lower
            or "causal" in criterion_lower
            or "hypothesis" in criterion_lower
        ) and contains_any(normalized_message, signal_groups["explanation"]):
            matched_criteria.append(criterion)

        elif (
            "prove" in criterion_lower
            or "limitation" in criterion_lower
            or "uncertainty" in criterion_lower
            or "alternative" in criterion_lower
        ) and contains_any(normalized_message, signal_groups["causal_caution"]):
            matched_criteria.append(criterion)

        elif (
            "comparison" in criterion_lower
            or "chooses" in criterion_lower
        ) and contains_any(normalized_message, signal_groups["comparison"]):
            matched_criteria.append(criterion)

        elif (
            "evidence" in criterion_lower
            or "fact" in criterion_lower
            or "finding" in criterion_lower
        ) and contains_any(normalized_message, signal_groups["evidence"]):
            matched_criteria.append(criterion)

        elif (
            "memo" in criterion_lower
            or "diagnostic question" in criterion_lower
        ) and contains_any(normalized_message, signal_groups["memo"]):
            matched_criteria.append(criterion)

    case_facts = find_case_facts(message, knowledge)

    required_count = len(criteria)

    if required_count <= 2:
        mastery_threshold = required_count
    else:
        mastery_threshold = min(3, required_count)

    matched_criteria = list(dict.fromkeys(matched_criteria))

    return {
        "is_complete": len(matched_criteria) >= mastery_threshold,
        "matched_criteria": matched_criteria,
        "matched_case_facts": [
            fact["id"] for fact in case_facts
        ]
    }


def choose_assessment_coach_response(
    message: str,
    evaluation: dict,
    rubric: dict,
    scaffolds: dict
):
    criteria = rubric.get("criteria", [])
    matched_text = " ".join(
        evaluation.get("matched_criteria", [])
    ).lower()

    priority_criterion = None

    for criterion in criteria:
        criterion_id = criterion.get("id", "")
        criterion_label = criterion.get("label", "").lower()

        if (
            criterion_id not in matched_text
            and criterion_label not in matched_text
        ):
            priority_criterion = criterion
            break

    if priority_criterion is None and criteria:
        priority_criterion = criteria[0]

    priority_id = (
        priority_criterion.get("id", "reasoning")
        if priority_criterion
        else "reasoning"
    )

    priority_label = (
        priority_criterion.get("label", "reasoning")
        if priority_criterion
        else "reasoning"
    )

    level = "1"

    if priority_id == "causal_discipline":
        level = "3"
    elif priority_id in {
        "diagnostic_framing",
        "evidence_use",
        "next_step"
    }:
        level = "2"

    scaffold = scaffolds.get("levels", {}).get(level, {})
    scaffold_message = scaffold.get(
        "template",
        "Review your response and make one part of your reasoning more specific."
    )

    return {
        "level": int(level),
        "priority_gap": priority_label,
        "reply": (
            "Assessment-Coach feedback: Your response needs a clearer "
            + priority_label.lower()
            + " step before it can meet the assessment criteria.\n\n"
            + scaffold_message
        )
    }



def general_concept_reply(concept: dict):
    reply = concept.get(
        "plain_language_definition",
        "I found a related Week 3 concept, but no approved definition is available."
    )

    if concept.get("why_it_matters"):
        reply += (
            "\n\nWhy it matters: "
            + concept["why_it_matters"]
        )

    if concept.get("how_to_use"):
        reply += (
            "\n\nHow to use it: "
            + concept["how_to_use"]
        )

    if concept.get("general_example"):
        reply += (
            "\n\nExample: "
            + concept["general_example"]
        )

    reply += (
        "\n\nFor Week 3, use this concept to inspect evidence "
        "and explain your reasoning in your own words."
    )

    return reply


@app.post("/api/chat")
def chat(payload: ChatRequest):
    config = load_config()
    knowledge = load_knowledge()
    encyclopedia = load_encyclopedia()

    activity = next(
        (
            item for item in config["activities"]
            if item["id"] == payload.activity_id
        ),
        None
    )

    if not activity:
        return JSONResponse(
            {"error": "Activity not found"},
            status_code=404
        )

    message = payload.message.strip()

    if not message:
        return {
            "reply": (
                "Please write your response in your own words before continuing."
            ),
            "status": "needs_attempt",
            "level": 0,
            "trace": {
                "reasoning_gap": "No student attempt",
                "matched_concepts": [],
                "matched_case_facts": []
            }
        }

    if direct_answer_request(message, knowledge):
        if (
            payload.mode == "assessment"
            and activity["type"] == "assessment"
        ):
            reply = knowledge["direct_answer_detection"][
                "response_pattern_assessment"
            ]
        else:
            reply = knowledge["direct_answer_detection"][
                "response_pattern_practice"
            ]

        return {
            "reply": reply,
            "status": "redirected",
            "level": 0,
            "trace": {
                "reasoning_gap": "Direct-answer request",
                "matched_concepts": [],
                "matched_case_facts": []
            }
        }

    if payload.chat_type == "general":
        matches = find_encyclopedia_concepts(
            message,
            encyclopedia
        )

        if matches:
            top_match = matches[0]
            concept = top_match["concept"]

            return {
                "reply": general_concept_reply(concept),
                "status": "general_explanation",
                "level": 0,
                "trace": {
                    "reasoning_gap": None,
                    "matched_concepts": [concept["id"]],
                    "matched_aliases": top_match["matched_aliases"],
                    "matched_case_facts": []
                }
            }

        return {
            "reply": (
                "I do not yet have an approved Week 3 explanation for that "
                "term in this simulated encyclopedia. Try asking about analytics, "
                "churn, retention, customer segments, support contacts, outages, "
                "findings, explanations, diagnostic analytics, triangulation, "
                "evidence, association, causation, uncertainty, proportional "
                "language, diagnostic memos, or the AI coaching process."
            ),
            "status": "general_scope_limit",
            "level": 0,
            "trace": {
                "reasoning_gap": "No matching Week 3 concept",
                "matched_concepts": [],
                "matched_case_facts": []
            }
        }

    activity_knowledge = get_activity_knowledge(
        payload.activity_id,
        knowledge
    )

    evaluation = evaluate_simulated_response(
        message,
        activity_knowledge,
        knowledge
    )

    if evaluation["is_complete"]:
        return {
            "reply": activity["responses"]["correct"],
            "status": "meets_criteria",
            "level": 0,
            "trace": {
                "reasoning_gap": None,
                "matched_concepts": [],
                "matched_case_facts": evaluation[
                    "matched_case_facts"
                ],
                "matched_criteria": evaluation[
                    "matched_criteria"
                ]
            }
        }

    if activity["type"] == "assessment":
        rubric = load_assessment_rubric()
        scaffolds = load_assessment_scaffolds()

        coach_response = choose_assessment_coach_response(
            message,
            evaluation,
            rubric,
            scaffolds
        )

        return {
            "reply": coach_response["reply"],
            "status": "assessment_coach",
            "level": coach_response["level"],
            "trace": {
                "reasoning_gap": coach_response["priority_gap"],
                "matched_concepts": [],
                "matched_case_facts": evaluation[
                    "matched_case_facts"
                ],
                "matched_criteria": evaluation[
                    "matched_criteria"
                ],
                "assessment_coach": True
            }
        }


    ladder = activity_knowledge.get(
        "practice_ladder",
        activity.get("ladder", [])
    )

    level = 1
    level_message = ""

    if len(ladder) > level:
        level_message = ladder[level]
    else:
        level_message = (
            "Review the task and identify one part of your reasoning "
            "that you can make more specific."
        )

    return {
        "reply": (
            activity["responses"]["incomplete"]
            + "\n\nSupport level "
            + str(level)
            + " — "
            + level_message
        ),
        "status": "scaffold",
        "level": level,
        "trace": {
            "reasoning_gap": "Incomplete response in practice mode",
            "matched_concepts": [],
            "matched_case_facts": evaluation[
                "matched_case_facts"
            ],
            "matched_criteria": evaluation[
                "matched_criteria"
            ]
        }
    }
