import pytest
import json
from haystack.dataclasses import ChatMessage
from chat.haystack_utils.agents import get_agent

QUESTIONS_FILE = "chat/tests/questions.json"

with open(QUESTIONS_FILE, encoding="utf-8") as f:
    test_cases = json.load(f)

@pytest.mark.asyncio
@pytest.mark.parametrize("test_case", test_cases)
async def test_gpt4o_document_qa(test_case):
    query = test_case["query"]
    user_id = test_case.get("user_id", "2")

    agent = get_agent(user_id=user_id)
    result = agent.run(messages=[ChatMessage.from_user(query)])
    last_msg = result["last_message"]
    final_answer = last_msg.text

    assert final_answer, "Brak odpowiedzi"

    # Obsługa wielu możliwych wersji oczekiwanej odpowiedzi
    expect_fragments = test_case.get("expect_any")
    if expect_fragments:
        matched = [frag for frag in expect_fragments if frag.lower() in final_answer.lower()]
        assert matched, (
            f"❌ Żaden z oczekiwanych fragmentów nie pasuje.\n"
            f"🔍 Szukano jednego z: {expect_fragments}\n"
            f"📩 Otrzymano: {final_answer[:300]}..."
        )
    else:
        expect_fragment = test_case["expect"]
        assert expect_fragment.lower() in final_answer.lower(), (
            f"❌ Oczekiwano: '{expect_fragment}',\n"
            f"📩 Otrzymano: '{final_answer[:300]}...'"
        )

    if "usage" in last_msg.meta:
        print(f"📊 Token usage: {last_msg.meta['usage']}")
