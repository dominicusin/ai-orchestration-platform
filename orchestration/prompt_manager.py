"""
Prompt versioning and management
Версионирование и управление промптами
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("orchestration.prompts")


@dataclass
class PromptVersion:
    """Версия промпта"""
    version: str
    template: str
    variables: dict[str, str]
    description: str
    created_at: str
    created_by: str = "system"
    is_active: bool = True


@dataclass
class PromptMetadata:
    """Метаданные промпта"""
    name: str
    category: str
    description: str
    versions: list[PromptVersion] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


class PromptVersionManager:
    """
    Менеджер версий промптов с поддержкой:
    - Версионирование
    - Rollback
    - A/B testing
    - Templates с переменными
    """

    def __init__(self, prompts_dir: Path = None):
        self.prompts_dir = prompts_dir or Path("prompts")
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        self._prompts: dict[str, PromptMetadata] = {}
        self._load_prompts()

    def _load_prompts(self):
        """Загрузка промптов из файлов"""
        for f in self.prompts_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                name = data.get("name", f.stem)
                versions = [
                    PromptVersion(
                        version=v["version"],
                        template=v["template"],
                        variables=v.get("variables", {}),
                        description=v.get("description", ""),
                        created_at=v.get("created_at", ""),
                        created_by=v.get("created_by", "system"),
                        is_active=v.get("is_active", True),
                    )
                    for v in data.get("versions", [])
                ]
                self._prompts[name] = PromptMetadata(
                    name=name,
                    category=data.get("category", "general"),
                    description=data.get("description", ""),
                    versions=versions,
                    tags=data.get("tags", []),
                    created_at=data.get("created_at", ""),
                    updated_at=data.get("updated_at", ""),
                )
            except Exception as e:
                logger.warning(f"Error loading prompt {f}: {e}")

    def _save_prompt(self, name: str):
        """Сохранение промпта в файл"""
        prompt = self._prompts.get(name)
        if not prompt:
            return

        data = {
            "name": prompt.name,
            "category": prompt.category,
            "description": prompt.description,
            "tags": prompt.tags,
            "created_at": prompt.created_at,
            "updated_at": datetime.now().isoformat(),
            "versions": [
                {
                    "version": v.version,
                    "template": v.template,
                    "variables": v.variables,
                    "description": v.description,
                    "created_at": v.created_at,
                    "created_by": v.created_by,
                    "is_active": v.is_active,
                }
                for v in prompt.versions
            ],
        }

        path = self.prompts_dir / f"{name}.json"
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def create_prompt(
        self,
        name: str,
        template: str,
        category: str = "general",
        description: str = "",
        variables: dict[str, str] = None,
        tags: list[str] = None,
    ) -> PromptMetadata:
        """Создание нового промпта"""
        version = PromptVersion(
            version="1.0.0",
            template=template,
            variables=variables or {},
            description=description,
            created_at=datetime.now().isoformat(),
            is_active=True,
        )

        metadata = PromptMetadata(
            name=name,
            category=category,
            description=description,
            versions=[version],
            tags=tags or [],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )

        self._prompts[name] = metadata
        self._save_prompt(name)
        logger.info(f"Created prompt: {name} v{version.version}")
        return metadata

    def add_version(
        self,
        name: str,
        template: str,
        description: str = "",
        variables: dict[str, str] = None,
    ) -> PromptVersion | None:
        """Добавление новой версии"""
        prompt = self._prompts.get(name)
        if not prompt:
            logger.warning(f"Prompt {name} not found")
            return None

        # Получаем текущую версию
        last = prompt.versions[-1] if prompt.versions else None
        major, minor, patch = 1, 0, 0
        if last:
            parts = last.version.split(".")
            major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
            patch += 1
            if patch > 9:
                patch = 0
                minor += 1
            if minor > 9:
                minor = 0
                major += 1

        version = PromptVersion(
            version=f"{major}.{minor}.{patch}",
            template=template,
            variables=variables or {},
            description=description,
            created_at=datetime.now().isoformat(),
            is_active=True,
        )

        # Деактивируем предыдущую
        if last:
            last.is_active = False

        prompt.versions.append(version)
        prompt.updated_at = datetime.now().isoformat()
        self._save_prompt(name)

        logger.info(f"Added version {version.version} to prompt {name}")
        return version

    def get_active_version(self, name: str) -> PromptVersion | None:
        """Получение активной версии"""
        prompt = self._prompts.get(name)
        if not prompt:
            return None

        for v in reversed(prompt.versions):
            if v.is_active:
                return v
        return prompt.versions[-1] if prompt.versions else None

    def get_version(self, name: str, version: str) -> PromptVersion | None:
        """Получение конкретной версии"""
        prompt = self._prompts.get(name)
        if not prompt:
            return None

        for v in prompt.versions:
            if v.version == version:
                return v
        return None

    def rollback(self, name: str, target_version: str = None) -> bool:
        """Откат к предыдущей версии"""
        prompt = self._prompts.get(name)
        if not prompt or len(prompt.versions) < 2:
            return False

        if target_version:
            for v in prompt.versions:
                if v.version == target_version:
                    v.is_active = True
                else:
                    v.is_active = False
        else:
            # Откат к предыдущей
            prompt.versions[-1].is_active = True
            if len(prompt.versions) > 1:
                prompt.versions[-2].is_active = False

        prompt.updated_at = datetime.now().isoformat()
        self._save_prompt(name)
        logger.info(f"Rolled back prompt {name}")
        return True

    def render(
        self,
        name: str,
        context: dict[str, Any] = None,
        version: str = None,
    ) -> str | None:
        """Рендер промпта с подстановкой переменных"""
        if version:
            prompt_version = self.get_version(name, version)
        else:
            prompt_version = self.get_active_version(name)

        if not prompt_version:
            return None

        template = prompt_version.template
        context = context or {}

        # Заменяем переменные {{variable}}
        for key, value in context.items():
            template = template.replace(f"{{{{{key}}}}}", str(value))

        return template

    def list_prompts(self, category: str = None) -> list[PromptMetadata]:
        """Список промптов"""
        if category:
            return [p for p in self._prompts.values() if p.category == category]
        return list(self._prompts.values())

    def delete_prompt(self, name: str) -> bool:
        """Удаление промпта"""
        if name in self._prompts:
            del self._prompts[name]
            path = self.prompts_dir / f"{name}.json"
            if path.exists():
                path.unlink()
            return True
        return False


# Singleton
_prompt_manager: PromptVersionManager | None = None


def get_prompt_manager(prompts_dir: Path = None) -> PromptVersionManager:
    """Получение менеджера промптов"""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptVersionManager(prompts_dir)
    return _prompt_manager
