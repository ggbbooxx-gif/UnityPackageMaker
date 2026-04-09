from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from PyQt6.QtWidgets import QApplication

from unity_package_maker.app import MainWindow


class AppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_main_window_constructs_without_attribute_error(self) -> None:
        window = MainWindow()
        self.assertIsNotNone(window.log_output)
        self.assertEqual(window.log_output.toPlainText(), "准备就绪。")
        window.close()


if __name__ == "__main__":
    unittest.main()