import gmpy2
from gmpy2 import mpz, mpfr, get_context
import math
import os

def compute_pi(digits):
    # Set precision with extra buffer to avoid rounding issues
    get_context().precision = int(digits * 3.5)

    def bs(a, b):
        """Binary splitting for Chudnovsky algorithm"""
        if b - a == 1:
            if a == 0:
                P = Q = mpz(1)
            else:
                P = mpz((6*a - 5)*(2*a - 1)*(6*a - 1))
                Q = mpz(a*a*a * 640320**3 // 24)
            T = P * (13591409 + 545140134 * a)
            if a % 2:
                T = -T
            return P, Q, T
        else:
            m = (a + b) // 2
            P1, Q1, T1 = bs(a, m)
            P2, Q2, T2 = bs(m, b)
            return P1 * P2, Q1 * Q2, T1 * Q2 + T2 * P1

    # Each term contributes ~14.181647 digits
    DIGITS_PER_TERM = math.log10((640320**3) / 24 / 6 / 2 / math.pi)
    terms = int(digits / DIGITS_PER_TERM) + 1

    # Compute the series
    P, Q, T = bs(0, terms)

    # Final multiplication
    C = mpfr(426880) * gmpy2.sqrt(mpfr(10005))
    pi = C * Q / T

    return str(pi)[:digits + 2]  # 3. + digits

if __name__ == "__main__":
    digits = int(input("Enter number of digits to calculate for Pi: "))
    print("Calculating...")

    pi_str = compute_pi(digits)
    
    filename = f"pi_{digits}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(pi_str)

    print(f"\nPi to {digits} digits saved to '{filename}'.")
