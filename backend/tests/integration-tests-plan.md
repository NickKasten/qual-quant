# Integration Tests Improvement Plan

- [x] Update patch targets in integration tests to match the actual import paths used in the modules under test (e.g., patch 'main.fetch_ohlcv' instead of 'data.fetcher.fetch_ohlcv').
- [x] Remove unnecessary mocks (e.g., don't mock generate_signals if you want to test its real behavior).
- [ ] Ensure test data and mocks match the expected input/output types.
- [ ] Rerun integration tests and verify all pass.
