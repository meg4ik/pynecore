<!--
---
weight: 1001
title: "AST Transformation"
description: "How PyneCore uses AST transformation to implement Pine Script behavior"
icon: "code"
date: "2025-03-31"
lastmod: "2025-03-31"
draft: false
toc: true
categories: ["Advanced", "Technical Implementation"]
tags: ["ast", "python", "transformations", "compiler", "internals"]
---
-->

# AST Transformation

## Import Hook System

The system's entry point is the import hook, which transforms Python files marked with the `@pyne` magic comment:

```python
# Import hook through importlib meta_path system
sys.meta_path.insert(0, PyneImportHook())
```

The `PyneLoader` class performs code transformation in multiple steps, applying the AST transformation chain.

## Transformation Chain

PyneCore applies several key transformations to Python code to make it behave like Pine Script:

1. **Import Lifter** - Moves function-level imports to module level
2. **Import Normalizer** - Standardizes import statements
3. **PersistentSeries Transformer** - Manages the hybrid PersistentSeries type
4. **Library Series Transformer** - Prepares library Series variables
5. **Function Isolation Transformer** - Ensures separate state for each function call
6. **Module Property Transformer** - Handles module properties
7. **Series Transformer** - Handles Series variables
8. **Persistent Transformer** - Manages persistent variables
9. **Input Transformer** - Processes input parameters
10. **Safe Convert Transformer** - Converts float()/int() calls to safe versions
11. **Safe Division Transformer** - Protects against division by zero

This order ensures that dependencies between transformations are properly handled. For example, PersistentSeries transformation must happen before both Persistent and Series transformations

Each transformation step modifies the Python AST to implement Pine Script behavior while maintaining Python syntax and readability.

## Detailed Transformation Process

### Import Lifter

The Import Lifter moves function-level imports to module level.

**Original code:**
```python
def main():
    from pynecore.lib.ta import sma
    result = sma(close, 14)
```

**Transformed code:**
```python
from pynecore.lib.ta import sma

def main():
    result = sma(close, 14)
```

Key aspects:
- Lifts all pynecore.lib related imports to module level
- Ensures imports are accessible throughout the module
- Prevents duplicate imports

### Import Normalizer

The Import Normalizer transforms all PyneCore imports to use a consistent format.

**Original code:**
```python
from pynecore.lib.ta import sma, ema
from pynecore.lib import plot, close

def main():
    plot(close)
    plot(sma(close, 14))
    plot(ema(close, 14))
```

**Transformed code:**
```python
from pynecore import lib
import pynecore.lib.ta

def main():
    lib.plot(lib.close)
    lib.plot(lib.ta.sma(lib.close, 14))
    lib.plot(lib.ta.ema(lib.close, 14))
```

Key aspects:
- Converts all lib-related imports to 'from pynecore import lib'
- Transforms variable references to use fully qualified names (lib.ta.sma)
- Maintains compatibility with wildcard imports
- Ensures consistent import style across the codebase

This is very important to make lib level properties work like `close`, `open`, `high`, `low`, `volume`, etc.
If you would use this kind of import:
```python
a = close
```
That would not work, because the value would never be updated in the next bar.
However, after using the import normalizer, it will work:
```python
a = lib.close
```
Because the module level variable changed, and we access through the lib module object.

### PersistentSeries Transformer

The PersistentSeries transformer converts the combined PersistentSeries type into separate Persistent and Series declarations.

**Original code:**
```python
ps: PersistentSeries[float] = 1
ps += 1
```

**Transformed code:**
```python
p: Persistent[float] = 1
s: Series[float] = p
s += 1
```

Key aspects:
- Splits PersistentSeries declarations into two separate declarations
- Must be applied before both Persistent and Series transformers

This makes easier to declare variables are both persistent and series.

### Library Series Transformer

The Library Series transformer prepares library Series variables (like close, open, high, etc.) for proper handling by the Series transformer.

