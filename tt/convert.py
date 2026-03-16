"""Conversion utilities and helpers"""

import re
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ConversionResult:
    """Conversion result"""
    success: bool
    output: str
    errors: List[str]
    warnings: List[str]
    stats: Dict[str, Any]


class TypeMapper:
    """Map C++ types to target languages"""
    
    # C++ -> Haskell
    CPP_TO_HASKELL = {
        "int": "Int",
        "long": "Integer",
        "short": "Int",
        "char": "Char",
        "bool": "Bool",
        "float": "Double",
        "double": "Double",
        "void": "()",
        "std::string": "Text",
        "std::vector": "Seq",
        "std::list": "List",
        "std::map": "Map",
        "std::set": "Set",
        "std::pair": "(,)",
        "std::unique_ptr": "Maybe",
        "std::shared_ptr": "IO",
        "std::optional": "Maybe",
    }
    
    # C++ -> QML
    CPP_TO_QML = {
        "int": "int",
        "long": "int",
        "bool": "bool",
        "float": "real",
        "double": "real",
        "QString": "string",
        "QObject": "QtObject",
        "QWidget": "Item",
        "QQuickItem": "Item",
        "QAbstractListModel": "ListModel",
    }
    
    # C++ -> SQL
    CPP_TO_SQL = {
        "int": "INTEGER",
        "long": "BIGINT",
        "short": "SMALLINT",
        "char": "CHAR(1)",
        "bool": "BOOLEAN",
        "float": "REAL",
        "double": "DOUBLE PRECISION",
        "std::string": "VARCHAR(255)",
        "QString": "VARCHAR(255)",
    }
    
    @classmethod
    def to_haskell(cls, cpp_type: str) -> str:
        """Map C++ type to Haskell"""
        # Remove const, pointers, references
        clean = re.sub(r'\b(const|volatile)\b', '', cpp_type)
        clean = re.sub(r'[*&]', '', clean).strip()
        
        # Handle templates
        if "<" in clean:
            base = clean[:clean.index("<")]
            if base in cls.CPP_TO_HASKELL:
                inner = clean[clean.index("<")+1:clean.rindex(">")]
                haskell_inner = cls.to_haskell(inner)
                return f"{cls.CPP_TO_HASKELL[base]}<{haskell_inner}>"
        
        return cls.CPP_TO_HASKELL.get(clean, clean)
    
    @classmethod
    def to_qml(cls, cpp_type: str) -> str:
        """Map C++ type to QML"""
        clean = re.sub(r'\bconst\b', '', cpp_type)
        clean = re.sub(r'[*&]', '', clean).strip()
        return cls.CPP_TO_QML.get(clean, "var")
    
    @classmethod
    def to_sql(cls, cpp_type: str) -> str:
        """Map C++ type to SQL"""
        clean = re.sub(r'\bconst\b', '', cpp_type)
        clean = re.sub(r'[*&]', '', clean).strip()
        
        # Check for string
        if "string" in clean.lower() or "qstring" in clean.lower():
            return "VARCHAR(255)"
        
        return cls.CPP_TO_SQL.get(clean, "TEXT")


class NameConverter:
    """Convert naming conventions"""
    
    @staticmethod
    def cpp_to_haskell(name: str) -> str:
        """Convert C++ snake_case to Haskell CamelCase"""
        # Handle common patterns
        name = re.sub(r'^[a-z]', lambda m: m.group().upper(), name)
        parts = name.split('_')
        return ''.join(p.capitalize() for p in parts if p)
    
    @staticmethod
    def cpp_to_qml(name: str) -> str:
        """Convert C++ camelCase to QML camelCase"""
        return name
    
    @staticmethod
    def cpp_to_python(name: str) -> str:
        """Convert C++ camelCase to Python snake_case"""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    @staticmethod
    def cpp_to_sql(name: str) -> str:
        """Convert C++ camelCase to SQL snake_case"""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


class CodeCleaner:
    """Clean and normalize code"""
    
    @staticmethod
    def remove_comments(code: str, language: str = "cpp") -> str:
        """Remove comments"""
        if language == "cpp":
            # Remove /* */ comments
            code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
            # Remove // comments
            code = re.sub(r'//.*?$', '', code, flags=re.MULTILINE)
        elif language == "haskell":
            # Remove {- -} comments
            code = re.sub(r'\{-.*?-\}', '', code, flags=re.DOTALL)
            # Remove -- comments
            code = re.sub(r'--.*?$', '', code, flags=re.MULTILINE)
        
        return code
    
    @staticmethod
    def remove_includes(code: str) -> str:
        """Remove #include directives"""
        return re.sub(r'#include\s*<[^>]+>', '', code)
    
    @staticmethod
    def normalize_whitespace(code: str) -> str:
        """Normalize whitespace"""
        # Remove trailing whitespace
        code = re.sub(r'[ \t]+$', '', code, flags=re.MULTILINE)
        # Remove empty lines
        code = re.sub(r'\n\s*\n', '\n', code)
        # Normalize indentation
        return code
    
    @staticmethod
    def extract_using(code: str) -> List[str]:
        """Extract using/typedef declarations"""
        using = re.findall(r'using\s+(\w+)\s*=\s*([^;]+);', code)
        return [f"{alias} = {type_}" for alias, type_ in using]


