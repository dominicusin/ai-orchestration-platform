"""Prompt management system with versioning"""

import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger("orchestration.prompts")


@dataclass
class PromptVersion:
    """Prompt version"""
    version: str
    prompt: str
    created_at: str
    description: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PromptTemplate:
    """Prompt template"""
    name: str
    description: str
    current_version: str
    versions: List[PromptVersion]
    variables: List[str] = field(default_factory=list)


class PromptManager:
    """Manage AI prompts with versioning and analytics"""
    
    def __init__(self, prompts_dir: str = "./prompts"):
        self.prompts_dir = Path(prompts_dir)
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        
        self.templates: Dict[str, PromptTemplate] = {}
        self._load_templates()
        
        # Built-in templates
        self._register_builtin_templates()
    
    def _load_templates(self):
        """Load prompt templates from disk"""
        for template_file in self.prompts_dir.glob("*.json"):
            try:
                data = json.loads(template_file.read_text())
                
                versions = []
                for v in data.get("versions", []):
                    versions.append(PromptVersion(
                        version=v["version"],
                        prompt=v["prompt"],
                        created_at=v.get("created_at", ""),
                        description=v.get("description", ""),
                        metrics=v.get("metrics", {}),
                    ))
                
                template = PromptTemplate(
                    name=data["name"],
                    description=data.get("description", ""),
                    current_version=data.get("current_version", "1.0"),
                    versions=versions,
                    variables=data.get("variables", []),
                )
                
                self.templates[template.name] = template
                
            except Exception as e:
                logger.warning(f"Failed to load {template_file}: {e}")
    
    def _register_builtin_templates(self):
        """Register built-in prompt templates"""
        self.templates["cpp_to_haskell"] = PromptTemplate(
            name="cpp_to_haskell",
            description="Convert C++ to Haskell",
            current_version="1.0",
            versions=[
                PromptVersion(
                    version="1.0",
                    prompt="""Ты - эксперт по конвертации C++ в Haskell.
Конвертируй следующий C++ код в чистый Haskell.

ПРАВИЛА:
1. Используй Haskell 2010
2. Типы: int → Int, float → Double, bool → Bool
3. std::string → Text, std::vector → [a]
4. class → data type с record синтаксисом
5. public/private не нужны в Haskell

```cpp
{code}
```

Haskell:""",
                    created_at=datetime.now().isoformat(),
                    description="Initial version",
                ),
            ],
            variables=["code"],
        )
        
        self.templates["sql_ddl"] = PromptTemplate(
            name="sql_ddl",
            description="Generate PostgreSQL DDL",
            current_version="1.0",
            versions=[
                PromptVersion(
                    version="1.0",
                    prompt="""Ты - эксперт по PostgreSQL.
Конвертируй структуру в DDL.

ПРАВИЛА:
1. snake_case для имен
2. Типы: int → INTEGER, long → BIGINT

{struct_info}

SQL:""",
                    created_at=datetime.now().isoformat(),
                ),
            ],
            variables=["struct_info"],
        )
        
        self.templates["qml_convert"] = PromptTemplate(
            name="qml_convert",
            description="Convert Qt to QML",
            current_version="1.0",
            versions=[
                PromptVersion(
                    version="1.0",
                    prompt="""Ты - эксперт по Qt → QML.
Конвертируй в QML 3.

МАППИНГ:
- QPushButton → Button
- QLineEdit → TextField
- QLabel → Text
- QCheckBox → CheckBox

```cpp
{code}
```

QML:""",
                    created_at=datetime.now().isoformat(),
                ),
            ],
            variables=["code"],
        )
    
    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """Get prompt template"""
        return self.templates.get(name)
    
    def render(self, name: str, variables: Dict[str, str], version: str = None) -> Optional[str]:
        """Render prompt with variables"""
        template = self.templates.get(name)
        
        if not template:
            logger.error(f"Template not found: {name}")
            return None
        
        # Get version
        if version is None:
            version = template.current_version
        
        prompt_version = next(
            (v for v in template.versions if v.version == version),
            template.versions[0] if template.versions else None
        )
        
        if not prompt_version:
            return None
        
        # Render variables
        prompt = prompt_version.prompt
        
        for var_name, var_value in variables.items():
            prompt = prompt.replace(f"{{{var_name}}}", var_value)
        
        return prompt
    
    def create_template(
        self,
        name: str,
        description: str,
        prompt: str,
        variables: List[str],
    ) -> bool:
        """Create new prompt template"""
        if name in self.templates:
            return False
        
        version = PromptVersion(
            version="1.0",
            prompt=prompt,
            created_at=datetime.now().isoformat(),
            description="Initial version",
        )
        
        template = PromptTemplate(
            name=name,
            description=description,
            current_version="1.0",
            versions=[version],
            variables=variables,
        )
        
        self.templates[name] = template
        self._save_template(template)
        
        return True
    
    def update_template(
        self,
        name: str,
        prompt: str,
        description: str = None,
    ) -> bool:
        """Update template with new version"""
        template = self.templates.get(name)
        
        if not template:
            return False
        
        # Create new version
        version_parts = template.current_version.split(".")
        new_version = f"{version_parts[0]}.{int(version_parts[1]) + 1}"
        
        version = PromptVersion(
            version=new_version,
            prompt=prompt,
            created_at=datetime.now().isoformat(),
            description=description or f"Updated to version {new_version}",
        )
        
        template.versions.append(version)
        template.current_version = new_version
        
        if description:
            template.description = description
        
        self._save_template(template)
        
        return True
    
    def _save_template(self, template: PromptTemplate):
        """Save template to disk"""
        data = {
            "name": template.name,
            "description": template.description,
            "current_version": template.current_version,
            "variables": template.variables,
            "versions": [
                {
                    "version": v.version,
                    "prompt": v.prompt,
                    "created_at": v.created_at,
                    "description": v.description,
                    "metrics": v.metrics,
                }
                for v in template.versions
            ],
        }
        
        file_path = self.prompts_dir / f"{template.name}.json"
        file_path.write_text(json.dumps(data, indent=2))
    
    def record_usage(self, name: str, version: str, success: bool, tokens: int):
        """Record prompt usage for analytics"""
        template = self.templates.get(name)
        
        if not template:
            return
        
        prompt_version = next(
            (v for v in template.versions if v.version == version),
            None
        )
        
        if prompt_version:
            if "usage_count" not in prompt_version.metrics:
                prompt_version.metrics["usage_count"] = 0
            if "total_tokens" not in prompt_version.metrics:
                prompt_version.metrics["total_tokens"] = 0
            
            prompt_version.metrics["usage_count"] += 1
            prompt_version.metrics["total_tokens"] += tokens
            
            if success:
                prompt_version.metrics["success_count"] = \
                    prompt_version.metrics.get("success_count", 0) + 1
            
            self._save_template(template)
    
    def get_analytics(self, name: str) -> Dict[str, Any]:
        """Get prompt analytics"""
        template = self.templates.get(name)
        
        if not template:
            return {}
        
        analytics = {
            "name": template.name,
            "description": template.description,
            "current_version": template.current_version,
            "versions": [],
        }
        
        for v in template.versions:
            metrics = v.metrics
            usage = metrics.get("usage_count", 0)
            success = metrics.get("success_count", 0)
            
            analytics["versions"].append({
                "version": v.version,
                "description": v.description,
                "usage_count": usage,
                "success_rate": success / usage if usage > 0 else 0,
                "total_tokens": metrics.get("total_tokens", 0),
            })
        
        return analytics
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """List all templates"""
        return [
            {
                "name": t.name,
                "description": t.description,
                "current_version": t.current_version,
                "versions_count": len(t.versions),
            }
            for t in self.templates.values()
        ]


# Global instance
_prompt_manager: Optional[PromptManager] = None


def get_prompt_manager() -> PromptManager:
    """Get prompt manager"""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager
