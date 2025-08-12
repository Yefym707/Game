from src.gamecore import i18n


def test_fallback_to_default_language():
    # Switch to a non-existent language and ensure we fall back to English
    i18n.set_language('xx')
    assert i18n.gettext(i18n.PLAY) == 'Play'
    # Restore default language for other tests
    i18n.set_language('en')
