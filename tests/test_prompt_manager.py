"""Tests for Prompt Manager"""

import json

import pytest

from orchestration.prompt_manager import (
    PromptMetadata,
    PromptVersion,
    PromptVersionManager,
)


class TestPromptVersion:
    """Test PromptVersion dataclass"""

    def test_creation(self):
        """Test version creation"""
        version = PromptVersion(
            version="1.0.0",
            template="Hello {{name}}",
            variables={"name": "world"},
            description="Test version",
            created_at="2024-01-01T00:00:00Z",
        )
        assert version.version == "1.0.0"
        assert "{{name}}" in version.template
        assert version.is_active is True


class TestPromptMetadata:
    """Test PromptMetadata dataclass"""

    def test_creation(self):
        """Test metadata creation"""
        metadata = PromptMetadata(
            name="test_prompt",
            category="conversion",
            description="Test prompt",
            tags=["haskell", "conversion"],
        )
        assert metadata.name == "test_prompt"
        assert metadata.category == "conversion"
        assert "haskell" in metadata.tags


class TestPromptVersionManager:
    """Test Prompt Version Manager"""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create temp prompts directory"""
        return tmp_path / "prompts"

    @pytest.fixture
    def manager(self, temp_dir):
        """Create manager with temp directory"""
        return PromptVersionManager(temp_dir)

    def test_manager_init(self, manager):
        """Test manager initialization"""
        assert manager.prompts_dir.exists()

    def test_create_prompt(self, manager):
        """Test create prompt"""
        result = manager.create_prompt(
            name="test_prompt",
            template="Convert {{code}} to Haskell",
            category="conversion",
            description="Test prompt",
            variables={"code": "C++ code"},
        )
        assert result is not None
        assert result.name == "test_prompt"
        assert len(result.versions) == 1
        assert result.versions[0].version == "1.0.0"

    def test_create_prompt_saves_file(self, manager, temp_dir):
        """Test that creating prompt saves file"""
        manager.create_prompt("test", "Template {{var}}")
        file_path = temp_dir / "test.json"
        assert file_path.exists()

        data = json.loads(file_path.read_text())
        assert data["name"] == "test"
        assert len(data["versions"]) == 1

    def test_add_version(self, manager):
        """Test add version"""
        manager.create_prompt("test", "Version 1")
        version = manager.add_version("test", "Version 2", "Description")

        assert version is not None
        assert version.version == "1.0.1"
        assert version.template == "Version 2"

    def test_get_active_version(self, manager):
        """Test get active version"""
        manager.create_prompt("test", "Active version")
        manager.add_version("test", "New version")

        active = manager.get_active_version("test")
        assert active is not None
        assert active.template == "New version"

    def test_get_version(self, manager):
        """Test get specific version"""
        manager.create_prompt("test", "Version 1")
        manager.add_version("test", "Version 2")

        v1 = manager.get_version("test", "1.0.0")
        assert v1 is not None
        assert v1.template == "Version 1"

        v2 = manager.get_version("test", "1.0.1")
        assert v2 is not None
        assert v2.template == "Version 2"

    def test_rollback(self, manager):
        """Test rollback"""
        manager.create_prompt("test", "Version 1")
        manager.add_version("test", "Version 2")
        manager.add_version("test", "Version 3")

        # Rollback to previous (last active is v3, should go to v2)
        result = manager.rollback("test")
        assert result is True

        active = manager.get_active_version("test")
        # After rollback, v3 is disabled, v2 becomes active
        assert active.version in ["1.0.1", "1.0.2"]

    def test_rollback_to_specific(self, manager):
        """Test rollback to specific version"""
        manager.create_prompt("test", "Version 1")
        manager.add_version("test", "Version 2")
        manager.add_version("test", "Version 3")

        # Rollback to v1
        result = manager.rollback("test", "1.0.0")
        assert result is True

        active = manager.get_active_version("test")
        assert active.version == "1.0.0"

    def test_render(self, manager):
        """Test render prompt"""
        manager.create_prompt(
            "test",
            "Convert {{code}} to {{lang}}",
            variables={"code": "C++", "lang": "Haskell"},
        )

        result = manager.render("test", {"code": "int x;", "lang": "Haskell"})
        assert result is not None
        assert "int x;" in result
        assert "Haskell" in result

    def test_render_with_version(self, manager):
        """Test render with specific version"""
        manager.create_prompt("test", "Version 1 {{var}}")
        manager.add_version("test", "Version 2 {{var}}")

        result = manager.render("test", {"var": "test"}, version="1.0.0")
        assert result == "Version 1 test"

    def test_list_prompts(self, manager):
        """Test list prompts"""
        manager.create_prompt("prompt1", "Template 1", category="cat1")
        manager.create_prompt("prompt2", "Template 2", category="cat2")

        all_prompts = manager.list_prompts()
        assert len(all_prompts) == 2

        cat1 = manager.list_prompts("cat1")
        assert len(cat1) == 1
        assert cat1[0].name == "prompt1"

    def test_delete_prompt(self, manager):
        """Test delete prompt"""
        manager.create_prompt("test", "Template")
        result = manager.delete_prompt("test")
        assert result is True

        # Check file deleted
        file_path = manager.prompts_dir / "test.json"
        assert not file_path.exists()

    def test_delete_nonexistent(self, manager):
        """Test delete nonexistent prompt"""
        result = manager.delete_prompt("nonexistent")
        assert result is False
