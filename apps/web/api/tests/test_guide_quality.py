"""Guide quality: prompt rules, number rounding tolerance, trimming and the removed "Based on:" line."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from api import guide_llm  # noqa: E402


def test_prompt_asks_for_a_direct_short_plain_answer_without_copied_caveats():
    prompt = guide_llm.SYSTEM_PROMPT
    assert "Answer the student's actual question in your first sentence" in prompt
    assert "80-140 words" in prompt and "16-18" in prompt and "next step" in prompt
    assert "at most ONE short caveat" in prompt
    assert "never paste caveat" in prompt
    assert "word for word" not in prompt and 'starting "Based on:"' not in prompt
    tools = guide_llm.TOOLS_PROMPT
    for name in ("get_employer", "get_career_path", "compare_roles", "search_jobs", "quant researcher"):
        assert name in tools
    assert "word for word" not in tools and "Cite which tool" not in tools
    assert "word for word" not in guide_llm._tool_system(prompt + "x")


@pytest.mark.parametrize(
    ("text", "allowed", "ok"),
    [
        ("Median pay was £53,342 a year.", {"53342"}, True),
        ("Pay grew +23.3% since 2022.", {"23.32", "2022"}, True),
        ("Pay grew 23.4% since 2022.", {"23.32", "2022"}, False),  # wrong rounding
        ("Pay grew 23.32% since 2022.", {"23.3", "2022"}, False),  # cannot invent precision
        ("Pay was about £53,342.", {"53342.4"}, True),
        ("Exposure is 1.", {"0.5444"}, False),  # small values never round to whole numbers
        ("Exposure is 0.5.", {"0.5444"}, True),
        ("Pay is £99,999.", {"53342.4", "23.32"}, False),
    ],
)
def test_number_check_accepts_correct_rounding_only(text, allowed, ok):
    assert (guide_llm.failed_check(text, allowed) is None) is ok


def test_clean_reply_drops_based_on_and_trims_to_the_last_whole_sentence():
    assert guide_llm.clean_reply("Short answer here. Based on: ONS ASHE.") == "Short answer here."
    assert guide_llm.clean_reply("Short answer.\nBased on: ONS ASHE.") == "Short answer."
    long = "A sentence of words. " * 100
    trimmed = guide_llm.clean_reply(long)
    assert len(trimmed) <= guide_llm.MAX_CHARS and trimmed.endswith("words.")
    assert guide_llm.failed_check(trimmed, set()) is None
