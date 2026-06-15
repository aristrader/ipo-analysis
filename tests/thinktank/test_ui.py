import pytest
from streamlit.testing.v1 import AppTest
from unittest.mock import patch, MagicMock

# We use Streamlit's official AppTest framework to simulate user interaction programmatically
def test_ui_initial_render():
    at = AppTest.from_file("thinktank/orchestration/ui.py")
    at.run()
    
    # Assert the page title and initial text input are present
    assert not at.exception
    assert "🧠 Think Tank Control Center" in at.title[0].value
    
    # Assert the 'Run Ideation' button is present
    assert at.button[0].label == "Run Ideation"

@patch("thinktank.orchestration.nodes.ChatGoogleGenerativeAI")
def test_ui_ideation_run(mock_llm_class):
    # Mocking the JSON response expected by the UI from the Review Agent
    mock_response = MagicMock()
    mock_response.content = '[{"idea": "UI Test Idea", "status": "IN", "justification": "Looks good"}]'
    mock_instance = MagicMock()
    mock_instance.invoke.return_value = mock_response
    mock_llm_class.return_value = mock_instance

    at = AppTest.from_file("thinktank/orchestration/ui.py").run()
    
    # Simulate user typing a seed hypothesis
    at.text_input[0].input("Do IPOs underperform if they list on a Tuesday?").run()
    
    # Simulate user clicking "Run Ideation"
    at.button[0].click().run()
    
    assert not at.exception
    
    # Check if the UI correctly updated to show the Pruning Checkpoint
    assert "Checkpoint 1: Pruning & Expansion" in at.subheader[0].value
    
    # Verify a dropdown was created for the parsed item
    assert at.selectbox[0].label == "Status"
    
@patch("thinktank.orchestration.nodes.ChatGoogleGenerativeAI")
def test_ui_execution_run(mock_llm_class):
    # Mocking the responses for execution
    mock_response = MagicMock()
    mock_response.content = "Mocked execution output"
    mock_instance = MagicMock()
    mock_instance.invoke.return_value = mock_response
    mock_llm_class.return_value = mock_instance

    # We pre-load the session state to skip straight to Checkpoint 2
    at = AppTest.from_file("thinktank/orchestration/ui.py")
    
    # Inject state as if Step 1 just finished
    at.session_state["pipeline_state"] = {
        "sorted_ideas": '[{"idea": "Idea", "status": "IN", "justification": "Reason"}]',
        "prior_art_report": "Prior art"
    }
    
    at.run()
    
    # Click the "Confirm & Build Plan" button
    # at.button[1] is the confirm button since button[0] is "Run Ideation"
    assert at.button[1].label == "Confirm & Build Plan"
    at.button[1].click().run()
    
    assert not at.exception
    
    # Ensure it moved to Checkpoint 2
    assert "Checkpoint 2: Execution & Review" in at.subheader[0].value