**Original code:**
```python
lib.close[1]  # Access previous bar's close price
```

**Transformed code:**
```python
_lib_close: Series = lib.close
_lib_close[1]  # Now works with Series transformer
```

Key aspects:
- Creates local Series variables for library Series
- Prepares variables for Series transformer processing

If you import a variable from a library, it does not know if it is a series or not. But if you use
indexing (subscription) on it, it should initialize it as a series. This is needed, because the AST
transformer does not know anything about the other files just the one it is currently transforming.

### Function Isolation Transformer

The Function Isolation transformer ensures each function call gets its own isolated scope by wrapping functions with the isolate_function decorator.

**Original code:**
```python
def compute_avg(source):
    return (source + source[1]) / 2

result = compute_avg(close)
```

**Transformed code:**
```python
from pynecore.core.function_isolation import isolate_function
__scope_id__ = "8af7c21e_example.py"

def compute_avg(source):
    global __scope_id__
    return (source + source[1]) / 2

result = isolate_function(compute_avg, "main|compute_avg|0", __scope_id__)(close)
```

Key aspects:
- Wraps each function call with isolate_function
- Generates a unique call ID for each invocation
- Maintains scope hierarchy information
- Adds scope ID handling to each function
- Excludes standard library and non-transformable functions

### Module Property Transformer

The Module Property transformer handles attributes that should be called as functions based on configuration.

**Original code:**
```python
bar_index = lib.bar_index
time = lib.time
```

**Transformed code:**
```python
bar_index = lib.bar_index()
time = lib.time
```

Key aspects:
- Uses configuration to determine which attributes are properties
- Automatically adds parentheses for property calls
- Preserves normal attributes as is
- Handles dynamic cases with runtime checks

### Series Transformer

The Series transformer converts Series annotated variables in Python code into a global SeriesImpl instance with add() and set() operations.

**Original code:**
```python
s: Series[float] = close
s += 1
previous = s[1]
```

**Transformed code:**
```python
from pynecore.core.series import SeriesImpl

__series_main_s__ = SeriesImpl()
__series_function_vars__ = {'main': ['__series_main_s__']}

def main():
    s = __series_main_s__.add(close)
    s = __series_main_s__.set(s + 1)
    previous = __series_main_s__[1]
```

Key aspects:
- Creates a global SeriesImpl instance for each Series variable
- Converts assignments to add() and set() operations
- Redirects indexing operations to the global instance
- Maintains a registry of all Series variables per function scope

### Persistent Transformer

The Persistent transformer converts variables with Persistent type annotation to global variables that maintain their values across function calls.

**Original code:**
```python
p: Persistent[float] = 0
p += 1
```

**Transformed code:**
```python
__persistent_main_p__ = 0
__persistent_function_vars__ = {'main': ['__persistent_main_p__']}

def main():
    global __persistent_main_p__
    __persistent_main_p__ += 1
```

Key aspects:
- Creates a global variable for each Persistent variable
- Adds global declarations in functions
- Handles initialization for non-literal values
- Maintains a registry of all Persistent variables by scope
- Uses `·` (middle dot, U+00B7) as scope separator in variable names to avoid conflicts with underscores in function names

This is the fastest possible way to implement persistent variables.

**Important Note**: The Persistent and Series transformers use the Unicode character `·` (middle dot, U+00B7) as the internal scope separator. This prevents conflicts when function names contain underscores. For example:
- Function `f_f` in scope `main` creates variables like `__persistent_main·f_f·a__`
- This ensures proper isolation between functions with similar names

Avoid using the `·` character in function or variable names to prevent conflicts with the internal scoping system.

### Input Transformer

The Input transformer processes input parameters and adds necessary ID information.

**Original code:**
```python
@script.indicator
def main(source=lib.input.source("Source", lib.close)):
    result = source * 2
```

**Transformed code:**
```python
@script.indicator
def main(source=lib.input.source("Source", lib.close, _id="source")):
    source = getattr(lib, source, lib.na)
    result = source * 2
```

