"""Code analysis tools"""

import sys
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from collections import defaultdict

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class ClassInfo:
    """Class information"""
    name: str
    file: str
    line: int
    methods: List[str] = None
    fields: List[str] = None
    base_classes: List[str] = None
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.methods is None:
            self.methods = []
        if self.fields is None:
            self.fields = []
        if self.base_classes is None:
            self.base_classes = []
        if self.dependencies is None:
            self.dependencies = []


class CPPSourceAnalyzer:
    """Analyze C++ source code"""
    
    def __init__(self):
        self.classes: List[ClassInfo] = []
        self.dependencies: Dict[str, List[str]] = defaultdict(list)
    
    def analyze_file(self, file_path: Path) -> List[ClassInfo]:
        """Analyze a C++ file"""
        content = file_path.read_text()
        
        classes = []
        
        # Find classes
        class_pattern = r'class\s+(\w+)(?:\s*:\s*(.*?))?\{'
        
        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            inheritance = match.group(2) or ""
            
            base_classes = [
                b.strip().split()[-1]
                for b in inheritance.replace("{", "").split(",")
                if b.strip()
            ]
            
            # Find methods and fields
            class_body = self._extract_class_body(content, match.start())
            methods = self._extract_methods(class_body)
            fields = self._extract_fields(class_body)
            
            classes.append(ClassInfo(
                name=class_name,
                file=str(file_path),
                line=content[:match.start()].count('\n') + 1,
                methods=methods,
                fields=fields,
                base_classes=base_classes,
            ))
        
        return classes
    
    def _extract_class_body(self, content: str, start: int) -> str:
        """Extract class body"""
        depth = 0
        end = start
        
        for i in range(start, len(content)):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    end = i
                    break
        
        return content[start:end]
    
    def _extract_methods(self, body: str) -> List[str]:
        """Extract method declarations"""
        methods = []
        
        # Match method declarations
        pattern = r'(?:virtual\s+)?(?:\w+(?:\*|&)?\s+)+(\w+)\s*\([^)]*\)'
        
        for match in re.finditer(pattern, body):
            name = match.group(1)
            if name not in ["if", "while", "for", "switch", "return"]:
                methods.append(name)
        
        return list(set(methods))
    
    def _extract_fields(self, body: str) -> List[str]:
        """Extract field declarations"""
        fields = []
        
        # Match field declarations
        pattern = r'(?:private|protected|public)?\s*(?:\w+(?:\*|&)?\s+)+(\w+)\s*;'
        
        for match in re.finditer(pattern, body):
            name = match.group(1)
            if not name.startswith("_") and name not in ["int", "void", "bool", "char"]:
                fields.append(name)
        
        return list(set(fields))
    
    def analyze_directory(self, dir_path: Path) -> Dict[str, Any]:
        """Analyze entire directory"""
        cpp_files = list(dir_path.glob("**/*.cpp")) + list(dir_path.glob("**/*.h"))
        
        all_classes = []
        
        for cpp_file in cpp_files:
            try:
                classes = self.analyze_file(cpp_file)
                all_classes.extend(classes)
            except Exception as e:
                print(f"Error analyzing {cpp_file}: {e}")
        
        self.classes = all_classes
        
        # Build dependency graph
        self._build_dependencies()
        
        return self.get_summary()
    
    def _build_dependencies(self):
        """Build class dependency graph"""
        for cls in self.classes:
            deps = set()
            
            # Add base class dependencies
            deps.update(cls.base_classes)
            
            # Add method return type dependencies
            # (simplified)
            
            self.dependencies[cls.name] = list(deps)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get analysis summary"""
        return {
            "total_classes": len(self.classes),
            "total_methods": sum(len(c.methods) for c in self.classes),
            "total_fields": sum(len(c.fields) for c in self.classes),
            "classes": [
                {
                    "name": c.name,
                    "file": c.file,
                    "line": c.line,
                    "methods": len(c.methods),
                    "fields": len(c.fields),
                    "base_classes": c.base_classes,
                }
                for c in self.classes
            ],
            "dependencies": dict(self.dependencies),
        }
    
    def find_circular_dependencies(self) -> List[List[str]]:
        """Find circular dependencies"""
        def has_cycle(node, visited, rec_stack, path):
            visited.add(node)
            rec_stack.append(node)
            
            for dep in self.dependencies.get(node, []):
                if dep not in visited:
                    if has_cycle(dep, visited, rec_stack, path):
                        return True
                elif dep in rec_stack:
                    # Found cycle
                    cycle_start = rec_stack.index(dep)
                    path.append(rec_stack[cycle_start:] + [dep])
                    return True
            
            rec_stack.pop()
            return False
        
        cycles = []
        visited = set()
        
        for node in self.dependencies:
            if node not in visited:
                has_cycle(node, visited, [], cycles)
        
        return cycles


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="C++ Code Analyzer")
    parser.add_argument("path", help="File or directory to analyze")
    parser.add_argument("--output", "-o", help="Output JSON file")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    
    args = parser.parse_args()
    
    path = Path(args.path)
    
    analyzer = CPPSourceAnalyzer()
    
    if path.is_file():
        classes = analyzer.analyze_file(path)
        result = {
            "file": str(path),
            "classes": len(classes),
            "details": [
                {
                    "name": c.name,
                    "line": c.line,
                    "methods": c.methods,
                    "fields": c.fields,
                }
                for c in classes
            ],
        }
    else:
        result = analyzer.analyze_directory(path)
    
    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(f"Total classes: {result.get('total_classes', 0)}")
        print(f"Total methods: {result.get('total_methods', 0)}")
        print(f"Total fields: {result.get('total_fields', 0)}")
        
        if args.format == "text":
            for cls in result.get("classes", [])[:10]:
                print(f"  {cls['name']} ({cls['file']}:{cls['line']})")
    
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2))
        print(f"\nSaved to: {args.output}")


if __name__ == "__main__":
    main()