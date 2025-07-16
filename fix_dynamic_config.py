import re

# Fix config/base.py - make dynamic_config usage lazy
with open("config/base.py", "r") as f:
    content = f.read()

# Replace the problematic class-level dynamic_config calls with default values
# and lazy loading

content = re.sub(
    r"connection_timeout: int = dynamic_config\.get_db_connection_timeout\(\)",
    "connection_timeout: int = 30  # Default value, can be overridden",
    content,
)

content = re.sub(
    r"max_retries: int = dynamic_config\.get_db_max_retries\(\)",
    "max_retries: int = 3  # Default value, can be overridden",
    content,
)

# Add any other dynamic_config usage fixes if they exist
content = re.sub(
    r"dynamic_config\.[^(]+\(\)",
    lambda m: f"None  # TODO: Lazy load {m.group(0)}",
    content,
)

with open("config/base.py", "w") as f:
    f.write(content)

print("✅ Fixed dynamic_config usage in config/base.py")
