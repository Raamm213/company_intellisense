def test_environment_heartbeat():
    """A simple test to verify that pytest and the environment are working correctly."""
    assert True


def test_imports():
    """Verify that core modules can be imported without errors."""
    try:
        import fastapi
        import langchain
        import pydantic
        import supabase

        assert True
    except ImportError as e:
        assert False, f"Import failed: {e}"
