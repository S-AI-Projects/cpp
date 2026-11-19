#include "resistor_color_duo.h"
#include <string>
#include <unordered_map>
#include <vector>

namespace resistor_color_duo {

const std::unordered_map<std::string, int> color_map{
    {"black", 0}, {"brown", 1}, {"red", 2},    {"orange", 3}, {"yellow", 4},
    {"green", 5}, {"blue", 6},  {"violet", 7}, {"grey", 8},   {"white", 9}
};

int value(const std::vector<std::string>& bands) {
    return color_map.at(bands.at(0)) * 10 + color_map.at(bands.at(1));
}

}  // namespace resistor_color_duo
