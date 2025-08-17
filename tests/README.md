# Tests Directory

This directory contains all test files for the options backtesting engine.

## Test Files

### Core Functionality Tests
- **`test_core_functionality.py`** - Basic engine functionality tests
- **`test_comprehensive_functionality.py`** - Comprehensive feature tests

### Strategy Tests
- **`test_complex_strategies_pnl.py`** - Complex strategy P&L validation
- **`test_gamma_scalping.py`** - Gamma scalping strategy tests
- **`test_gamma_scalping_integration.py`** - Gamma scalping integration tests
- **`test_pattern_strategies.py`** - Pattern recognition strategy tests
- **`test_pattern_integration.py`** - Pattern strategy integration tests

### Multi-Symbol Tests
- **`test_multi_symbol_integration.py`** - Multi-symbol functionality tests

### Market Regime Tests
- **`test_market_regime_accuracy.py`** - Market regime detection accuracy tests

### Reporting Tests
- **`test_summary_report.py`** - Reporting functionality tests

### Test Runner
- **`run_all_comprehensive_tests.py`** - Runs all tests in sequence

## Running Tests

### Run All Tests
```bash
cd tests
python run_all_comprehensive_tests.py
```

### Run Individual Tests
```bash
cd tests
python test_core_functionality.py
python test_comprehensive_functionality.py
# ... etc
```

## Test Structure

Tests are organized by functionality area and include:
- Unit tests for individual components
- Integration tests for multi-component functionality
- End-to-end tests for complete workflows
- Performance validation tests
- Accuracy verification tests

All tests include comprehensive assertions and detailed output for debugging and validation purposes.