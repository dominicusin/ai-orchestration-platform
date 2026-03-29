"""
Serializers for various data formats
Сериализаторы для различных форматов данных
"""

import base64
import json
import pickle
import xml.etree.ElementTree as ET
from dataclasses import asdict, is_dataclass
from typing import Any


class Serializer:
    """Базовый класс сериализатора"""

    def serialize(self, data: Any) -> str:
        """Сериализация данных"""
        raise NotImplementedError

    def deserialize(self, data: str) -> Any:
        """Десериализация данных"""
        raise NotImplementedError


class JSONSerializer(Serializer):
    """JSON сериализатор"""

    def __init__(self, indent: int = 2, default_handler: callable = None):
        self.indent = indent
        self.default_handler = default_handler

    def serialize(self, data: Any) -> str:
        """Сериализация в JSON"""
        # Handle dataclasses
        if is_dataclass(data):
            data = asdict(data)

        return json.dumps(data, indent=self.indent, default=self.default_handler, ensure_ascii=False)

    def deserialize(self, data: str) -> Any:
        """Десериализация из JSON"""
        return json.loads(data)


class PickleSerializer(Serializer):
    """Pickle сериализатор"""

    def __init__(self, protocol: int = pickle.HIGHEST_PROTOCOL):
        self.protocol = protocol

    def serialize(self, data: Any) -> str:
        """Сериализация в pickle"""
        return base64.b64encode(pickle.dumps(data, protocol=self.protocol)).decode()

    def deserialize(self, data: str) -> Any:
        """Десериализация из pickle"""
        return pickle.loads(base64.b64decode(data.encode()))


class XMLSerializer(Serializer):
    """XML сериализатор"""

    def __init__(self, root_tag: str = "root"):
        self.root_tag = root_tag

    def serialize(self, data: Any) -> str:
        """Сериализация в XML"""
        root = ET.Element(self.root_tag)
        self._dict_to_xml(data, root)
        return ET.tostring(root, encoding="unicode", xml_declaration=True)

    def deserialize(self, data: str) -> Any:
        """Десериализация из XML"""
        root = ET.fromstring(data)
        return self._xml_to_dict(root)

    def _dict_to_xml(self, data: Any, parent: ET.Element):
        """Конвертация dict в XML"""
        if isinstance(data, dict):
            for key, value in data.items():
                elem = ET.SubElement(parent, str(key))
                self._dict_to_xml(value, elem)
        elif isinstance(data, list):
            for item in data:
                item_elem = ET.SubElement(parent, "item")
                self._dict_to_xml(item, item_elem)
        else:
            parent.text = str(data)

    def _xml_to_dict(self, elem: ET.Element) -> Any:
        """Конвертация XML в dict"""
        result = {}

        for child in elem:
            value = self._xml_to_dict(child)

            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(value)
            else:
                result[child.tag] = value

        if not result and elem.text:
            return elem.text

        return result if result else None


class MessagePackSerializer(Serializer):
    """MessagePack сериализатор (если доступен)"""

    def __init__(self):
        try:
            import msgpack
            self.msgpack = msgpack
        except ImportError as e:
            raise ImportError("msgpack not installed") from e

    def serialize(self, data: Any) -> bytes:
        """Сериализация в MessagePack"""
        return self.msgpack.packb(data, use_bin_type=True)

    def deserialize(self, data: bytes) -> Any:
        """Десериализация из MessagePack"""
        return self.msgpack.unpackb(data, raw=False)


# Factory functions

def get_serializer(format: str, **kwargs) -> Serializer:
    """Получение сериализатора по формату"""
    serializers = {
        "json": JSONSerializer,
        "pickle": PickleSerializer,
        "xml": XMLSerializer,
    }

    if format not in serializers:
        raise ValueError(f"Unknown format: {format}")

    return serializers[format](**kwargs)


def serialize(data: Any, format: str = "json", **kwargs) -> Any:
    """Универсальная сериализация"""
    serializer = get_serializer(format, **kwargs)

    if format == "pickle":
        # Return string for pickle
        return serializer.serialize(data)
    elif format == "xml":
        return serializer.serialize(data)
    else:
        return serializer.serialize(data)


def deserialize(data: Any, format: str = "json", **kwargs) -> Any:
    """Универсальная десериализация"""
    serializer = get_serializer(format, **kwargs)
    return serializer.deserialize(data)


# Convenience functions

def to_json(data: Any, **kwargs) -> str:
    """Сериализация в JSON строку"""
    return JSONSerializer(**kwargs).serialize(data)


def from_json(data: str) -> Any:
    """Десериализация из JSON строки"""
    return JSONSerializer().deserialize(data)


def to_pickle(data: Any, **kwargs) -> str:
    """Сериализация в pickle строку"""
    return PickleSerializer(**kwargs).serialize(data)


def from_pickle(data: str) -> Any:
    """Десериализация из pickle строки"""
    return PickleSerializer().deserialize(data)


def to_xml(data: Any, root_tag: str = "root", **kwargs) -> str:
    """Сериализация в XML строку"""
    return XMLSerializer(root_tag).serialize(data)


def from_xml(data: str) -> Any:
    """Десериализация из XML строки"""
    return XMLSerializer().deserialize(data)
