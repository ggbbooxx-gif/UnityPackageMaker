from __future__ import annotations

import json
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from unity_package_maker.exporter import ExportOptions, PackageMetadata, export_package


class ExporterTests(unittest.TestCase):
    def test_raw_directory_exports_to_runtime_and_tgz(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_dir = root / "MyFeature"
            output_dir = root / "out"
            source_dir.mkdir()
            (source_dir / "Example.cs").write_text("public class Example {}", encoding="utf-8")

            metadata = PackageMetadata(
                name="com.example.myfeature",
                display_name="My Feature",
                version="1.2.3",
                unity_version="2022.3",
                description="Example export",
                author_name="Tester",
            )
            options = ExportOptions(
                source_dir=source_dir,
                output_dir=output_dir,
                package_slug="my-feature",
                create_tgz=True,
                source_mode="raw",
            )

            result = export_package(metadata, options)

            self.assertTrue((result.package_dir / "Runtime" / "ImportedContent" / "Example.cs").exists())
            package_json = json.loads(result.package_json_path.read_text(encoding="utf-8"))
            self.assertEqual(package_json["name"], "com.example.myfeature")
            self.assertIsNotNone(result.tarball_path)
            assert result.tarball_path is not None
            with tarfile.open(result.tarball_path, "r:gz") as archive:
                member_names = archive.getnames()
            self.assertIn("package/package.json", member_names)

    def test_upm_directory_keeps_runtime_layout(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_dir = root / "AlreadyUpm"
            runtime_dir = source_dir / "Runtime"
            output_dir = root / "out"
            runtime_dir.mkdir(parents=True)
            (runtime_dir / "Tool.cs").write_text("public class Tool {}", encoding="utf-8")

            metadata = PackageMetadata(
                name="com.example.toolkit",
                display_name="Toolkit",
                version="1.0.0",
                unity_version="2022.3",
                description="UPM structure export",
                author_name="Tester",
            )
            options = ExportOptions(
                source_dir=source_dir,
                output_dir=output_dir,
                package_slug="toolkit",
                create_tgz=False,
                source_mode="upm",
            )

            result = export_package(metadata, options)
            self.assertTrue((result.package_dir / "Runtime" / "Tool.cs").exists())
            self.assertIsNone(result.tarball_path)


if __name__ == "__main__":
    unittest.main()
