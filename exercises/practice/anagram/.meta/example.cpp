#include <algorithm>
#include <cctype>

#include "anagram.h"

using namespace std;

namespace {

string to_lower_copy(string const& s) {
    string cpy(s);
    for (auto& c : cpy) {
        c = tolower(c);
    }
    return cpy;
}

string make_key(string const& s) {
    string key{to_lower_copy(s)};
    sort(key.begin(), key.end());
    return key;
}

bool is_anagram_candidate(string const& candidate,
                          string const& lowered_subject,
                          string const& subject_key) {
    if (candidate.length() != subject_key.length()) {
        return false;
    }
    if (to_lower_copy(candidate) == lowered_subject) {
        return false;
    }
    return make_key(candidate) == subject_key;
}

}  // namespace

namespace anagram {

anagram::anagram(string const& subject)
    : subject_(subject), key_(make_key(subject)) {}

// Invariant: a candidate matches iff it shares subject_'s case-insensitive
// letter multiset (key_) without being the same word case-insensitively.
vector<string> anagram::matches(vector<string> const& candidates) {
    const string lowered_subject = to_lower_copy(subject_);
    vector<string> result;
    for (string const& candidate : candidates) {
        if (is_anagram_candidate(candidate, lowered_subject, key_)) {
            result.push_back(candidate);
        }
    }
    return result;
}

}  // namespace anagram