Key aspects:
- Adds _id parameter to input calls
- Adds getattr for source inputs at the start of functions
- Enables proper input parameter resolution
- Handles source inputs specially

### Safe Convert Transformer

The Safe Convert transformer replaces float() and int() calls with safe versions that handle NA values properly.

**Original code:**
```python
value = float(some_value)
number = int(another_value)
```

**Transformed code:**
```python
from pynecore.core import safe_convert

value = safe_convert.safe_float(some_value)
number = safe_convert.safe_int(another_value)
```

Key aspects:
- Converts float() and int() to safe_float() and safe_int()
- Returns NA(float) or NA(int) when TypeError occurs (e.g., from NA inputs)
- Maintains Pine Script semantics for type conversions
- Only adds import if conversion functions are actually used

### Safe Division Transformer

The Safe Division transformer converts division operations to safe alternatives that handle division by zero like Pine Script.

**Original code:**
```python
result = (close - open_) / (high - low)
ratio = value / divisor
constant = 1 / 2  # Literal division remains unchanged
```

**Transformed code:**
```python
from pynecore.core import safe_convert

result = safe_convert.safe_div(close - open_, high - low)
ratio = safe_convert.safe_div(value, divisor)
constant = 1 / 2  # Literal divisions are not transformed
```

Key aspects:
- Converts division operations (/) to safe_div() calls
- Returns NA(float) instead of raising ZeroDivisionError
- Literal divisions (e.g., 1/2) remain unchanged for performance
- Matches Pine Script behavior where division by zero returns NA
- Only adds import if division operations are actually transformed


## Example of Complete Transformation

Let's see a full example of how a simple Pyne code is transformed:

**Original Pyne Code:**
```python
"""
@pyne
"""
from pynecore import Series, Persistent
from pynecore.lib.ta import sma
from pynecore.lib import close, open_, high, low, plot

def main():
    # Persistent counter
    count: Persistent[int] = 0
    count += 1

    # Moving average calculation
    ma: Series[float] = sma(close, 14)
    
    # Safe division that could cause division by zero
    range_ratio = (close - open_) / (high - low)

    # Plot results
    plot(ma, "MA", color=lib.color.blue)
    plot(count, "Count", color=lib.color.red)
    plot(range_ratio, "Range Ratio", color=lib.color.green)
```

**Transformed Code:**
```python
"""
@pyne
"""
from pynecore import lib
import pynecore.lib.ta
from pynecore.core.series import SeriesImpl
from pynecore.core.function_isolation import isolate_function
from pynecore.core import safe_convert

# Global variables and scope ID
__scope_id__ = "8af7c21e_example.py"
__persistent_main_count__ = 0
__series_main_ma__ = SeriesImpl()
__series_main_range_ratio__ = SeriesImpl()

# Function and variable registries
__persistent_function_vars__ = {'main': ['__persistent_main_count__']}
__series_function_vars__ = {'main': ['__series_main_ma__', '__series_main_range_ratio__']}

def main():
    global __scope_id__
    global __persistent_main_count__

    # Persistent counter
    __persistent_main_count__ += 1

    # Moving average calculation
    ma = __series_main_ma__.add(isolate_function(lib.ta.sma, "main|lib.ta.sma|0", __scope_id__)(lib.close, 14))
    
    # Safe division that could cause division by zero
    range_ratio = __series_main_range_ratio__.add(safe_convert.safe_div(lib.close - lib.open_, lib.high - lib.low))

    # Plot results
    lib.plot(ma, "MA", color=lib.color.blue)
    lib.plot(__persistent_main_count__, "Count", color=lib.color.red)
    lib.plot(range_ratio, "Range Ratio", color=lib.color.green)
```

This example demonstrates how the different transformers work together to convert a simple Pyne script into equivalent Python code that provides Pine Script-like behavior through PyneCore's runtime system.