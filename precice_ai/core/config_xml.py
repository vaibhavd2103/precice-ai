from __future__ import annotations

from pathlib import Path

from lxml import etree


def parse_precice_config(config_file: Path) -> etree._Element:
    """Parse a precice-config.xml and return its root element.

    preCICE configs use prefixed tags (data:scalar, mapping:..., m2n:...)
    without declaring the namespaces, which a strict XML parser rejects, so
    the file is parsed in recovery mode. Raises ValueError if it is unreadable.
    """
    try:
        root = etree.parse(str(config_file), etree.XMLParser(recover=True)).getroot()
    except (etree.XMLSyntaxError, OSError) as exc:
        raise ValueError(str(exc)) from exc
    if root is None:
        raise ValueError(f"no root element in {config_file}")
    return root
