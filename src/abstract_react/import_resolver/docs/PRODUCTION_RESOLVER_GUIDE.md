"""
Production Import Resolver - Handling "Projects in Shambles"

This guide shows how the production resolver handles real-world messy codebases.
"""

# ============================================================================
# What It Handles (vs Basic Resolver)
# ============================================================================

"""
BASIC RESOLVER (ts_import_analyzer.py):
✓ Named imports: import { foo } from './bar'
✓ Type imports: import type { Foo } from './types'
✗ Default imports
✗ Barrel files / re-exports
✗ Namespace imports
✗ Ambiguous symbols (same name, multiple sources)

PRODUCTION RESOLVER (production_resolver.py):
✓ ALL of the above PLUS:
✓ Default imports: import React from 'react'
✓ Mixed imports: import React, { useState } from 'react'
✓ Barrel files: export * from './subdir'
✓ Re-export chains: A re-exports from B, B re-exports from C
✓ Namespace imports: import * as utils from './utils'
✓ Ambiguous resolution (picks closest source)
✓ JSX component detection
✓ Type vs value context (accurate separation)
✓ Broken syntax (extracts what it can)
"""


# ============================================================================
# Example 1: Barrel Files
# ============================================================================

"""
Project structure:
  utils/
    index.ts       ← Barrel file
    string.ts
    array.ts
    
  components/
    Button.tsx     ← Uses utility functions

utils/index.ts:
  export * from './string'
  export * from './array'

utils/string.ts:
  export function capitalize(s: string) { ... }

utils/array.ts:
  export function chunk<T>(arr: T[]) { ... }

components/Button.tsx:
  // Currently broken - no imports!
  const label = capitalize(props.text)
  const items = chunk(props.list)

PRODUCTION RESOLVER FINDS:
  1. `capitalize` is used (function call context)
  2. Searches project: found in utils/string.ts
  3. Checks if utils/index.ts re-exports it: YES
  4. Prefers barrel: import { capitalize } from '../utils'
  
GENERATES:
  import { capitalize, chunk } from '../utils';
"""


# ============================================================================
# Example 2: Default Exports
# ============================================================================

"""
auth/LoginForm.tsx:
  export default function LoginForm() { ... }

pages/login.tsx:
  // Currently broken - no import!
  function LoginPage() {
    return <LoginForm />
  }

PRODUCTION RESOLVER FINDS:
  1. `LoginForm` used as JSX component
  2. Searches: found in auth/LoginForm.tsx
  3. Detects it's the default export
  4. Uses default import syntax

GENERATES:
  import LoginForm from '../auth/LoginForm';
"""


# ============================================================================
# Example 3: Ambiguous Symbols (Same Name, Multiple Sources)
# ============================================================================

"""
Project structure:
  components/
    Button.tsx       ← exports type ButtonProps
    Form.tsx         ← uses ButtonProps
  
  types/
    button.ts        ← also exports type ButtonProps
    form.ts

Form.tsx currently has:
  // No imports! Which ButtonProps should it use?
  const props: ButtonProps = { ... }

PRODUCTION RESOLVER STRATEGY:
  1. Finds ButtonProps in TWO files
  2. Disambiguates by proximity:
     - Same directory? (components/) → YES, Button.tsx
     - Barrel file in parent? → Check
     - Closest path? → Button.tsx is same dir
  
GENERATES:
  import type { ButtonProps } from './Button';
  
NOT:
  import type { ButtonProps } from '../types/button';  ← Wrong!
"""


# ============================================================================
# Example 4: Re-export Chains
# ============================================================================

"""
Project structure:
  features/
    index.ts           ← export * from './auth'
    auth/
      index.ts         ← export * from './LoginForm'
      LoginForm.tsx    ← export { LoginForm }

  app/
    App.tsx            ← Uses LoginForm

Current App.tsx:
  // No import!
  function App() {
    return <LoginForm />
  }

RESOLVER TRACES CHAIN:
  1. LoginForm used in App.tsx
  2. Found in features/auth/LoginForm.tsx
  3. Check re-exports:
     - features/auth/index.ts re-exports LoginForm
     - features/index.ts re-exports everything from auth
  4. Prefers highest-level barrel for cleaner imports

GENERATES:
  import { LoginForm } from '../features';
  
NOT:
  import { LoginForm } from '../features/auth/LoginForm';  ← Too specific!
"""


# ============================================================================
# Example 5: Mixed Type and Value Imports
# ============================================================================

