from app.services.topic_guard import TopicGuard


def test_topic_guard_allows_persian_immigration_question() -> None:
    guard = TopicGuard()

    assert guard.is_immigration_related("برای ویزای کاری آلمان چه مدارکی لازم است؟")


def test_topic_guard_rejects_unrelated_question() -> None:
    guard = TopicGuard()

    assert not guard.is_immigration_related("بهترین فیلم امسال چیست؟")
