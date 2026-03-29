"""Tests for Input Validators"""


from orchestration.input_validators import (
    AndValidator,
    CustomValidator,
    EmailValidator,
    LengthValidator,
    OrValidator,
    PatternValidator,
    RangeValidator,
    RequiredValidator,
    SchemaValidator,
    TypeValidator,
    URLValidator,
    and_,
    custom,
    email,
    is_type,
    length,
    pattern,
    range,
    required,
    schema,
    url,
)


class TestRequiredValidator:
    """Test RequiredValidator"""

    def test_valid(self):
        """Test valid value"""
        v = RequiredValidator()
        assert v.validate("test") is True
        assert v.validate(123) is True

    def test_invalid(self):
        """Test invalid value"""
        v = RequiredValidator()
        assert v.validate("") is False
        assert v.validate(None) is False


class TestTypeValidator:
    """Test TypeValidator"""

    def test_valid(self):
        """Test valid type"""
        v = TypeValidator(str)
        assert v.validate("test") is True

    def test_invalid(self):
        """Test invalid type"""
        v = TypeValidator(str)
        assert v.validate(123) is False


class TestRangeValidator:
    """Test RangeValidator"""

    def test_within_range(self):
        """Test within range"""
        v = RangeValidator(0, 100)
        assert v.validate(50) is True
        assert v.validate(0) is True
        assert v.validate(100) is True

    def test_outside_range(self):
        """Test outside range"""
        v = RangeValidator(0, 100)
        assert v.validate(-1) is False
        assert v.validate(101) is False


class TestLengthValidator:
    """Test LengthValidator"""

    def test_valid_length(self):
        """Test valid length"""
        v = LengthValidator(2, 5)
        assert v.validate("abc") is True

    def test_invalid_length(self):
        """Test invalid length"""
        v = LengthValidator(2, 5)
        assert v.validate("a") is False
        assert v.validate("abcdef") is False


class TestPatternValidator:
    """Test PatternValidator"""

    def test_valid_pattern(self):
        """Test valid pattern"""
        v = PatternValidator(r"^\d+$")
        assert v.validate("123") is True

    def test_invalid_pattern(self):
        """Test invalid pattern"""
        v = PatternValidator(r"^\d+$")
        assert v.validate("abc") is False


class TestEmailValidator:
    """Test EmailValidator"""

    def test_valid_email(self):
        """Test valid email"""
        v = EmailValidator()
        assert v.validate("test@example.com") is True

    def test_invalid_email(self):
        """Test invalid email"""
        v = EmailValidator()
        assert v.validate("not-an-email") is False


class TestURLValidator:
    """Test URLValidator"""

    def test_valid_url(self):
        """Test valid URL"""
        v = URLValidator()
        assert v.validate("http://example.com") is True
        assert v.validate("https://example.com") is True

    def test_invalid_url(self):
        """Test invalid URL"""
        v = URLValidator()
        assert v.validate("ftp://example.com") is False


class TestCustomValidator:
    """Test CustomValidator"""

    def test_custom_valid(self):
        """Test custom validator"""
        v = CustomValidator(lambda x: x > 0, "Must be positive")
        assert v.validate(5) is True
        assert v.validate(-1) is False


class TestAndValidator:
    """Test AndValidator"""

    def test_all_pass(self):
        """Test all pass"""
        v = AndValidator(
            RequiredValidator(),
            LengthValidator(min_len=3),
        )
        assert v.validate("test") is True

    def test_one_fail(self):
        """Test one fails"""
        v = AndValidator(
            RequiredValidator(),
            LengthValidator(min_len=10),
        )
        assert v.validate("test") is False


class TestOrValidator:
    """Test OrValidator"""

    def test_one_passes(self):
        """Test one passes"""
        v = OrValidator(
            TypeValidator(str),
            TypeValidator(int),
        )
        assert v.validate("test") is True
        assert v.validate(123) is True
        assert v.validate([]) is False


class TestSchemaValidator:
    """Test SchemaValidator"""

    def test_valid_schema(self):
        """Test valid schema"""
        v = SchemaValidator({
            "name": RequiredValidator(),
            "age": and_(RequiredValidator(), RangeValidator(0, 150)),
        })
        assert v.validate({"name": "John", "age": 30}) is True

    def test_invalid_schema(self):
        """Test invalid schema"""
        v = SchemaValidator({
            "name": RequiredValidator(),
            "age": and_(RequiredValidator(), RangeValidator(0, 150)),
        })
        result = v.validate({"name": "John"})  # age is missing
        assert result is False


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_required(self):
        """Test required helper"""
        v = required()
        assert v.validate("test") is True
        assert v.validate("") is False

    def test_is_type(self):
        """Test is_type helper"""
        v = is_type(str)
        assert v.validate("test") is True
        assert v.validate(123) is False

    def test_range(self):
        """Test range helper"""
        v = range(0, 100)
        assert v.validate(50) is True
        assert v.validate(200) is False

    def test_length(self):
        """Test length helper"""
        v = length(2, 5)
        assert v.validate("abc") is True

    def test_pattern(self):
        """Test pattern helper"""
        v = pattern(r"^\d+$")
        assert v.validate("123") is True

    def test_email(self):
        """Test email helper"""
        v = email()
        assert v.validate("test@example.com") is True

    def test_url(self):
        """Test url helper"""
        v = url()
        assert v.validate("http://example.com") is True

    def test_custom(self):
        """Test custom helper"""
        v = custom(lambda x: x > 0)
        assert v.validate(5) is True

    def test_and(self):
        """Test and_ helper"""
        v = and_(required(), length(min_len=3))
        assert v.validate("test") is True

    def test_schema(self):
        """Test schema helper"""
        v = schema({"name": required()})
        assert v.validate({"name": "John"}) is True
        assert v.validate({}) is False