class CodeExtractor:
    """Extract code structures"""
    
    @staticmethod
    def extract_classes(code: str) -> List[Dict[str, Any]]:
        """Extract class definitions"""
        classes = []
        
        # Match class definitions
        pattern = r'class\s+(\w+)(?:\s*:\s*(.*?))?\s*\{'
        
        for match in re.finditer(pattern, code):
            class_name = match.group(1)
            inheritance = match.group(2) or ""
            
            # Extract body
            body_start = match.end()
            depth = 1
            body_end = body_start
            
            for i in range(body_start, len(code)):
                if code[i] == '{':
                    depth += 1
                elif code[i] == '}':
                    depth -= 1
                    if depth == 0:
                        body_end = i
                        break
            
            body = code[body_start:body_end]
            
            classes.append({
                "name": class_name,
                "inheritance": inheritance.strip().split(',') if inheritance else [],
                "body": body,
            })
        
        return classes
    
    @staticmethod
    def extract_functions(code: str) -> List[Dict[str, Any]]:
        """Extract function definitions"""
        functions = []
        
        # Match function definitions
        pattern = r'(?:virtual\s+)?(\w+(?:\*|&)?)\s+(\w+)\s*\(([^)]*)\)'
        
        for match in re.finditer(pattern, code):
            ret_type = match.group(1)
            name = match.group(2)
            params = match.group(3)
            
            if name not in ['if', 'while', 'for', 'switch', 'return']:
                functions.append({
                    "name": name,
                    "return_type": ret_type,
                    "params": params,
                })
        
        return functions
    
    @staticmethod
    def extract_includes(code: str) -> List[str]:
        """Extract #include directives"""
        return re.findall(r'#include\s+[<"]([^>"]+)[>"]', code)


class TemplateRenderer:
    """Render code from templates"""
    
    def __init__(self):
        self.templates: Dict[str, str] = {}
    
    def register_template(self, name: str, template: str):
        """Register a template"""
        self.templates[name] = template
    
    def render(self, name: str, context: Dict) -> str:
        """Render a template"""
        template = self.templates.get(name)
        
        if not template:
            raise ValueError(f"Unknown template: {name}")
        
        # Simple template rendering
        result = template
        
        for key, value in context.items():
            result = result.replace(f"${{{key}}}", str(value))
        
        return result


class FileConverter:
    """Convert files between formats"""
    
    def __init__(self):
        self.type_mapper = TypeMapper()
        self.name_converter = NameConverter()
        self.cleaner = CodeCleaner()
        self.extractor = CodeExtractor()
    
    def convert_cpp_to_haskell(self, cpp_code: str) -> ConversionResult:
        """Convert C++ to Haskell"""
        errors = []
        warnings = []
        
        try:
            # Clean code
            code = self.cleaner.remove_comments(cpp_code, "cpp")
            code = self.cleaner.normalize_whitespace(code)
            
            # Extract classes
            classes = self.extractor.extract_classes(code)
            
            # Convert each class
            haskell_modules = []
            
            for cls in classes:
                module = self._convert_class_to_haskell(cls)
                haskell_modules.append(module)
            
            output = "\n\n".join(haskell_modules)
            
            return ConversionResult(
                success=True,
                output=output,
                errors=errors,
                warnings=warnings,
                stats={"classes": len(classes)},
            )
            
        except Exception as e:
            return ConversionResult(
                success=False,
                output="",
                errors=[str(e)],
                warnings=[],
                stats={},
            )
    
    def _convert_class_to_haskell(self, cls: Dict) -> str:
        """Convert a C++ class to Haskell module"""
        name = cls["name"]
        
        # Convert class name
        haskell_name = self.name_converter.cpp_to_haskell(name)
        
        # Generate module
        module = f"module {haskell_name} where\n\n"
        
        # Add data type
        fields = self._extract_fields(cls["body"])
        
        if fields:
            module += f"data {haskell_name} = {haskell_name}\n"
            module += "  { " + "\n , ".join(fields) + " }\n"
        
        return module
    
    def _extract_fields(self, body: str) -> List[str]:
        """Extract fields from class body"""
        fields = []
        
        # Match field declarations
        pattern = r'(\w+)\s+(\w+)\s*;'
        
        for match in re.finditer(pattern, body):
            ftype = match.group(1)
            fname = match.group(2)
            
            haskell_type = self.type_mapper.to_haskell(ftype)
            fields.append(f"{fname} :: {haskell_type}")
        
        return fields


# Global converter
_converter: Optional[FileConverter] = None


def get_converter() -> FileConverter:
    """Get file converter"""
    global _converter
    if _converter is None:
        _converter = FileConverter()
    return _converter