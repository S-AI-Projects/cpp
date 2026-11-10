# Sieve of Eratosthenes - C++ Hints

## Key C++ Construct: Lambda Capture and Iterators

This exercise uses a **lambda expression** with **capture by value**. Understanding this is crucial for correctly implementing the sieve algorithm.

### What is a Lambda?

A lambda (anonymous function) lets you define small functions inline:
```cpp
[n] (int x) { return x > n; }  // captures 'n', compares x against it
```

### Capture Modes Matter!

The sieve reference uses **capture by value**:
```cpp
candidates.remove_if([next](int n) { return n % next == 0; });
//     ^^^^
//    Capture 'next' BY VALUE into the lambda
```

**Why value capture?** Because `next` comes from `candidates.front()` and will change when we pop elements. If we captured by reference, the lambda would see a different value each time it's called!

### Micro-Example: Capture by Value vs Reference

```cpp
#include <iostream>
#include <vector>
using namespace std;

int main() {
    vector<int> nums = {10, 20, 30};
    
    // Capture BY VALUE (correct for our use case)
    int val = 5;
    auto func_by_value = [val](int n) { 
        cout << "By value: n / " << val << " = " << n/val << endl;
    };
    
    // Capture BY REFERENCE (dangerous here!)
    auto func_by_ref = [&val](int n) { 
        cout << "By ref: n / " << val << " = " << n/val << endl;
    };
    
    // Later... modify val after creating lambdas
    val = 2;
    
    cout << "--- Calling lambdas after changing val to 2 ---\n";
    func_by_value(10);  // Uses stored value (5): 10/5 = 2
    func_by_ref(10);    // Sees current value (2): 10/2 = 5
    
    return 0;
}
```

**Output:**
```
--- Calling lambdas after changing val to 2 ---
By value: n / 5 = 2
By ref: n / 2 = 5
```

### How This Applies to the Sieve

In the sieve algorithm:
1. We store the **current prime** (the smallest remaining candidate)
2. We need to remove all multiples of that prime
3. The lambda must use that specific prime value throughout the removal process

If we captured `next` by reference, subsequent `pop_front()` calls would change what `next` refers to, causing incorrect behavior!

### Common Pitfall

**Wrong approach (capturing by reference):**
```cpp
// DANGEROUS: next changes as we iterate
candidates.remove_if([](int n) { return n % next == 0; });
```

**Correct approach (capturing by value):**
```cpp
// SAFE: next is frozen at the current value
const int next = candidates.front();
candidates.remove_if([next](int n) { return n % next == 0; });
```

### Other Useful C++ Constructs in This Exercise

- **`std::list`** vs `std::vector`: `std::list::remove_if()` efficiently removes elements while iterating, which is perfect for the sieve
- **`const int&`** references: Used to avoid copying large objects (though not needed for `int`)
- **`std::iota`**: Fills a range with sequential values (e.g., 2, 3, 4, 5...)

See https://en.cppreference.com/w/cpp/language/lambda for more details on lambda syntax and capture semantics.