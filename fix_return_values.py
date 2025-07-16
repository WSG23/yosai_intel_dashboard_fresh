import re

print("Fixing return value unpacking in mde.py...")
with open("mde.py", "r") as f:
    content = f.read()

content = re.sub(
    r"upload_results, preview_components, file_info = loop\.run_until_complete\(",
    r"result_tuple = loop.run_until_complete(",
    content,
)

content = re.sub(
    r"result_tuple = loop\.run_until_complete\(\s*self\.upload_service\.process_uploaded_files\(\[contents\], \[filename\]\)\s*\)",
    """result_tuple = loop.run_until_complete(
                        self.upload_service.process_uploaded_files([contents], [filename])
                    )
                    
                    # Base code returns 7 values - extract what we need
                    logger.info(f"Upload service returned {len(result_tuple)} values")
                    upload_results, preview_components, file_info = result_tuple[0], result_tuple[1], result_tuple[2]""",
    content,
    flags=re.DOTALL,
)

with open("mde.py", "w") as f:
    f.write(content)

print("✅ Fixed return value unpacking")