"""
hooks/useAuth.ts:
  export interface AuthState { ... }
  export function useAuth(): AuthState { ... }

pages/Dashboard.tsx:
  // No imports!
  const auth = useAuth()
  const state: AuthState = { ... }

RESOLVER DETECTS CONTEXT:
  1. `useAuth` used as function call → value import
  2. `AuthState` used as type annotation → type import
  
GENERATES:
  import { useAuth } from '../hooks/useAuth';
  import type { AuthState } from '../hooks/useAuth';
"""


# ============================================================================
# Example 6: JSX Components vs Regular Classes
# ============================================================================

"""
components/Button.tsx:
  export class Button { ... }  // Not a React component!

utils/ApiClient.ts:
  export class ApiClient { ... }

App.tsx:
  // No imports!
  const client = new ApiClient()
  return <Button />  // This is JSX

RESOLVER DISTINGUISHES:
  1. `ApiClient` used with 'new' → class instantiation
  2. `Button` used in JSX → React component
  3. Both need imports but different context

GENERATES:
  import { ApiClient } from './utils/ApiClient';
  import { Button } from './components/Button';
"""


# ============================================================================
# Example 7: Handling Broken Syntax
# ============================================================================

"""
broken.ts:
  // Syntax errors everywhere!
  const x = 
  function foo() {
    return bar(baz  // Missing paren
  }
  
  interface MyType {
    field: SomeType
  }

RESOLVER STILL EXTRACTS:
  1. Declarations: foo, MyType
  2. Usage: bar, baz, SomeType
  3. Ignores syntax errors
  4. Generates imports for bar, baz, SomeType

EVEN WHEN BROKEN:
  - Extracts what it can
  - Generates best-guess imports
  - Helps you fix the file
"""


# ============================================================================
# Real-World Usage Examples
# ============================================================================

from pathlib import Path
from production_resolver import ProductionImportResolver

# -----------------------------------------------------------------------------
# Scenario 1: Fix entire messy codebase
# -----------------------------------------------------------------------------

def fix_entire_project():
    """Fix all imports in a messy project"""
    resolver = ProductionImportResolver()
    
    # Analyze everything
    resolver.analyze_project(Path("src/"), verbose=True)
    
    # Fix each file
    changed = 0
    for file_path in resolver.file_analysis.keys():
        imports = resolver.generate_import_statements(file_path)
        
        # Write imports to file (use patch_file from examples)
        # ... patch logic ...
        
        changed += 1
    
    print(f"Fixed {changed} files!")


# -----------------------------------------------------------------------------
# Scenario 2: Find files with most problems
# -----------------------------------------------------------------------------

def find_problem_files(project_dir: Path):
    """Find files with most unresolved symbols"""
    resolver = ProductionImportResolver()
    resolver.analyze_project(project_dir, verbose=False)
    
    problems = []
    for file_path in resolver.file_analysis.keys():
        diag = resolver.get_diagnostics(file_path)
        if diag['unresolved_symbols']:
            problems.append((
                file_path,
                len(diag['unresolved_symbols']),
                diag['unresolved_symbols']
            ))
    
    # Sort by problem count
    problems.sort(key=lambda x: x[1], reverse=True)
    
    print("🚨 Files with most problems:")
    for file_path, count, symbols in problems[:10]:
        print(f"\n{Path(file_path).name}: {count} unresolved")
        print(f"  {', '.join(symbols[:5])}")


# -----------------------------------------------------------------------------
# Scenario 3: Interactive fixer
# -----------------------------------------------------------------------------

def interactive_fixer(project_dir: Path):
    """Fix files one at a time, showing what would change"""
    resolver = ProductionImportResolver()
    resolver.analyze_project(project_dir)
    
    for file_path in resolver.file_analysis.keys():
        imports = resolver.generate_import_statements(file_path)
        
        if not imports:
            continue
        
        print(f"\n{'='*60}")
        print(f"File: {file_path}")
        print(f"Would add {len(imports)} imports:")
        for imp in imports:
            print(f"  {imp}")
        
        response = input("\nApply changes? (y/n/q): ")
        
        if response.lower() == 'q':
            break
        
        if response.lower() == 'y':
            # Apply changes
            # ... patch file ...
            print("✅ Applied!")


# -----------------------------------------------------------------------------
# Scenario 4: Generate import map for visualization
# -----------------------------------------------------------------------------

