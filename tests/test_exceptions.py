"""Unit tests for pico_fastapi exceptions."""
import pytest
from pico_fastapi.exceptions import (
    PicoFastAPIError,
    NoControllersFoundError,
)


class TestPicoFastAPIError:
    """Tests for base exception class."""

    def test_is_exception_subclass(self):
        """PicoFastAPIError is an Exception subclass."""
        assert issubclass(PicoFastAPIError, Exception)

    def test_can_be_raised(self):
        """PicoFastAPIError can be raised with a message."""
        with pytest.raises(PicoFastAPIError, match="test error"):
            raise PicoFastAPIError("test error")

    def test_can_be_caught_as_exception(self):
        """PicoFastAPIError can be caught as Exception."""
        try:
            raise PicoFastAPIError("error")
        except Exception as e:
            assert isinstance(e, PicoFastAPIError)


class TestNoControllersFoundError:
    """Tests for NoControllersFoundError."""

    def test_is_pico_fastapi_error_subclass(self):
        """NoControllersFoundError is a PicoFastAPIError subclass."""
        assert issubclass(NoControllersFoundError, PicoFastAPIError)

    def test_has_descriptive_message(self):
        """Error has descriptive message about missing controllers."""
        error = NoControllersFoundError()
        msg = str(error)

        assert "No controllers were registered" in msg
        assert "controller modules are scanned" in msg

    def test_no_args_required(self):
        """NoControllersFoundError requires no arguments."""
        error = NoControllersFoundError()
        assert error is not None

    def test_can_be_caught_as_pico_fastapi_error(self):
        """NoControllersFoundError can be caught as PicoFastAPIError."""
        try:
            raise NoControllersFoundError()
        except PicoFastAPIError as e:
            assert isinstance(e, NoControllersFoundError)


class TestExceptionHierarchy:
    """Tests for exception hierarchy behavior."""

    def test_all_exceptions_catchable_with_base(self):
        """All pico-fastapi exceptions can be caught with base class."""
        exceptions = [
            PicoFastAPIError("test"),
            NoControllersFoundError(),
        ]

        for exc in exceptions:
            try:
                raise exc
            except PicoFastAPIError:
                pass  # Should be caught
            except Exception:
                pytest.fail(f"{type(exc).__name__} not caught as PicoFastAPIError")
