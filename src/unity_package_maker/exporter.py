from __future__ import annotations

import json
import os
import re
import shutil
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

_LOG = Callable[[str], None]

PACKAGE_NAME_PATTERN = re.compile(r"^[a-z0-9]+(\.[a-z0-9][a-z0-9-_]*)+$")
IGNORED_NAMES = {
    ".git",
    ".vs",
    ".vscode",
    "__pycache__",
    ".DS_Store",
    "Thumbs.db",
}
IGNORED_SUFFIXES = {".pyc", ".pyo"}
UPM_MARKER_DIRS = {"Runtime", "Editor", "Documentation~", "Samples~", "Tests"}


@dataclass(slots=True)
class PackageMetadata:
    name: str
    display_name: str
    version: str
    unity_version: str
    description: str
    author_name: str
    author_email: str = ""
    author_url: str = ""
    keywords: tuple[str, ...] = ()


@dataclass(slots=True)
class ExportOptions:
    source_dir: Path
    output_dir: Path
    package_slug: str
    create_tgz: bool = True
    overwrite: bool = True
    source_mode: str = "auto"


@dataclass(slots=True)
class ExportResult:
    package_dir: Path
    package_json_path: Path
    tarball_path: Path | None
    copied_mode: str


def validate_metadata(metadata: PackageMetadata) -> None:
    if not PACKAGE_NAME_PATTERN.match(metadata.name):
        raise ValueError("包名必须类似 `com.company.package-name`，且只能使用小写字母、数字、点和中划线/下划线。")
    if not metadata.display_name.strip():
        raise ValueError("Display Name 不能为空。")
    if not re.match(r"^\d+\.\d+\.\d+$", metadata.version):
        raise ValueError("版本号必须是语义化版本，例如 1.0.0。")
    if not re.match(r"^\d{4}\.\d+$", metadata.unity_version):
        raise ValueError("Unity 版本格式必须类似 2022.3。")


def detect_source_mode(source_dir: Path) -> str:
    if (source_dir / "package.json").exists():
        return "upm"
    child_names = {child.name for child in source_dir.iterdir() if child.is_dir()}
    if child_names & UPM_MARKER_DIRS:
        return "upm"
    return "raw"


def export_package(metadata: PackageMetadata, options: ExportOptions, log: _LOG | None = None) -> ExportResult:
    logger = log or (lambda _message: None)
    validate_metadata(metadata)

    source_dir = options.source_dir.resolve()
    output_dir = options.output_dir.resolve()

    if not source_dir.exists() or not source_dir.is_dir():
        raise ValueError("源目录不存在。")

    output_dir.mkdir(parents=True, exist_ok=True)
    package_dir = output_dir / options.package_slug

    if package_dir.exists():
        if not options.overwrite:
            raise FileExistsError(f"目标目录已存在: {package_dir}")
        logger(f"删除旧导出目录: {package_dir}")
        shutil.rmtree(package_dir)

    package_dir.mkdir(parents=True, exist_ok=True)

    resolved_mode = options.source_mode
    if resolved_mode == "auto":
        resolved_mode = detect_source_mode(source_dir)
    logger(f"使用导出模式: {resolved_mode}")

    if resolved_mode == "upm":
        _copy_source_as_package_root(source_dir, package_dir, logger)
    else:
        _copy_raw_source_into_runtime(source_dir, package_dir, logger)

    package_json_path = package_dir / "package.json"
    _write_package_json(package_json_path, metadata)
    _ensure_readme(package_dir, metadata)

    tarball_path: Path | None = None
    if options.create_tgz:
        tarball_path = output_dir / f"{options.package_slug}-{metadata.version}.tgz"
        logger(f"生成 tarball: {tarball_path}")
        _create_tgz(package_dir, tarball_path)

    logger("导出完成。")
    return ExportResult(
        package_dir=package_dir,
        package_json_path=package_json_path,
        tarball_path=tarball_path,
        copied_mode=resolved_mode,
    )


def _should_ignore(path: Path) -> bool:
    return path.name in IGNORED_NAMES or path.suffix.lower() in IGNORED_SUFFIXES


def _copy_source_as_package_root(source_dir: Path, package_dir: Path, log: _LOG) -> None:
    for item in source_dir.iterdir():
        if _should_ignore(item):
            continue
        destination = package_dir / item.name
        if item.is_dir():
            log(f"复制目录: {item.name}")
            shutil.copytree(item, destination, dirs_exist_ok=True, ignore=shutil.ignore_patterns(*IGNORED_NAMES, "*.pyc", "*.pyo"))
        else:
            log(f"复制文件: {item.name}")
            shutil.copy2(item, destination)



def _copy_raw_source_into_runtime(source_dir: Path, package_dir: Path, log: _LOG) -> None:
    runtime_dir = package_dir / "Runtime" / "ImportedContent"
    runtime_dir.mkdir(parents=True, exist_ok=True)

    for item in source_dir.iterdir():
        if _should_ignore(item):
            continue
        destination = runtime_dir / item.name
        if item.is_dir():
            log(f"导入目录到 Runtime: {item.name}")
            shutil.copytree(item, destination, dirs_exist_ok=True, ignore=shutil.ignore_patterns(*IGNORED_NAMES, "*.pyc", "*.pyo"))
        else:
            log(f"导入文件到 Runtime: {item.name}")
            shutil.copy2(item, destination)



def _write_package_json(package_json_path: Path, metadata: PackageMetadata) -> None:
    package_json = {
        "name": metadata.name,
        "displayName": metadata.display_name,
        "version": metadata.version,
        "unity": metadata.unity_version,
        "description": metadata.description.strip() or metadata.display_name,
        "author": {
            "name": metadata.author_name.strip() or "Unknown",
        },
    }
    if metadata.author_email.strip():
        package_json["author"]["email"] = metadata.author_email.strip()
    if metadata.author_url.strip():
        package_json["author"]["url"] = metadata.author_url.strip()
    if metadata.keywords:
        package_json["keywords"] = [keyword for keyword in metadata.keywords if keyword.strip()]

    package_json_path.write_text(
        json.dumps(package_json, ensure_ascii=False, indent=2) + os.linesep,
        encoding="utf-8",
    )



def _ensure_readme(package_dir: Path, metadata: PackageMetadata) -> None:
    readme_path = package_dir / "README.md"
    if readme_path.exists():
        return
    readme_content = (
        f"# {metadata.display_name}\n\n"
        f"{metadata.description.strip() or 'Unity Package Manager package exported by Unity Package Maker.'}\n\n"
        f"- Package Name: `{metadata.name}`\n"
        f"- Version: `{metadata.version}`\n"
        f"- Unity: `{metadata.unity_version}`\n"
    )
    readme_path.write_text(readme_content, encoding="utf-8")



def _create_tgz(package_dir: Path, tarball_path: Path) -> None:
    if tarball_path.exists():
        tarball_path.unlink()

    with tempfile.TemporaryDirectory(prefix="upm-tar-") as temp_dir:
        temp_root = Path(temp_dir)
        npm_package_root = temp_root / "package"
        shutil.copytree(package_dir, npm_package_root, dirs_exist_ok=True)
        with tarfile.open(tarball_path, "w:gz") as archive:
            archive.add(npm_package_root, arcname="package")
