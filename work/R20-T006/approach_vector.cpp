#include "resistor_color_duo.h"
#include <algorithm>
#include <string>
#include <vector>

namespace resistor_color_duo {

const std::vector<std::string> colors{
    "black", "brown", "red", "orange", "yellow",
    "green", "blue", "violet", "grey", "white"
};

int color_code(const std::string& color) {
    auto it = std::find(colors.begin(), colors.end(), color);
    return (it != colors.end()) ? static_cast<int>(std::distance(colors.begin(), it)) : -1;
}

int value(const std::vector<std::string>& bands) {
    return color_code(bands.at(0)) * 10 + color_code(bands.at(1));
}

}  // namespace resistor_color_duo
