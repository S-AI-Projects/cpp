#include <stack>
#include <string>

#include "matching_brackets.h"

using namespace std;

namespace matching_brackets {

// Invariant & Complexity Specification:
// Invariant:
//   A LIFO stack (`std::stack<char>`) maintains the sequence of currently unclosed
//   opening brackets ('(', '{', '['). When an opening bracket is encountered, it is
//   pushed onto the stack. When a closing bracket (')', '}', ']') is encountered,
//   the stack must not be empty and its top element must match the opening bracket
//   corresponding to that closing delimiter. Non-bracket characters are bypassed.
// Complexity:
//   - Time Complexity: O(n) where n = expression.size(). Each character is inspected
//     once; string::find over 3-character constant strings is O(1); stack push/pop/top
//     operations execute in amortized O(1) time.
//   - Space Complexity: O(n) auxiliary space in the worst case (when all characters are
//     nested opening brackets, e.g. "((((...").
bool check(string const& expression) {
    const string open("({[");
    const string close(")}]");
    stack<char> st;
    for (const char c : expression) {
        if (open.find(c) != string::npos) {
            st.push(c);
        } else if (close.find(c) != string::npos) {
            if (st.empty() || st.top() != open[close.find(c)]) {
                return false;
            }
            st.pop();
        }
    }
    return st.empty();
}

}  // namespace matching_brackets
