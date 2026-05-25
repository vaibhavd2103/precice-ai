from datetime import datetime
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

from mcp.server.fastmcp import FastMCP

from precice_ai.core.paths import get_project_path, get_precice_config_path
from precice_ai.core.command_runner import run_safe_command


def register_config_tools(mcp: FastMCP) -> None:
    """Register preCICE configuration-related MCP tools."""

    @mcp.tool()
    def inspect_precice_config(project_name: str) -> str:
        """Read the precice-config.xml file of a project."""
        config_file = get_precice_config_path(project_name)
        if not config_file.exists():
            return f"No precice-config.xml found at: {config_file}"
        return config_file.read_text(errors="ignore")

    @mcp.tool()
    def summarize_precice_config(project_name: str) -> str:
        """Summarize important information from precice-config.xml."""
        config_file = get_precice_config_path(project_name)
        if not config_file.exists():
            return f"No precice-config.xml found at: {config_file}"

        try:
            tree = ET.parse(config_file)
            root = tree.getroot()
        except ET.ParseError as exc:
            return f"Failed to parse XML file: {exc}"

        participants: list[str] = []
        meshes: list[str] = []
        data_items: list[str] = []
        coupling_schemes: list[str] = []

        for element in root.iter():
            tag = _clean_xml_tag(element.tag)
            if tag == "participant":
                name = element.attrib.get("name")
                if name:
                    participants.append(name)
            if tag == "mesh":
                name = element.attrib.get("name")
                if name:
                    meshes.append(name)
            if tag in {"read-data", "write-data", "data:scalar", "data:vector"}:
                name = element.attrib.get("name")
                if name:
                    data_items.append(name)
            if "coupling-scheme" in tag:
                coupling_schemes.append(tag)

        return f"""preCICE configuration summary

Project:
{project_name}

Config file:
{config_file}

Participants:
{_format_list(participants)}

Meshes:
{_format_list(meshes)}

Data items:
{_format_list(data_items)}

Coupling scheme tags:
{_format_list(coupling_schemes)}
"""

    @mcp.tool()
    def check_precice_config(project_name: str) -> str:
        """Run preCICE config check on precice-config.xml."""
        project_path = get_project_path(project_name)
        config_file = get_precice_config_path(project_name)

        if not config_file.exists():
            return f"No precice-config.xml found at: {config_file}"

        command = "precice-cli config check precice-config.xml"
        result = run_safe_command(command=command, cwd=project_path, timeout=60)

        if "executable is not allowed" in result or "not found" in result.lower():
            fallback_command = "precice-tools check precice-config.xml"
            fallback_result = run_safe_command(
                command=fallback_command, cwd=project_path, timeout=60
            )
            return f"""Tried primary command:
{command}

Primary result:
{result}

Tried fallback command:
{fallback_command}

Fallback result:
{fallback_result}
"""
        return result

    @mcp.tool()
    def backup_precice_config(project_name: str) -> str:
        """Create a timestamped backup of precice-config.xml."""
        config_file = get_precice_config_path(project_name)
        if not config_file.exists():
            return f"No precice-config.xml found at: {config_file}"

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_file = config_file.with_name(f"precice-config.backup-{timestamp}.xml")
        shutil.copy2(config_file, backup_file)
        return f"Backup created: {backup_file}"

    @mcp.tool()
    def visualize_precice_config(project_name: str) -> str:
        """Generate a visualization of precice-config.xml if preCICE CLI supports it."""
        project_path = get_project_path(project_name)
        config_file = get_precice_config_path(project_name)

        if not config_file.exists():
            return f"No precice-config.xml found at: {config_file}"

        return run_safe_command(
            command="precice-cli config visualize precice-config.xml",
            cwd=project_path,
            timeout=60,
        )


def _clean_xml_tag(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _format_list(items: list[str]) -> str:
    unique_items = sorted(set(items))
    if not unique_items:
        return "- None found"
    return "\n".join(f"- {item}" for item in unique_items)
