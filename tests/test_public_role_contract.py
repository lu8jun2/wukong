from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFS_ROOT = ROOT / "skills" / "multi-agent-wukong" / "references"
TEAM_ROLES = REFS_ROOT / "team-roles.md"
ROLE_MAP_JSON = REFS_ROOT / "agency-agent-role-map.json"
ROLE_MAP_MD = REFS_ROOT / "agency-agent-role-map.md"


class PublicRoleContractTests(unittest.TestCase):
    def test_public_historian_is_a_resident_secondary_only_role(self) -> None:
        registry_text = TEAM_ROLES.read_text(encoding="utf-8")
        mapping = json.loads(ROLE_MAP_JSON.read_text(encoding="utf-8"))

        self.assertIn("public-historian", registry_text)
        self.assertIn("Role=Public Historian/公共史官", registry_text)
        self.assertIn("secondary-only", registry_text)
        self.assertIn("resident role", registry_text.lower())

        role = mapping["public_role_registry"]["roles"]["public-historian"]
        self.assertEqual("Role=Public Historian/公共史官", role["display"])
        self.assertEqual("secondary-only", role["classification"])
        self.assertTrue(role["resident_role"])
        self.assertFalse(role["primary_assignable"])
        self.assertTrue(role["resident_role_definition"])

    def test_role_registry_exposes_explicit_primary_and_secondary_counts(self) -> None:
        mapping = json.loads(ROLE_MAP_JSON.read_text(encoding="utf-8"))

        self.assertEqual(11, mapping["role_count"])
        self.assertEqual(10, mapping["primary_role_count"])
        self.assertGreaterEqual(mapping["secondary_role_count"], 1)

    def test_public_historian_can_only_be_reached_as_historian_secondary(self) -> None:
        mapping = json.loads(ROLE_MAP_JSON.read_text(encoding="utf-8"))
        historian = mapping["agents"]["historian"]

        self.assertEqual("观音", historian["primary_role"])
        self.assertEqual(
            {"太上老君", "沙僧"},
            set(historian["secondary_roles"]) & {"太上老君", "沙僧"},
        )
        self.assertIn("public-historian", historian["secondary_roles"])
        self.assertNotEqual("public-historian", historian["primary_role"])
        self.assertNotIn(
            "public-historian",
            [agent["primary_role"] for agent in mapping["agents"].values()],
        )

    def test_public_markdown_map_publishes_role_and_historian_mapping(self) -> None:
        text = ROLE_MAP_MD.read_text(encoding="utf-8")

        self.assertIn("public-historian", text)
        self.assertIn("Role=Public Historian/公共史官", text)
        self.assertIn("secondary-only", text)
        self.assertRegex(
            text,
            r"\| `historian` \| Historian \| 观音 \| [^|]*public-historian",
        )


if __name__ == "__main__":
    unittest.main()
