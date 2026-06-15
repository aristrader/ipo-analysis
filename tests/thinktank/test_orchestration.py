import pytest
from unittest.mock import patch, MagicMock
from thinktank.orchestration.state import ThinkTankState
from thinktank.orchestration.nodes import (
    step0_triage_history,
    step1_high_ideation,
    step1_5_review_agent,
    step2_execution_planning,
    step3_code_generation,
    step4_peer_review
)
from thinktank.orchestration.graph import build_graph

# We need to mock ChatGoogleGenerativeAI to avoid hitting the actual API during tests
# This saves API quota and ensures tests run instantly
@pytest.fixture
def mock_llm():
    with patch("thinktank.orchestration.nodes.ChatGoogleGenerativeAI") as mock_class:
        mock_response = MagicMock()
        mock_response.content = "Mocked LLM Response"
        
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = mock_response
        
        mock_class.return_value = mock_instance
        yield mock_class

def test_step0_triage_history(mock_llm):
    state: ThinkTankState = {"task_description": "Test Task", "messages": [], "errors": []}
    result = step0_triage_history(state)
    assert "prior_art_report" in result
    assert result["prior_art_report"] == "Mocked LLM Response"

def test_step1_high_ideation(mock_llm):
    state: ThinkTankState = {"task_description": "Test Task"}
    result = step1_high_ideation(state)
    assert "raw_ideas" in result
    assert result["raw_ideas"] == "Mocked LLM Response"

def test_step1_5_review_agent_json_output(mock_llm):
    # Mocking a specific JSON response for the review agent to ensure UI won't break
    mock_instance = mock_llm.return_value
    mock_response = MagicMock()
    mock_response.content = '[{"idea": "Test Idea", "status": "IN", "justification": "Because it makes sense"}]'
    mock_instance.invoke.return_value = mock_response

    state: ThinkTankState = {"raw_ideas": "Raw Idea Text"}
    result = step1_5_review_agent(state)
    assert "sorted_ideas" in result
    assert "Test Idea" in result["sorted_ideas"]
    assert "IN" in result["sorted_ideas"]

def test_step2_execution_planning(mock_llm):
    state: ThinkTankState = {"approved_ideas": "Idea 1"}
    result = step2_execution_planning(state)
    assert "execution_plan" in result
    assert result["execution_plan"] == "Mocked LLM Response"

def test_step3_code_generation(mock_llm):
    state: ThinkTankState = {"execution_plan": "print('hello')"}
    result = step3_code_generation(state)
    assert "code_execution_result" in result
    assert result["code_execution_result"] == "Mocked LLM Response"

def test_step4_peer_review_swarm_aggregator(mock_llm):
    state: ThinkTankState = {"code_execution_result": "print(1)", "execution_plan": "Math"}
    result = step4_peer_review(state)
    # The swarm calls invoke 3 times, we just check if it aggregates them properly
    assert "peer_review_feedback" in result
    assert "CODE AUDITOR" in result["peer_review_feedback"]
    assert "MATH AUDITOR" in result["peer_review_feedback"]
    assert "FALSIFIER" in result["peer_review_feedback"]

def test_graph_compilation():
    # Ensure the state machine compiles correctly with all edges intact
    graph = build_graph()
    assert graph is not None
