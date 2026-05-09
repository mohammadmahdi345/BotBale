from app.workflows.immigration import ImmigrationWorkflow


def test_workflow_adds_specialized_questions() -> None:
    workflow = ImmigrationWorkflow()
    keys = [question.key for question in workflow.questions_for("work")]

    assert "education" in keys
    assert "work_experience" in keys
    assert "job_offer" in keys


def test_workflow_returns_next_unanswered_question() -> None:
    workflow = ImmigrationWorkflow()

    question = workflow.next_question("study", {"age", "family_status"})

    assert question is not None
    assert question.key == "education"
