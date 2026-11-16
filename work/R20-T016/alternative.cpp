#include <algorithm>
#include <array>
#include <cstdlib>
#include <string>

#include "zebra_puzzle.h"

namespace zebra_puzzle {
namespace {

enum Color { Red, Green, Ivory, Yellow, Blue };
enum Nationality { Englishman, Spaniard, Ukrainian, Norwegian, Japanese };
enum Pet { Dog, Snails, Fox, Horse, Zebra };
enum Drink { Tea, Coffee, Milk, OrangeJuice, Water };
enum Hobby { Dancing, Painting, Reading, Football, Chess };

using Positions = std::array<int, 5>;

bool adjacent(int left, int right) {
    return std::abs(left - right) == 1;
}

}  // namespace

Solution solve() {
    constexpr std::array<const char*, 5> nationalities{
        "Englishman", "Spaniard", "Ukrainian", "Norwegian", "Japanese"};
    Positions color{0, 1, 2, 3, 4};

    do {
        if (color[Green] != color[Ivory] + 1) continue;

        Positions nationality{0, 1, 2, 3, 4};
        do {
            if (nationality[Norwegian] != 0 ||
                nationality[Englishman] != color[Red] ||
                !adjacent(nationality[Norwegian], color[Blue])) {
                continue;
            }

            Positions drink{0, 1, 2, 3, 4};
            do {
                if (drink[Milk] != 2 || drink[Coffee] != color[Green] ||
                    drink[Tea] != nationality[Ukrainian]) {
                    continue;
                }

                Positions pet{0, 1, 2, 3, 4};
                do {
                    if (pet[Dog] != nationality[Spaniard]) continue;

                    Positions hobby{0, 1, 2, 3, 4};
                    do {
                        if (hobby[Dancing] != pet[Snails] ||
                            hobby[Painting] != color[Yellow] ||
                            !adjacent(hobby[Reading], pet[Fox]) ||
                            !adjacent(hobby[Painting], pet[Horse]) ||
                            hobby[Football] != drink[OrangeJuice] ||
                            hobby[Chess] != nationality[Japanese]) {
                            continue;
                        }

                        Solution solution;
                        for (int person = 0; person < 5; ++person) {
                            if (nationality[person] == drink[Water]) {
                                solution.drinksWater = nationalities[person];
                            }
                            if (nationality[person] == pet[Zebra]) {
                                solution.ownsZebra = nationalities[person];
                            }
                        }
                        return solution;
                    } while (std::next_permutation(hobby.begin(), hobby.end()));
                } while (std::next_permutation(pet.begin(), pet.end()));
            } while (std::next_permutation(drink.begin(), drink.end()));
        } while (std::next_permutation(nationality.begin(), nationality.end()));
    } while (std::next_permutation(color.begin(), color.end()));

    return {};
}

}  // namespace zebra_puzzle
