"""
Minimal Streamlit stub installed into sys.modules for tests.

This allows tests to patch 'streamlit' via patch.multiple('streamlit', ...)
without requiring the real streamlit dependency. Only attributes used by
the test suite are provided. All functions are no-ops unless a trivial
return is useful for tests.
"""
from types import ModuleType, SimpleNamespace
import sys


def _noop(*args, **kwargs):
    return None


def _return_false(*args, **kwargs):
    return False


def _return_true(*args, **kwargs):
    return True


def _return_zero(*args, **kwargs):
    return 0


def _return_int_default(value=0):
    def _inner(*args, **kwargs):
        return value
    return _inner


def _make_mocks(n=3):
    return [SimpleNamespace() for _ in range(n)]


# Create a minimal 'streamlit' module
st = ModuleType("streamlit")

# Basic page and text functions
st.set_page_config = _noop # type: ignore
st.title = _noop # type: ignore
st.markdown = _noop # type: ignore
st.success = _noop # type: ignore
st.error = _noop # type: ignore
st.info = _noop # type: ignore
st.warning = _noop # type: ignore
st.subheader = _noop # type: ignore
st.caption = _noop # type: ignore
st.divider = _noop # type: ignore

# Widgets - return simple defaults so code can branch if needed
st.button = _return_false # type: ignore
st.checkbox = _return_false # type: ignore
st.text_input = (lambda *args, **kwargs: kwargs.get("value", "")) # type: ignore
st.selectbox = (lambda *args, **kwargs: kwargs.get("index", 0)) # type: ignore
st.slider = (lambda *args, **kwargs: kwargs.get("value", 0)) # type: ignore

# Layout helpers
st.columns = (lambda n=3, *args, **kwargs: _make_mocks(n)) # type: ignore
st.tabs = (lambda labels, *args, **kwargs: _make_mocks(len(labels) if hasattr(labels, "__len__") else 3)) # type: ignore

# Misc
st.metric = _noop # type: ignore
st.rerun = _noop # type: ignore
st.plotly_chart = _noop # type: ignore

# Spinner context manager
class _Spinner:
    def __init__(self, *args, **kwargs):
        pass
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False

st.spinner = _Spinner # type: ignore

# Ensure importable as 'streamlit'
sys.modules.setdefault("streamlit", st)