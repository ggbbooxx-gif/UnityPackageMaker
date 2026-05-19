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

    def test_raw_directory_can_customize_content_folder_name(self) -> None:
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
                create_tgz=False,
                source_mode="raw",
                content_folder_name="Content",
            )

            result = export_package(metadata, options)

            self.assertTrue((result.package_dir / "Runtime" / "Content" / "Example.cs").exists())
            self.assertFalse((result.package_dir / "Runtime" / "ImportedContent").exists())

    def test_raw_directory_can_omit_content_folder_name(self) -> None:
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
                create_tgz=False,
                source_mode="raw",
                content_folder_name="",
            )

            result = export_package(metadata, options)

            self.assertTrue((result.package_dir / "Runtime" / "Example.cs").exists())
            self.assertFalse((result.package_dir / "Runtime" / "ImportedContent").exists())

    def test_raw_directory_generates_runtime_and_editor_asmdefs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_dir = root / "JokerTools"
            output_dir = root / "out"
            (source_dir / "Setting").mkdir(parents=True)
            (source_dir / "AssetBundleUtility" / "Editor").mkdir(parents=True)

            (source_dir / "Setting" / "JkLocalSetting.cs").write_text(
                "namespace JokerTools.Settings { public class JkSettingData {} }",
                encoding="utf-8",
            )
            (source_dir / "AssetBundleUtility" / "Editor" / "JkABBuilder.cs").write_text(
                "using JokerTools.Settings; public class JkABBuilder { JkSettingData data; }",
                encoding="utf-8",
            )

            metadata = PackageMetadata(
                name="com.example.jokertools",
                display_name="JokerTools",
                version="1.0.0",
                unity_version="2022.3",
                description="Asmdef export",
                author_name="Tester",
            )
            options = ExportOptions(
                source_dir=source_dir,
                output_dir=output_dir,
                package_slug="jokertools",
                create_tgz=False,
                source_mode="raw",
            )

            result = export_package(metadata, options)

            runtime_asmdef = json.loads((result.package_dir / "Runtime" / "com.example.jokertools.asmdef").read_text(encoding="utf-8"))
            editor_asmdef = json.loads((result.package_dir / "Editor" / "com.example.jokertools.Editor.asmdef").read_text(encoding="utf-8"))

            self.assertEqual(runtime_asmdef["name"], "com.example.jokertools")
            self.assertEqual(editor_asmdef["name"], "com.example.jokertools.Editor")
            self.assertEqual(editor_asmdef["includePlatforms"], ["Editor"])
            self.assertEqual(editor_asmdef["references"], ["com.example.jokertools"])

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

    def test_upm_directory_generates_missing_asmdefs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_dir = root / "AlreadyUpm"
            runtime_dir = source_dir / "Runtime"
            editor_dir = source_dir / "Editor"
            output_dir = root / "out"
            runtime_dir.mkdir(parents=True)
            editor_dir.mkdir(parents=True)
            (runtime_dir / "Tool.cs").write_text("public class Tool {}", encoding="utf-8")
            (editor_dir / "ToolEditor.cs").write_text("public class ToolEditor {}", encoding="utf-8")

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

            self.assertTrue((result.package_dir / "Runtime" / "com.example.toolkit.asmdef").exists())
            self.assertTrue((result.package_dir / "Editor" / "com.example.toolkit.Editor.asmdef").exists())

    def test_raw_directory_hoists_nested_editor_folders_out_of_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_dir = root / "JokerTools"
            output_dir = root / "out"
            asset_dir = source_dir / "AssetBundleUtility"
            editor_dir = asset_dir / "Editor"
            setting_dir = source_dir / "Setting"
            ui_dir = source_dir / "UI"
            ui_editor_dir = ui_dir / "Editor"

            editor_dir.mkdir(parents=True)
            setting_dir.mkdir(parents=True)
            ui_editor_dir.mkdir(parents=True)

            (asset_dir / "JkABNameStrategy.cs").write_text("public interface IABNameStrategy {}", encoding="utf-8")
            (editor_dir / "JkABBuilder.cs").write_text("public class JkABBuilder {}", encoding="utf-8")
            (setting_dir / "JkLocalSetting.cs").write_text("namespace JokerTools.Settings { public class JkSettingData {} }", encoding="utf-8")
            (ui_dir / "JkHorizontalUIPopupGroup.cs").write_text("public class JkHorizontalUIPopupGroup {}", encoding="utf-8")
            (ui_editor_dir / "JkHorizontalUIPopupGroupEditor.cs").write_text("public class JkHorizontalUIPopupGroupEditor {}", encoding="utf-8")

            metadata = PackageMetadata(
                name="com.example.jokertools",
                display_name="JokerTools",
                version="1.0.0",
                unity_version="2022.3",
                description="Unity asset style export",
                author_name="Tester",
            )
            options = ExportOptions(
                source_dir=source_dir,
                output_dir=output_dir,
                package_slug="jokertools",
                create_tgz=False,
                source_mode="raw",
            )

            result = export_package(metadata, options)

            self.assertTrue((result.package_dir / "Runtime" / "ImportedContent" / "AssetBundleUtility" / "JkABNameStrategy.cs").exists())
            self.assertTrue((result.package_dir / "Runtime" / "ImportedContent" / "Setting" / "JkLocalSetting.cs").exists())
            self.assertTrue((result.package_dir / "Runtime" / "ImportedContent" / "UI" / "JkHorizontalUIPopupGroup.cs").exists())
            self.assertTrue((result.package_dir / "Editor" / "ImportedContent" / "AssetBundleUtility" / "JkABBuilder.cs").exists())
            self.assertTrue((result.package_dir / "Editor" / "ImportedContent" / "UI" / "JkHorizontalUIPopupGroupEditor.cs").exists())
            self.assertFalse((result.package_dir / "Runtime" / "ImportedContent" / "AssetBundleUtility" / "Editor").exists())
            self.assertFalse((result.package_dir / "Runtime" / "ImportedContent" / "AssetBundleUtility" / "Editor.meta").exists())
            self.assertFalse((result.package_dir / "Runtime" / "ImportedContent" / "UI" / "Editor").exists())
            self.assertFalse((result.package_dir / "Runtime" / "ImportedContent" / "UI" / "Editor.meta").exists())


if __name__ == "__main__":
    unittest.main()
