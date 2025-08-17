#!/usr/bin/env python3
"""
Master test runner for all comprehensive backtesting engine tests
"""

import sys
import os
import time
from typing import List, Tuple

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import all test modules
from test_comprehensive_functionality import run_comprehensive_tests
from test_multi_symbol_integration import run_multi_symbol_tests
from test_market_regime_accuracy import run_regime_accuracy_tests
from test_complex_strategies_pnl import run_complex_strategy_tests

# Import existing test modules
from test_gamma_scalping import test_gamma_scalping_setup
from test_gamma_scalping_integration import test_gamma_scalping_integration
from test_pattern_strategies import main as run_pattern_tests
from test_pattern_integration import main as run_pattern_integration_tests


def run_existing_tests() -> bool:
    """Run existing test modules"""
    print("Running Existing Test Modules")
    print("=" * 50)
    
    success = True
    
    try:
        print("\n1. Testing Gamma Scalping Setup...")
        test_gamma_scalping_setup()
        print("✓ Gamma Scalping Setup tests passed")
    except Exception as e:
        print(f"✗ Gamma Scalping Setup tests failed: {e}")
        success = False
    
    try:
        print("\n2. Testing Gamma Scalping Integration...")
        test_gamma_scalping_integration()
        print("✓ Gamma Scalping Integration tests passed")
    except Exception as e:
        print(f"✗ Gamma Scalping Integration tests failed: {e}")
        success = False
    
    try:
        print("\n3. Testing Pattern Strategies...")
        run_pattern_tests()
        print("✓ Pattern Strategies tests passed")
    except Exception as e:
        print(f"✗ Pattern Strategies tests failed: {e}")
        success = False
    
    try:
        print("\n4. Testing Pattern Integration...")
        run_pattern_integration_tests()
        print("✓ Pattern Integration tests passed")
    except Exception as e:
        print(f"✗ Pattern Integration tests failed: {e}")
        success = False
    
    return success


def run_all_tests() -> Tuple[bool, List[str]]:
    """Run all comprehensive tests and return results"""
    print("🧪 COMPREHENSIVE BACKTESTING ENGINE TEST SUITE")
    print("=" * 80)
    print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = []
    overall_success = True
    
    # Test categories with their runner functions
    test_categories = [
        ("Existing Tests", run_existing_tests),
        ("Multi-Symbol Data Loading", run_multi_symbol_tests),
        ("Market Regime Detection Accuracy", run_regime_accuracy_tests),
        ("Complex Multi-Leg Strategy P&L", run_complex_strategy_tests),
        ("Comprehensive Functionality", run_comprehensive_tests),
    ]
    
    for category_name, test_runner in test_categories:
        print(f"\n{'='*20} {category_name} {'='*20}")
        start_time = time.time()
        
        try:
            success = test_runner()
            end_time = time.time()
            duration = end_time - start_time
            
            status = "PASSED" if success else "FAILED"
            test_results.append(f"{category_name}: {status} ({duration:.2f}s)")
            
            if not success:
                overall_success = False
                
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"ERROR in {category_name}: {e}")
            test_results.append(f"{category_name}: ERROR ({duration:.2f}s)")
            overall_success = False
    
    return overall_success, test_results


def print_test_summary(success: bool, results: List[str]):
    """Print comprehensive test summary"""
    print("\n" + "=" * 80)
    print("🏁 TEST SUITE SUMMARY")
    print("=" * 80)
    
    for result in results:
        status_icon = "✅" if "PASSED" in result else "❌" if "FAILED" in result else "⚠️"
        print(f"{status_icon} {result}")
    
    print("\n" + "-" * 80)
    
    if success:
        print("🎉 ALL TESTS PASSED! The backtesting engine is ready for production use.")
        print("\nKey functionality verified:")
        print("  ✓ Multi-symbol data loading and processing")
        print("  ✓ Market regime detection accuracy")
        print("  ✓ Dynamic parameter adjustment logic")
        print("  ✓ Complex multi-leg strategy P&L calculations")
        print("  ✓ Pattern recognition strategy signal generation")
        print("  ✓ Cross-symbol correlation and risk management")
        print("  ✓ Gamma scalping and advanced strategies")
        print("  ✓ Integration between all components")
    else:
        print("❌ SOME TESTS FAILED! Please review the failures above.")
        print("\nNext steps:")
        print("  1. Review failed test details")
        print("  2. Fix any identified issues")
        print("  3. Re-run the test suite")
        print("  4. Ensure all tests pass before production deployment")
    
    print("\n" + "=" * 80)
    print(f"Completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    """Main test execution"""
    try:
        success, results = run_all_tests()
        print_test_summary(success, results)
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test execution interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n\n💥 Unexpected error during test execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    main()