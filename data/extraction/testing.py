import re

text = "UTC-5(4)\\nElev 1250"  # This is a string containing: UTC-5(4)\nElev 1250

pattern = r"UTC-5\(4\\nElev 1250"  # raw string regex pattern

match = re.search(pattern, text)
if match:
    print("✅ Match found!")
else:
    print("❌ No match.")