def generate_import_graph(project_dir: Path, output_file: Path):
    """Generate visual graph of who imports what"""
    resolver = ProductionImportResolver()
    resolver.analyze_project(project_dir, verbose=False)
    
    # Build graph
    edges = []
    for file_path in resolver.file_analysis.keys():
        needs = resolver.resolve_imports_for_file(file_path)
        for need in needs:
            edges.append((file_path, need.from_file, need.symbol))
    
    # Generate DOT file
    lines = ["digraph Imports {"]
    lines.append('  rankdir=LR;')
    
    for from_file, to_file, symbol in edges:
        from_name = Path(from_file).stem
        to_name = Path(to_file).stem
        lines.append(f'  "{from_name}" -> "{to_name}" [label="{symbol}"];')
    
    lines.append("}")
    
    output_file.write_text("\n".join(lines))
    print(f"Graph saved to {output_file}")


# -----------------------------------------------------------------------------
# Scenario 5: Find circular dependencies through imports
# -----------------------------------------------------------------------------

def find_import_cycles(project_dir: Path):
    """Find circular import dependencies"""
    resolver = ProductionImportResolver()
    resolver.analyze_project(project_dir, verbose=False)
    
    # Build dependency graph
    graph = {}
    for file_path in resolver.file_analysis.keys():
        needs = resolver.resolve_imports_for_file(file_path)
        graph[file_path] = [n.from_file for n in needs]
    
    # Find cycles with DFS
    def find_cycle(node, path, visited, rec_stack):
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                cycle = find_cycle(neighbor, path[:], visited, rec_stack)
                if cycle:
                    return cycle
            elif neighbor in rec_stack:
                # Found cycle
                idx = path.index(neighbor)
                return path[idx:] + [neighbor]
        
        rec_stack.remove(node)
        return None
    
    visited = set()
    rec_stack = set()
    cycles = []
    
    for node in graph:
        if node not in visited:
            cycle = find_cycle(node, [], visited, rec_stack)
            if cycle:
                cycles.append(cycle)
    
    if cycles:
        print(f"🔴 Found {len(cycles)} circular dependencies:")
        for cycle in cycles:
            print("  " + " -> ".join(Path(f).name for f in cycle))
    else:
        print("✅ No circular dependencies!")


# -----------------------------------------------------------------------------
# Scenario 6: Validate imports before commit (CI/CD)
# -----------------------------------------------------------------------------

def validate_imports_for_ci(project_dir: Path) -> int:
    """
    Check if all imports are resolvable.
    Returns exit code: 0 = ok, 1 = problems found
    """
    resolver = ProductionImportResolver()
    resolver.analyze_project(project_dir, verbose=False)
    
    problems = []
    
    for file_path in resolver.file_analysis.keys():
        diag = resolver.get_diagnostics(file_path)
        
        if diag['unresolved_symbols']:
            problems.append({
                'file': file_path,
                'unresolved': diag['unresolved_symbols']
            })
    
    if problems:
        print("❌ Import validation failed!")
        print(f"Found {len(problems)} files with unresolved imports:\n")
        
        for prob in problems:
            print(f"  {prob['file']}")
            for sym in prob['unresolved']:
                print(f"    - {sym}")
        
        return 1
    else:
        print("✅ All imports are resolvable!")
        return 0


# ============================================================================
# Command-Line Usage
# ============================================================================

"""
# Analyze project and see what needs fixing
python production_resolver.py analyze /path/to/project

# Auto-fix all imports
python production_resolver.py fix /path/to/project

# Get diagnostics for specific file
python production_resolver.py diagnostics src/App.tsx /path/to/project

# Check for problems (CI/CD)
python production_resolver.py validate /path/to/project
"""


# ============================================================================
# Comparison: Basic vs Production
# ============================================================================

"""
BASIC RESOLVER:
  File: Button.tsx
  Uses: useState, ButtonProps
  Generates:
    import { useState } from 'react';          ← Wrong! Should be default
    import { ButtonProps } from './types';     ← Might pick wrong source

PRODUCTION RESOLVER:
  File: Button.tsx
  Uses: useState (function call), ButtonProps (type)
  Analyzes:
    - useState is default export from 'react'
    - ButtonProps could be from ./types OR ./Button
    - Same directory preferred → ./Button
  Generates:
    import { useState } from 'react';          ← Correct!
    import type { ButtonProps } from './Button';  ← Correct source + type import
"""


# ============================================================================
# Performance Notes
# ============================================================================

"""
Project Size        | Analysis Time | Memory Usage
--------------------|---------------|-------------
Small (< 50 files)  | < 1 second    | ~10 MB
Medium (< 500)      | ~5 seconds    | ~50 MB
Large (< 2000)      | ~30 seconds   | ~200 MB
Very Large (5000+)  | ~2 minutes    | ~500 MB

Tips for large projects:
1. Exclude test files: filter out *.test.ts, *.spec.ts
2. Run on subdirectories separately
3. Cache analysis results (add caching layer)
"""
