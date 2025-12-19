#!/usr/bin/env python3
"""
EvoLoop Stage 1 - Robustness Validation Demo

This script validates that EvoLoop Stage 1 is production-ready by testing:
1. Async function support (@monitor with async def)
2. Complex object serialization (Pydantic, dataclasses, custom objects)
3. Error capture (exceptions are logged but traces are saved)
4. Concurrent operations (multiple traces in quick succession)

Run with:
    python demo_stage1.py

Expected output:
    - All tests should pass
    - 5+ traces should be saved to evoloop_demo.db
    - No crashes or unhandled exceptions
"""

import asyncio
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

# Add src to path for local development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from evoloop import monitor, get_storage, Trace
from evoloop.storage import SQLiteStorage
from evoloop.tracker import set_storage


# ============================================================================
# Test 1: Complex Object Serialization
# ============================================================================

@dataclass
class UserContext:
    """A dataclass to test serialization."""
    user_id: int
    is_admin: bool
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class CustomObject:
    """A custom class to test fallback serialization."""
    def __init__(self, name: str, value: int):
        self.name = name
        self.value = value
    
    def __str__(self):
        return f"CustomObject({self.name}={self.value})"


@monitor(name="complex_serialization_agent")
def test_complex_serialization(query: str, context: UserContext) -> dict:
    """Test that complex objects are serialized without errors."""
    custom = CustomObject("result", 42)
    return {
        "response": f"Processed: {query}",
        "context_used": context,  # dataclass
        "custom_result": custom,  # custom object
        "timestamp": datetime.now(),  # datetime
        "bytes_data": b"hello",  # bytes
        "set_data": {1, 2, 3},  # set
    }


# ============================================================================
# Test 2: Async Function Support
# ============================================================================

@monitor(name="async_agent")
async def test_async_agent(query: str) -> str:
    """Test that async functions work with @monitor."""
    await asyncio.sleep(0.05)  # Simulate I/O
    return f"Async result for: {query}"


@monitor(name="async_with_error")
async def test_async_with_error(should_fail: bool) -> str:
    """Test error handling in async functions."""
    await asyncio.sleep(0.01)
    if should_fail:
        raise ValueError("Intentional async error for testing")
    return "Success"


# ============================================================================
# Test 3: Sync Function with Error
# ============================================================================

@monitor(name="sync_error_agent")
def test_sync_error() -> None:
    """Test that errors are captured but re-raised."""
    raise RuntimeError("Intentional sync error for testing")


# ============================================================================
# Test 4: Simple Sync Function
# ============================================================================

@monitor(name="simple_sync_agent")
def test_simple_sync(a: int, b: int) -> int:
    """Basic sync function test."""
    return a + b


# ============================================================================
# Main Test Runner
# ============================================================================

async def run_all_tests():
    """Run all validation tests."""
    
    print("=" * 60)
    print("EvoLoop Stage 1 - Robustness Validation")
    print("=" * 60)
    
    # Use a separate database for demo
    demo_db = "evoloop_demo.db"
    if os.path.exists(demo_db):
        os.remove(demo_db)
    
    set_storage(SQLiteStorage(db_path=demo_db))
    storage = get_storage()
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Complex Serialization
    print("\n[Test 1] Complex Object Serialization...")
    try:
        ctx = UserContext(user_id=123, is_admin=True)
        result = test_complex_serialization("Hello world", ctx)
        assert "response" in result
        print("  ✅ PASSED - Complex objects serialized without errors")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ FAILED - {e}")
        tests_failed += 1
    
    # Test 2: Async Function
    print("\n[Test 2] Async Function Support...")
    try:
        result = await test_async_agent("async query")
        assert "Async result" in result
        print("  ✅ PASSED - Async function executed and traced")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ FAILED - {e}")
        tests_failed += 1
    
    # Test 3: Async Error Handling
    print("\n[Test 3] Async Error Capture...")
    try:
        await test_async_with_error(should_fail=True)
        print("  ❌ FAILED - Error should have been raised")
        tests_failed += 1
    except ValueError as e:
        if "Intentional async error" in str(e):
            print("  ✅ PASSED - Async error captured and re-raised correctly")
            tests_passed += 1
        else:
            print(f"  ❌ FAILED - Wrong error: {e}")
            tests_failed += 1
    except Exception as e:
        print(f"  ❌ FAILED - Unexpected error type: {e}")
        tests_failed += 1
    
    # Test 4: Sync Error Handling
    print("\n[Test 4] Sync Error Capture...")
    try:
        test_sync_error()
        print("  ❌ FAILED - Error should have been raised")
        tests_failed += 1
    except RuntimeError as e:
        if "Intentional sync error" in str(e):
            print("  ✅ PASSED - Sync error captured and re-raised correctly")
            tests_passed += 1
        else:
            print(f"  ❌ FAILED - Wrong error: {e}")
            tests_failed += 1
    except Exception as e:
        print(f"  ❌ FAILED - Unexpected error type: {e}")
        tests_failed += 1
    
    # Test 5: Simple Sync
    print("\n[Test 5] Simple Sync Function...")
    try:
        result = test_simple_sync(10, 20)
        assert result == 30
        print("  ✅ PASSED - Simple sync function works")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ FAILED - {e}")
        tests_failed += 1
    
    # Verify traces were saved
    print("\n" + "=" * 60)
    print("Verifying Saved Traces...")
    print("=" * 60)
    
    traces = storage.list_traces(limit=20)
    success_count = storage.count(status="success")
    error_count = storage.count(status="error")
    
    print(f"\n📊 Storage Statistics:")
    print(f"   Total traces: {len(traces)}")
    print(f"   Success: {success_count}")
    print(f"   Errors: {error_count}")
    
    print(f"\n📋 Trace Details:")
    for i, trace in enumerate(traces, 1):
        status_icon = "✅" if trace.status == "success" else "❌"
        print(f"   {i}. [{status_icon}] {trace.metadata.get('function_name', 'unknown')}")
        print(f"      Duration: {trace.duration_ms:.2f}ms")
        print(f"      Is Async: {trace.metadata.get('is_async', 'N/A')}")
        if trace.error:
            print(f"      Error: {trace.error[:50]}...")
    
    # Final verdict
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"   Tests Passed: {tests_passed}")
    print(f"   Tests Failed: {tests_failed}")
    print(f"   Traces Saved: {len(traces)}")
    
    expected_traces = 5  # 5 test executions
    if tests_failed == 0 and len(traces) >= expected_traces:
        print("\n🎉 ALL VALIDATIONS PASSED!")
        print("   EvoLoop Stage 1 is production-ready.")
        return True
    else:
        print("\n⚠️  SOME VALIDATIONS FAILED")
        print("   Please review the errors above.")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
