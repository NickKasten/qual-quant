import os
import pytest

RUN_INTEGRATION = os.getenv("RUN_INTEGRATION_TESTS") == "true"
pytestmark = pytest.mark.skipif(
    not RUN_INTEGRATION,
    reason="Integration tests disabled. Set RUN_INTEGRATION_TESTS=true to enable."
)

# Placeholder integration tests retained for future end-to-end validation when enabled.
