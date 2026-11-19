#include <algorithm>
#include <iterator>

#include "sublist.h"

namespace sublist {
bool is_sublist(const std::vector<int>& sublist,
                const std::vector<int>& superlist) {
    // Invariant: An empty list is trivially a contiguous sublist of any list.
    // std::search finds the first contiguous occurrence of sublist within superlist.
    return std::search(superlist.begin(), superlist.end(),
                       sublist.begin(), sublist.end()) != superlist.end();
}

List_comparison sublist(const std::vector<int>& list_one,
                        const std::vector<int>& list_two) {
    if (list_one == list_two) {
        return List_comparison::equal;
    }
    if (list_one.size() < list_two.size() && is_sublist(list_one, list_two)) {
        return List_comparison::sublist;
    }
    if (list_one.size() > list_two.size() && is_sublist(list_two, list_one)) {
        return List_comparison::superlist;
    }
    return List_comparison::unequal;
}
}  // namespace sublist
