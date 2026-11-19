#include "rail_fence_cipher.h"
#include <cstddef>

namespace rail_fence_cipher {

std::string encode(const std::string& plaintext, int num_rails) {
    if (num_rails <= 1) return plaintext;

    // Zigzag traversal invariant:
    // A complete zigzag cycle covers period `stride = 2 * (num_rails - 1)`.
    // For each rail r in [0, num_rails - 1]:
    // - Downward stroke character is at index `pos = r + k * stride`.
    // - Upward (diagonal) stroke character is at `next_pos = pos + stride - 2 * r`,
    //   which exists strictly for intermediate rails (0 < r < num_rails - 1).
    // Using `std::size_t` index arithmetic prevents signed overflow and bounds errors.
    const std::size_t stride = static_cast<std::size_t>(num_rails * 2 - 2);
    const std::size_t length = plaintext.size();

    std::string result(length, ' ');
    auto dst = result.begin();

    for (int rail = 0; rail < num_rails; ++rail) {
        const std::size_t r = static_cast<std::size_t>(rail);
        for (std::size_t pos = r; pos < length; pos += stride) {
            *dst++ = plaintext[pos];
            if (rail > 0 && rail < num_rails - 1) {
                const std::size_t next_pos = pos + stride - 2 * r;
                if (next_pos < length) {
                    *dst++ = plaintext[next_pos];
                }
            }
        }
    }

    return result;
}

std::string decode(const std::string& ciphertext, int num_rails) {
    if (num_rails <= 1) return ciphertext;

    const auto stride = num_rails * 2 - 2;
    const auto length = ciphertext.size();

    std::string result(length, ' ');
    auto src = ciphertext.cbegin();

    for (int rail = 0; rail < num_rails; ++rail) {
        for (size_t pos = rail; pos < length; pos += stride) {
            result[pos] = *src++;
            if (0 < rail && rail < num_rails - 1) {
                size_t next_pos = pos + stride - rail * 2;
                if (next_pos < length) result[next_pos] = *src++;
            }
        }
    }

    return result;
}

}  // namespace rail_fence_cipher
