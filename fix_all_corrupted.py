# ""
# Automated corruption fixer for ApplySense-AI project.
# Scans all source files and converts any that are stored as escaped strings
# back into proper multi-line source code.
# """
# import os
# import re
# import json

# PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# # Extensions to scan
# EXTENSIONS = {
#     '.py', '.ts', '.tsx', '.js', '.jsx', '.json', '.css', '.html',
#     '.yml', '.yaml', '.md', '.env', '.txt', '.mjs', '.cjs',
# }

# # Directories to skip
# SKIP_DIRS = {'node_modules', '.git', '__pycache__', '.venv', 'venv', 'dist', 'build'}

# def is_corrupted(content: str) -> bool:
#     """Check if the file content is stored as an escaped string."""
#     stripped = content.strip()
#     # Pattern 1: Entire file wrapped in double quotes with 

#     if stripped.startswith('"') and '
# ' in stripped:
#         return True
#     # Pattern 2: Entire file wrapped in single quotes with 

#     if stripped.startswith("'") and '
# ' in stripped:
#         return True
#     return False

# def fix_content(content: str) -> str:
#     """Unescape a corrupted file back to normal source code."""
#     stripped = content.strip()
    
#     # Remove leading/trailing quotes
#     if stripped.startswith('"'):
#         # Find the last quote
#         stripped = stripped[1:]
#         if stripped.endswith('"'):
#             stripped = stripped[:-1]
#     elif stripped.startswith("'"):
#         stripped = stripped[1:]
#         if stripped.endswith("'"):
#             stripped = stripped[:-1]
    
#     # Unescape in the correct order
#     # First handle \" -> "
#     result = stripped.replace('\"', '"')
#     # Handle \' -> '
#     result = result.replace("\'", "'")
#     # Handle \
#  -> real newline (escaped backslash + n in source)
#     result = result.replace('\
# ', '
# ')
#     # Handle 
#  -> real newline
#     result = result.replace('
# ', '
# ')
#     # Handle \	 -> real tab
#     result = result.replace('\	', '	')
#     # Handle \ -> remove (we'll use 
# )
#     result = result.replace('\', '')
#     # Handle remaining \\ -> single backslash
#     result = result.replace('\\', '\')
    
#     # Clean up any double-blank lines from 
#  conversion
#     while '

# ' in result:
#         result = result.replace('

# ', '

# ')
    
#     return result.strip() + '
# '

# def scan_and_fix():
#     """Walk the project tree and fix all corrupted files."""
#     fixed_files = []
#     scanned = 0
    
#     for root, dirs, files in os.walk(PROJECT_ROOT):
#         # Skip directories we don't want
#         dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        
#         for filename in files:
#             _, ext = os.path.splitext(filename)
#             if ext.lower() not in EXTENSIONS:
#                 continue
            
#             filepath = os.path.join(root, filename)
#             scanned += 1
            
#             try:
#                 with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
#                     content = f.read()
#             except Exception as e:
#                 print(f"  SKIP (read error): {filepath} -> {e}")
#                 continue
            
#             if is_corrupted(content):
#                 fixed = fix_content(content)
#                 try:
#                     with open(filepath, 'w', encoding='utf-8', newline='
# ') as f:
#                         f.write(fixed)
#                     fixed_files.append(filepath)
#                     print(f"  FIXED: {filepath}")
#                 except Exception as e:
#                     print(f"  ERROR (write): {filepath} -> {e}")
    
#     print(f"
# === SUMMARY ===")
#     print(f"Scanned: {scanned} files")
#     print(f"Fixed:   {len(fixed_files)} files")
#     for f in fixed_files:
#         print(f"  - {os.path.relpath(f, PROJECT_ROOT)}")

# if __name__ == '__main__':
#     print("ApplySense-AI Corruption Fixer")
#     print(f"Project root: {PROJECT_ROOT}")
#     print("=" * 60)
#     scan_and_fix()
