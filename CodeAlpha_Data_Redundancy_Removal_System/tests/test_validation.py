from app import normalize_email, normalize_text, validate_record


def test_email_normalization():
    assert normalize_email("  STUDENT@Example.COM ") == "student@example.com"


def test_text_normalization():
    assert normalize_text("  Asha   Kumar ") == "Asha Kumar"


def test_valid_record():
    assert validate_record("Asha Kumar", "asha@example.com", "AIDS") is None


def test_invalid_email():
    assert validate_record("Asha Kumar", "not-an-email", "AIDS") == "Enter a valid email address."


def test_required_fields():
    assert validate_record("", "asha@example.com", "AIDS") is not None
