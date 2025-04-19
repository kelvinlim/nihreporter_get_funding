import re

# The raw input string containing concatenated names
raw_data = "al’Absi, Mustafaal’Absi, MustafaAnker, JustinBishop, JeffreyBishop, JeffreyCarroll, DanaCarroll, DanaCarroll, DanaCarroll, DanaConelea, ChristineConelea, ChristineConelea, ChristineFair, DamienFair, DamienFair, DamienFair, DamienGunlicks-Stoessel, MeredithGunlicks-Stoessel, MeredithKrueger, RobertKrueger, RobertKummerfeld, ErichKummerfeld, ErichKushner, MattLim, KelvinLim, KelvinLuciana, MonicaMcGue, MatthewMcMorris, BarbaraMcMorris, BarbaraMcMorris, BarbaraPeterson, CarolPeterson, CarolPiehler, TimothyRedish, A. DavidRedish, A. DavidRedish, A. DavidRinehart, LindaSchallmo, Michael-PaulSpecker, SheilaSpecker, SheilaSponheim, ScottSponheim, ScottSponheim, ScottThomas, MarkToomey, TraciVrieze, ScottVrieze, ScottWidome, RachelWilson, SyliaWilson, SyliaWilson, SyliaWilson, Sylia"

# Regex pattern to find "LastName, FirstName" segments.
# Explanation:
# ([A-Za-z’\-]+)    : Group 1 (Last Name) - Matches one or more letters, apostrophes, or hyphens.
# ,\s* : Matches a comma followed by zero or more whitespace characters.
# ([A-Za-z.\- ]+?) : Group 2 (First Name) - Matches one or more letters, periods, hyphens, or spaces (non-greedily).
# (?=...)           : Positive Lookahead - Ensures the following pattern exists but doesn't consume characters.
# [A-Z][a-z’\-]+,  : Matches the start of the next Last Name (uppercase letter followed by lowercase/apostrophe/hyphen) and a comma.
# |$                : OR matches the end of the string ($).
# This lookahead helps separate concatenated names correctly.
pattern = r"([A-Za-z’\-]+),\s*([A-Za-z.\- ]+?)(?=[A-Z][a-z’\-]+,|$)"

# Find all occurrences matching the pattern in the raw data
matches = re.findall(pattern, raw_data)

# Initialize an empty list to store the name tuples (including duplicates initially)
name_list_with_duplicates = []

# Process each match found by the regex
for last_name, first_name in matches:
    # Strip leading/trailing whitespace from both names
    clean_last_name = last_name.strip()
    clean_first_name = first_name.strip()
    # Create a tuple and append it to the list
    name_list_with_duplicates.append((clean_last_name, clean_first_name))

# --- Remove duplicates while preserving order ---
unique_name_list = []
seen_names = set() # Keep track of names already added

for name_tuple in name_list_with_duplicates:
    if name_tuple not in seen_names:
        unique_name_list.append(name_tuple)
        seen_names.add(name_tuple)
# --- End of duplicate removal ---

# Print the resulting list of unique tuples
print(unique_name_list)

# Optional: Print formatted output for better readability
# print("\nFormatted Unique List:")
# for last, first in unique_name_list:
#     print(f"('{last}', '{first}')")

# Optional: Print the number of unique names found
# print(f"\nFound {len(unique_name_list)} unique names.")
