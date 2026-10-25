from app.core.config import Settings


def test_model_name_is_stripped():
    s = Settings(llm_model="  gemini-3.1-flash-lite  ", llm_api_key="x")
    assert s.llm_model == "gemini-3.1-flash-lite"


def test_base_url_gets_trailing_slash():
    s = Settings(llm_base_url="https://example.com/v1", llm_api_key="x")
    assert s.llm_base_url == "https://example.com/v1/"


def test_base_url_none_stays_none():
    s = Settings(llm_base_url=None, llm_api_key="x")
    assert s.llm_base_url is None


def test_base_url_whitespace_stripped():
    s = Settings(llm_base_url="   ", llm_api_key="x")
    assert s.llm_base_url is None
