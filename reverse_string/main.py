def reverse_string(s):
    return s[::-1]

theString = "From Rich to... well, you know how these names go."
reverse_theString = reverse_string(theString)
print(f"Original String: {theString}")
print(f"Reversed String: {reverse_theString}")