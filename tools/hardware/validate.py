#!/usr/bin/env python3
"""Validate ATOM's JSON-compatible YAML hardware records without external packages."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CATEGORIES = {
    "camera_board", "controller_board", "passive_component", "power_supply",
    "sensor", "servo_motor", "stepper_driver", "stepper_motor", "mechanical",
    "connector", "other",
}
PHYSICAL_STATUSES = {"owned", "installed", "planned"}
IDENTIFICATION_STATUSES = {"complete", "incomplete", "unverified"}
CONFIDENCE_STATES = {"confirmed", "reported", "unknown"}
ASSEMBLY_STATUSES = {"confirmed", "unverified"}
MAPPING_STATUSES = {"confirmed", "unresolved", "unverified"}
ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
REQUIRED_COMPONENT_FIELDS = {
    "id", "category", "status", "identification", "manufacturer", "model",
    "quantity", "specifications", "datasheet", "evidence", "notes",
}


@dataclass(frozen=True)
class Message:
    severity: str
    location: str
    text: str


class Validator:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.messages: list[Message] = []

    def add(self, severity: str, location: str, text: str) -> None:
        self.messages.append(Message(severity, location, text))

    def load(self, path: Path) -> Any:
        try:
            # JSON is a strict subset of YAML 1.2. Keeping source files in this
            # subset avoids adding a parser dependency to the repository.
            return json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            self.add("ERROR", str(path), "required file does not exist")
        except (UnicodeError, json.JSONDecodeError) as exc:
            self.add("ERROR", str(path), f"invalid JSON-compatible YAML: {exc}")
        return None

    def validate_reference_path(self, value: Any, location: str) -> None:
        if not isinstance(value, str) or not value:
            self.add("ERROR", location, "reference path must be a non-empty string")
            return
        candidate = (self.root / value).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError:
            self.add("ERROR", location, "reference escapes the repository root")
            return
        if not candidate.is_file():
            self.add("WARNING", location, f"referenced file is missing: {value}")

    def validate_evidence(self, values: Any, location: str) -> None:
        if not isinstance(values, list):
            self.add("ERROR", location, "evidence must be a list")
            return
        for index, value in enumerate(values):
            self.validate_reference_path(value, f"{location}[{index}]")

    def validate_specifications(self, specs: Any, location: str) -> None:
        if not isinstance(specs, dict) or not specs:
            self.add("ERROR", location, "specifications must be a non-empty object")
            return
        for name, spec in specs.items():
            spec_location = f"{location}.{name}"
            if not isinstance(spec, dict):
                self.add("ERROR", spec_location, "specification must be an object")
                continue
            missing = {"value", "unit", "confidence", "source"} - spec.keys()
            if missing:
                self.add("ERROR", spec_location, f"missing fields: {', '.join(sorted(missing))}")
                continue
            confidence = spec["confidence"]
            if confidence not in CONFIDENCE_STATES:
                self.add("ERROR", spec_location, f"invalid confidence: {confidence!r}")
            value = spec["value"]
            if isinstance(value, bool) or not isinstance(value, (str, int, float, type(None))):
                self.add("ERROR", spec_location, "value must be a string, finite number, or null")
            if isinstance(value, (int, float)) and not isinstance(value, bool) and not math.isfinite(value):
                self.add("ERROR", spec_location, "numeric value must be finite")
            if value is None:
                if confidence != "unknown" or spec["source"] is not None:
                    self.add("ERROR", spec_location, "null values require unknown confidence and null source")
                self.add("WARNING", spec_location, "technical value is unknown")
            else:
                if confidence == "unknown":
                    self.add("ERROR", spec_location, "non-null value cannot have unknown confidence")
                if not isinstance(spec["source"], str) or not spec["source"].strip():
                    self.add("ERROR", spec_location, "non-null value requires a source")
            if spec["unit"] is not None and not isinstance(spec["unit"], str):
                self.add("ERROR", spec_location, "unit must be a string or null")
            if spec["unit"] is not None and value is not None and (
                isinstance(value, bool) or not isinstance(value, (int, float))
            ):
                self.add("ERROR", spec_location, "a specification with units requires a numeric value")

    def validate_components(self, data: Any) -> dict[str, dict[str, Any]]:
        if not isinstance(data, dict) or data.get("schema_version") != 1:
            self.add("ERROR", "components", "schema_version must be 1")
            return {}
        components = data.get("components")
        if not isinstance(components, list):
            self.add("ERROR", "components", "components must be a list")
            return {}
        result: dict[str, dict[str, Any]] = {}
        for index, component in enumerate(components):
            location = f"components[{index}]"
            if not isinstance(component, dict):
                self.add("ERROR", location, "component must be an object")
                continue
            missing = REQUIRED_COMPONENT_FIELDS - component.keys()
            if missing:
                self.add("ERROR", location, f"missing fields: {', '.join(sorted(missing))}")
            identifier = component.get("id")
            if not isinstance(identifier, str) or not ID_PATTERN.fullmatch(identifier):
                self.add("ERROR", f"{location}.id", "ID must be lowercase snake_case")
                continue
            if identifier in result:
                self.add("ERROR", f"{location}.id", f"duplicate component ID: {identifier}")
            else:
                result[identifier] = component
            if component.get("category") not in CATEGORIES:
                self.add("ERROR", f"{location}.category", f"invalid category: {component.get('category')!r}")
            if component.get("status") not in PHYSICAL_STATUSES:
                self.add("ERROR", f"{location}.status", f"invalid physical status: {component.get('status')!r}")
            identification = component.get("identification")
            if not isinstance(identification, dict) or identification.get("status") not in IDENTIFICATION_STATUSES:
                self.add("ERROR", f"{location}.identification", "invalid identification status")
            quantity = component.get("quantity")
            if quantity is None:
                self.add("WARNING", f"{location}.quantity", "quantity is unknown")
            elif isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
                self.add("ERROR", f"{location}.quantity", "quantity must be a positive integer or null")
            if component.get("manufacturer") is None or component.get("model") is None:
                self.add("WARNING", location, "manufacturer or model is not identified")
            self.validate_specifications(component.get("specifications"), f"{location}.specifications")
            datasheet = component.get("datasheet")
            if datasheet is not None:
                self.validate_reference_path(datasheet, f"{location}.datasheet")
            self.validate_evidence(component.get("evidence"), f"{location}.evidence")
        self.add("INFO", "components", f"loaded {len(result)} unique component records")
        return result

    def validate_component_ref(
        self, value: Any, location: str, components: dict[str, dict[str, Any]], *, nullable: bool = False
    ) -> None:
        if value is None and nullable:
            return
        if not isinstance(value, str) or value not in components:
            self.add("ERROR", location, f"unknown component reference: {value!r}")

    def validate_assembly(self, data: Any, components: dict[str, dict[str, Any]]) -> None:
        if not isinstance(data, dict) or data.get("schema_version") != 1:
            self.add("ERROR", "assembly", "schema_version must be 1")
            return
        assembly = data.get("assembly")
        if not isinstance(assembly, dict):
            self.add("ERROR", "assembly", "assembly must be an object")
            return
        if assembly.get("status") not in ASSEMBLY_STATUSES:
            self.add("ERROR", "assembly.status", "invalid assembly status")
        installed = assembly.get("installed_components")
        available = assembly.get("available_not_installed")
        if not isinstance(installed, list) or not isinstance(available, list):
            self.add("ERROR", "assembly", "installed and available component collections must be lists")
            return
        for field, values in (("installed_components", installed), ("available_not_installed", available)):
            if len(values) != len(set(values)):
                self.add("ERROR", f"assembly.{field}", "contains duplicate references")
            for index, value in enumerate(values):
                self.validate_component_ref(value, f"assembly.{field}[{index}]", components)
        overlap = set(installed) & set(available)
        if overlap:
            self.add("ERROR", "assembly", f"components cannot be installed and available: {sorted(overlap)}")
        for identifier in installed:
            if identifier in components and components[identifier].get("status") != "installed":
                self.add("ERROR", "assembly.installed_components", f"{identifier} is not marked installed in inventory")
        for identifier, component in components.items():
            if component.get("status") == "installed" and identifier not in installed:
                self.add("ERROR", "assembly.installed_components", f"installed inventory item omitted: {identifier}")
            if component.get("status") == "owned" and identifier not in installed and identifier not in available:
                self.add("WARNING", "assembly.available_not_installed", f"owned item is unaccounted for: {identifier}")
        subsystems = assembly.get("subsystems")
        if not isinstance(subsystems, list):
            self.add("ERROR", "assembly.subsystems", "subsystems must be a list")
        else:
            for index, subsystem in enumerate(subsystems):
                location = f"assembly.subsystems[{index}]"
                if not isinstance(subsystem, dict):
                    self.add("ERROR", location, "subsystem must be an object")
                    continue
                self.validate_component_ref(subsystem.get("controller_component_id"), f"{location}.controller_component_id", components, nullable=True)
                self.validate_evidence(subsystem.get("evidence"), f"{location}.evidence")
                if subsystem.get("controller_component_id") is None:
                    self.add("WARNING", location, "controller assignment is unresolved")
        simulation = assembly.get("simulation")
        if not isinstance(simulation, dict):
            self.add("ERROR", "assembly.simulation", "simulation mapping must be an object")
            return
        mappings = simulation.get("joint_mappings")
        if not isinstance(mappings, list):
            self.add("ERROR", "assembly.simulation.joint_mappings", "joint_mappings must be a list")
            return
        names: set[str] = set()
        for index, mapping in enumerate(mappings):
            location = f"assembly.simulation.joint_mappings[{index}]"
            if not isinstance(mapping, dict):
                self.add("ERROR", location, "mapping must be an object")
                continue
            name = mapping.get("simulation_joint")
            if not isinstance(name, str) or not name:
                self.add("ERROR", f"{location}.simulation_joint", "joint name is required")
            elif name in names:
                self.add("ERROR", f"{location}.simulation_joint", f"duplicate joint mapping: {name}")
            else:
                names.add(name)
            state = mapping.get("mapping_status")
            if state not in MAPPING_STATUSES:
                self.add("ERROR", f"{location}.mapping_status", "invalid mapping status")
            for field in ("physical_motor_id", "driver_id", "controller_id"):
                self.validate_component_ref(mapping.get(field), f"{location}.{field}", components, nullable=True)
            self.validate_evidence(mapping.get("evidence"), f"{location}.evidence")
            assigned = any(mapping.get(field) is not None for field in ("physical_motor_id", "driver_id", "controller_id"))
            if state == "confirmed" and (not assigned or not mapping.get("evidence")):
                self.add("ERROR", location, "confirmed mappings require assignments and evidence")
            if not assigned:
                self.add("WARNING", location, "physical mapping is unresolved")
        self.add("INFO", "assembly", f"loaded {len(installed)} installed and {len(available)} available references")

    def render(self) -> str:
        counts = {severity: 0 for severity in ("ERROR", "WARNING", "INFO")}
        for message in self.messages:
            counts[message.severity] += 1
        lines = [
            "ATOM Hardware Workspace validation",
            f"Result: {'FAILED' if counts['ERROR'] else 'PASSED WITH WARNINGS' if counts['WARNING'] else 'PASSED'}",
            f"Errors: {counts['ERROR']}  Warnings: {counts['WARNING']}  Info: {counts['INFO']}",
            "",
        ]
        lines.extend(f"[{m.severity}] {m.location}: {m.text}" for m in self.messages)
        return "\n".join(lines) + "\n"


def repository_root(script: Path) -> Path:
    return script.resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--components", type=Path, help="override components file")
    parser.add_argument("--assembly", type=Path, help="override assembly file")
    parser.add_argument("--report", type=Path, help="write the report to this path")
    args = parser.parse_args(argv)
    root = repository_root(Path(__file__))
    components_path = args.components or root / "hardware/inventory/components.yaml"
    assembly_path = args.assembly or root / "hardware/inventory/assembly.yaml"
    validator = Validator(root)
    components = validator.validate_components(validator.load(components_path))
    validator.validate_assembly(validator.load(assembly_path), components)
    report = validator.render()
    sys.stdout.write(report)
    if args.report:
        destination = args.report if args.report.is_absolute() else root / args.report
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(report, encoding="utf-8", newline="\n")
    return 1 if any(message.severity == "ERROR" for message in validator.messages) else 0


if __name__ == "__main__":
    raise SystemExit(main())
