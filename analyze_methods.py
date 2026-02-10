"""Analyze Python files for method size violations."""
import re
from pathlib import Path
from typing import List, Tuple

def count_method_lines(file_path: str) -> List[Tuple[str, int, int, int]]:
    """Count lines in each method/function.
    
    Returns: List of (func_name, start_line, end_line, code_lines)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    violations = []
    current_func = None
    func_start = 0
    indent_level = 0
    in_docstring = False
    docstring_delim = None
    code_lines = 0
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # Track docstrings
        if in_docstring:
            if docstring_delim in stripped:
                in_docstring = False
            continue
        
        if stripped.startswith('"""') or stripped.startswith("'''"):
            docstring_delim = '"""' if '"""' in stripped else "'''"
            if stripped.count(docstring_delim) == 1:
                in_docstring = True
            continue
        
        # Find function/method definitions
        func_pattern = r'^\s*(def |async def )'
        if re.match(func_pattern, line):
            # Save previous function if it exists
            if current_func:
                if code_lines > 20:
                    violations.append((current_func, func_start, i-1, code_lines))
            
            # Start new function
            indent_level = len(line) - len(line.lstrip())
            func_match = re.search(r'def (\w+)', line)
            if func_match:
                current_func = func_match.group(1)
                func_start = i
                code_lines = 0
        elif current_func and line.strip() and not line.strip().startswith('#'):
            # Count non-blank, non-comment lines
            curr_indent = len(line) - len(line.lstrip())
            if curr_indent > indent_level:
                code_lines += 1
    
    # Check last function
    if current_func and code_lines > 20:
        violations.append((current_func, func_start, len(lines), code_lines))
    
    return violations


if __name__ == '__main__':
    # Check main violators
    files = [
        r'c:\Dev\polish_art\src\utils\search_cache.py',
        r'c:\Dev\polish_art\src\api\routes.py',
        r'c:\Dev\polish_art\src\utils\google_vision_search.py',
        r'c:\Dev\polish_art\src\services\vision_tracking_service.py',
        r'c:\Dev\polish_art\src\services\similarity_service.py',
        r'c:\Dev\polish_art\src\repositories\vision_repository.py',
        r'c:\Dev\polish_art\src\utils\google_image_search.py',
        r'c:\Dev\polish_art\src\repositories\feature_repository.py',
        r'c:\Dev\polish_art\src\cv_pipeline\feature_extractor.py'
    ]
    
    all_violations = []
    for file_path in files:
        violations = count_method_lines(file_path)
        if violations:
            print(f'\n{Path(file_path).name}:')
            for func, start, end, lines in violations:
                print(f'  {func}() - Lines {start}-{end} ({lines} code lines) - EXCEEDS 20 LINE LIMIT')
                all_violations.append((file_path, func, start, end, lines))
    
    print(f'\n\nTOTAL VIOLATIONS: {len(all_violations)}')
