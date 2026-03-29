"""Tests for Data Validators"""

import pytest

from orchestration.data_validators import (
    BooleanValidator,
    ChoiceValidator,
    CompositeValidator,
    DictValidator,
    EmailValidator,
    ListValidator,
    NumberValidator,
    OptionalValidator,
    StringValidator,
    URLValidator,
    validate,
    validate_or_raise,
)


class TestStringValidator:
    """Test StringValidator"""

    def test_valid_string(self):
        """Test valid string"""
        v = StringValidator(min_length=3, max_length=10)
        is_valid, error = v.validate("hello")
        assert is_valid is True
        assert error is None

    def test_too_short(self):
        """Test too short"""
        v = StringValidator(min_length=5)
        is_valid, error = v.validate("hi")
        assert is_valid is False

    def test_too_long(self):
        """Test too long"""
        v = StringValidator(max_length=5)
        is_valid, error = v.validate("hello world")
        assert is_valid is False

    def test_pattern(self):
        """Test pattern"""
        v = StringValidator(pattern=r"^\d+$")
        is_valid, _ = v.validate("123")
        assert is_valid is True
        is_valid, _ = v.validate("abc")
        assert is_valid is False


class TestNumberValidator:
    """Test NumberValidator"""

    def test_valid_number(self):
        """Test valid number"""
        v = NumberValidator(min_value=0, max_value=100)
        is_valid, _ = v.validate(50)
        assert is_valid is True

    def test_out_of_range(self):
        """Test out of range"""
        v = NumberValidator(min_value=0, max_value=100)
        is_valid, _ = v.validate(150)
        assert is_valid is False

    def test_integer_only(self):
        """Test integer only"""
        v = NumberValidator(integer_only=True)
        is_valid, _ = v.validate(5)
        assert is_valid is True
        is_valid, _ = v.validate(5.5)
        assert is_valid is False


class TestBooleanValidator:
    """Test BooleanValidator"""

    def test_valid_bool(self):
        """Test valid bool"""
        v = BooleanValidator()
        is_valid, _ = v.validate(True)
        assert is_valid is True

    def test_string_bool(self):
        """Test string bool"""
        v = BooleanValidator()
        is_valid, _ = v.validate("true")
        assert is_valid is True


class TestListValidator:
    """Test ListValidator"""

    def test_valid_list(self):
        """Test valid list"""
        v = ListValidator(min_items=1, max_items=5)
        is_valid, _ = v.validate([1, 2, 3])
        assert is_valid is True

    def test_too_few_items(self):
        """Test too few items"""
        v = ListValidator(min_items=2)
        is_valid, _ = v.validate([1])
        assert is_valid is False


class TestDictValidator:
    """Test DictValidator"""

    def test_valid_dict(self):
        """Test valid dict"""
        v = DictValidator(required_keys=["name"])
        is_valid, _ = v.validate({"name": "John"})
        assert is_valid is True

    def test_missing_key(self):
        """Test missing key"""
        v = DictValidator(required_keys=["name"])
        is_valid, _ = v.validate({"age": 30})
        assert is_valid is False


class TestEmailValidator:
    """Test EmailValidator"""

    def test_valid_email(self):
        """Test valid email"""
        v = EmailValidator()
        is_valid, _ = v.validate("test@example.com")
        assert is_valid is True

    def test_invalid_email(self):
        """Test invalid email"""
        v = EmailValidator()
        is_valid, _ = v.validate("not-an-email")
        assert is_valid is False


class TestURLValidator:
    """Test URLValidator"""

    def test_valid_url(self):
        """Test valid URL"""
        v = URLValidator()
        is_valid, _ = v.validate("https://example.com")
        assert is_valid is True


class TestChoiceValidator:
    """Test ChoiceValidator"""

    def test_valid_choice(self):
        """Test valid choice"""
        v = ChoiceValidator(["a", "b", "c"])
        is_valid, _ = v.validate("a")
        assert is_valid is True

    def test_invalid_choice(self):
        """Test invalid choice"""
        v = ChoiceValidator(["a", "b", "c"])
        is_valid, _ = v.validate("d")
        assert is_valid is False


class TestCompositeValidator:
    """Test CompositeValidator"""

    def test_all_mode(self):
        """Test all mode"""
        v = CompositeValidator(
            StringValidator(min_length=3),
            StringValidator(max_length=10),
            mode="all",
        )
        is_valid, _ = v.validate("hello")
        assert is_valid is True


class TestOptionalValidator:
    """Test OptionalValidator"""

    def test_none_allowed(self):
        """Test none allowed"""
        v = OptionalValidator(StringValidator(min_length=3), allow_none=True)
        is_valid, _ = v.validate(None)
        assert is_valid is True


class TestHelperFunctions:
    """Test helper functions"""

    def test_validate(self):
        """Test validate helper"""
        v = StringValidator(min_length=3)
        assert validate("hello", v) is True
        assert validate("hi", v) is False

    def test_validate_or_raise(self):
        """Test validate or raise"""
        v = StringValidator(min_length=3)
        result = validate_or_raise("hello", v)
        assert result == "hello"

        with pytest.raises(ValueError):
            validate_or_raise("hi", v)
