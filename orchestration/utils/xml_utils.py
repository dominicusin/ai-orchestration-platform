"""XML utilities"""

import xml.etree.ElementTree as ET
from typing import Any, Dict


def parse_xml(xml_str: str) -> ET.Element:
    """Parse XML string"""
    return ET.fromstring(xml_str)


def xml_to_dict(element: ET.Element) -> Dict:
    """Convert XML to dict"""
    result = {}
    for child in element:
        result[child.tag] = child.text
    return result


def dict_to_xml(data: Dict, root_tag: str = "root") -> str:
    """Convert dict to XML"""
    root = ET.Element(root_tag)
    for key, value in data.items():
        child = ET.SubElement(root, key)
        child.text = str(value)
    return ET.tostring(root, encoding='unicode')


def pretty_xml(xml_str: str) -> str:
    """Pretty print XML"""
    tree = ET.parse(xml_str) if isinstance(xml_str, str) else ET.ElementTree(xml_str)
    ET.indent(tree.getroot())
    return ET.tostring(tree.getroot(), encoding='unicode')
