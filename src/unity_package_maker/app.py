from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from unity_package_maker.exporter import ExportOptions, PackageMetadata, export_package


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Unity Package Maker")
        self.resize(920, 700)
        self._build_ui()
        self._apply_defaults()

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setSpacing(12)

        intro = QLabel("选择一个目录，导出为 Unity 2022 可通过 Package Manager 添加的 UPM 包。")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        layout.addWidget(self._build_paths_group())
        layout.addWidget(self._build_metadata_group())
        layout.addWidget(self._build_options_group())

        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setPlaceholderText("导出日志会显示在这里。")

        layout.addWidget(self._build_actions_row())
        layout.addWidget(self.log_output, 1)

    def _build_paths_group(self) -> QGroupBox:
        box = QGroupBox("目录")
        grid = QGridLayout(box)
        grid.setColumnStretch(1, 1)

        self.source_input = QLineEdit()
        self.output_input = QLineEdit()

        source_button = QPushButton("选择源目录")
        source_button.clicked.connect(self._choose_source_dir)
        output_button = QPushButton("选择输出目录")
        output_button.clicked.connect(self._choose_output_dir)

        grid.addWidget(QLabel("源目录"), 0, 0)
        grid.addWidget(self.source_input, 0, 1)
        grid.addWidget(source_button, 0, 2)
        grid.addWidget(QLabel("输出目录"), 1, 0)
        grid.addWidget(self.output_input, 1, 1)
        grid.addWidget(output_button, 1, 2)
        return box

    def _build_metadata_group(self) -> QGroupBox:
        box = QGroupBox("包信息")
        form = QFormLayout(box)

        self.package_name_input = QLineEdit()
        self.display_name_input = QLineEdit()
        self.version_input = QLineEdit()
        self.unity_input = QLineEdit()
        self.description_input = QLineEdit()
        self.author_name_input = QLineEdit()
        self.author_email_input = QLineEdit()
        self.author_url_input = QLineEdit()
        self.package_slug_input = QLineEdit()
        self.content_folder_input = QLineEdit()

        form.addRow("Package Name", self.package_name_input)
        form.addRow("Display Name", self.display_name_input)
        form.addRow("Version", self.version_input)
        form.addRow("Unity", self.unity_input)
        form.addRow("Description", self.description_input)
        form.addRow("Author", self.author_name_input)
        form.addRow("Email", self.author_email_input)
        form.addRow("URL", self.author_url_input)
        form.addRow("导出目录名", self.package_slug_input)
        form.addRow("内容子目录", self.content_folder_input)
        return box

    def _build_options_group(self) -> QGroupBox:
        box = QGroupBox("导出选项")
        row = QHBoxLayout(box)

        self.mode_select = QComboBox()
        self.mode_select.addItem("自动识别", userData="auto")
        self.mode_select.addItem("源目录已是 UPM 结构", userData="upm")
        self.mode_select.addItem("普通目录打包到 Runtime", userData="raw")

        self.create_tgz_checkbox = QCheckBox("同时生成 `.tgz`")
        self.create_tgz_checkbox.setChecked(True)
        self.overwrite_checkbox = QCheckBox("覆盖已有导出")
        self.overwrite_checkbox.setChecked(True)

        row.addWidget(QLabel("源目录模式"))
        row.addWidget(self.mode_select)
        row.addWidget(self.create_tgz_checkbox)
        row.addWidget(self.overwrite_checkbox)
        row.addStretch(1)
        return box

    def _build_actions_row(self) -> QWidget:
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)

        autofill_button = QPushButton("根据目录自动填充")
        autofill_button.clicked.connect(self._autofill_from_source)
        export_button = QPushButton("开始导出")
        export_button.clicked.connect(self._export)
        clear_log_button = QPushButton("清空日志")
        clear_log_button.clicked.connect(self.log_output.clear)

        row.addWidget(autofill_button)
        row.addWidget(export_button)
        row.addWidget(clear_log_button)
        row.addStretch(1)
        return container

    def _apply_defaults(self) -> None:
        self.version_input.setText("1.0.0")
        self.unity_input.setText("2022.3")
        self.author_name_input.setText("Your Name")
        self.package_name_input.setText("com.company.package")
        self.display_name_input.setText("My Package")
        self.package_slug_input.setText("my-package")
        self.content_folder_input.setText("ImportedContent")
        self.description_input.setText("Exported with Unity Package Maker")
        self.log("准备就绪。")

    def _choose_source_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "选择源目录")
        if directory:
            self.source_input.setText(directory)
            self._autofill_from_source()

    def _choose_output_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if directory:
            self.output_input.setText(directory)

    def _autofill_from_source(self) -> None:
        source_text = self.source_input.text().strip()
        if not source_text:
            return
        source_path = Path(source_text)
        if not source_path.exists():
            return

        slug = source_path.name.lower().replace(" ", "-").replace("_", "-")
        company_token = source_path.parent.name.lower().replace(" ", "-") if source_path.parent.name else "company"
        package_name = f"com.{company_token}.{slug}".replace("--", "-")

        self.package_slug_input.setText(slug)
        self.display_name_input.setText(source_path.name)
        self.package_name_input.setText(package_name)
        if not self.output_input.text().strip():
            self.output_input.setText(str(source_path.parent / "Exports"))
        self.log("已根据源目录更新默认包信息。")

    def _collect_metadata(self) -> PackageMetadata:
        return PackageMetadata(
            name=self.package_name_input.text().strip(),
            display_name=self.display_name_input.text().strip(),
            version=self.version_input.text().strip(),
            unity_version=self.unity_input.text().strip(),
            description=self.description_input.text().strip(),
            author_name=self.author_name_input.text().strip(),
            author_email=self.author_email_input.text().strip(),
            author_url=self.author_url_input.text().strip(),
        )

    def _collect_options(self) -> ExportOptions:
        return ExportOptions(
            source_dir=Path(self.source_input.text().strip()),
            output_dir=Path(self.output_input.text().strip()),
            package_slug=self.package_slug_input.text().strip(),
            create_tgz=self.create_tgz_checkbox.isChecked(),
            overwrite=self.overwrite_checkbox.isChecked(),
            source_mode=self.mode_select.currentData(),
            content_folder_name=self.content_folder_input.text(),
        )

    def _export(self) -> None:
        try:
            metadata = self._collect_metadata()
            options = self._collect_options()
            if not options.package_slug:
                raise ValueError("导出目录名不能为空。")
            self.log_output.clear()
            self.log("开始导出...")
            result = export_package(metadata, options, log=self.log)
            message = [
                f"目录包: {result.package_dir}",
                f"package.json: {result.package_json_path}",
                f"导出模式: {result.copied_mode}",
            ]
            if result.tarball_path:
                message.append(f"tgz: {result.tarball_path}")
            self.log("导出成功。")
            QMessageBox.information(self, "导出完成", "\n".join(message))
        except Exception as error:
            self.log(f"导出失败: {error}")
            QMessageBox.critical(self, "导出失败", str(error))

    def log(self, message: str) -> None:
        self.log_output.appendPlainText(message)
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        QApplication.processEvents()



def run() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Unity Package Maker")
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()
    return app.exec()
