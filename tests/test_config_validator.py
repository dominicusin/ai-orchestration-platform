"""Tests for Config Validator"""


from orchestration.config_validator import (
    ConfigValidator,
    create_pipeline_validator,
    validate_env_var,
    validate_path,
    validate_pipeline_config,
    validate_port,
    validate_positive_int,
    validate_range,
    validate_url,
)


class TestValidators:
    """Test validators"""

    def test_validate_port(self):
        """Test port validation"""
        assert validate_port(8080) is True
        assert validate_port(80) is True
        assert validate_port(65535) is True
        assert validate_port(0) is False
        assert validate_port(70000) is False
        assert validate_port("8080") is True

    def test_validate_url(self):
        """Test URL validation"""
        assert validate_url("http://localhost:8080") is True
        assert validate_url("https://example.com") is True
        assert validate_url("not-a-url") is False

    def test_validate_path(self):
        """Test path validation"""
        assert validate_path("/tmp/test") is True
        assert validate_path("relative/path") is True

    def test_validate_positive_int(self):
        """Test positive int validation"""
        assert validate_positive_int(1) is True
        assert validate_positive_int(100) is True
        assert validate_positive_int(0) is False
        assert validate_positive_int(-1) is False
        assert validate_positive_int("10") is True

    def test_validate_range(self):
        """Test range validation"""
        assert validate_range(50, 0, 100) is True
        assert validate_range(0, 0, 100) is True
        assert validate_range(100, 0, 100) is True
        assert validate_range(-1, 0, 100) is False
        assert validate_range(101, 0, 100) is False

    def test_validate_env_var(self):
        """Test env var validation"""
        assert validate_env_var("MY_VAR") is True
        assert validate_env_var("API_KEY") is True
        assert validate_env_var("my_var") is False
        assert validate_env_var("123") is False


class TestConfigValidator:
    """Test ConfigValidator"""

    def test_creation(self):
        """Test creation"""
        validator = ConfigValidator()
        assert validator.rules == {}

    def test_add_rule(self):
        """Test add rule"""
        validator = ConfigValidator()
        validator.add_rule("test", lambda x: True, "Test error")
        assert "test" in validator.rules

    def test_validate_pass(self):
        """Test validation passes"""
        validator = ConfigValidator()
        validator.add_rule("field1", lambda x: "field1" in x, "field1 required")

        result = validator.validate({"field1": "value"})
        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_fail(self):
        """Test validation fails"""
        validator = ConfigValidator()
        validator.add_rule("field1", lambda x: "field1" in x, "field1 required")

        result = validator.validate({})
        assert result.valid is False
        assert len(result.errors) == 1


class TestPipelineValidator:
    """Test pipeline validator"""

    def test_create_pipeline_validator(self):
        """Test create validator"""
        validator = create_pipeline_validator()
        assert validator is not None
        assert len(validator.rules) > 0

    def test_validate_valid_config(self):
        """Test valid config"""
        config = {
            "project_path": "/path/to/project",
            "output_path": "/path/to/output",
            "max_workers": 4,
        }
        result = validate_pipeline_config(config)
        assert result.valid is True

    def test_validate_missing_required(self):
        """Test missing required fields"""
        config = {
            "max_workers": 4,
        }
        result = validate_pipeline_config(config)
        assert result.valid is False
        assert len(result.errors) > 0

    def test_validate_invalid_port(self):
        """Test invalid port"""
        config = {
            "project_path": "/path",
            "output_path": "/out",
            "prometheus_port": 70000,
        }
        result = validate_pipeline_config(config)
        assert result.valid is False
