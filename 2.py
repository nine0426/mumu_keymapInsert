from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QLabel, QApplication, QMessageBox, QFileDialog
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
import os, json, sys

CONFIG_PATH = r"C:\ProgramData\keymap.json"

def resource_path(relative_path):
    """获取打包后或源码状态下的资源路径"""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class KeymapEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("宏点位插入工具")
        self.setGeometry(400, 200, 400, 120)

        # 设置窗口图标
        self.setWindowIcon(QIcon(resource_path("myicon.ico")))

        # 中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        central_widget.setLayout(main_layout)

        # 首页模板显示
        self.template_label = QLabel("新增宏点位模板：默认")
        self.template_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        main_layout.addWidget(self.template_label)

        # 顶部选择区
        top_layout = QHBoxLayout()
        label = QLabel("选择点位文件：")
        label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        top_layout.addWidget(label)

        self.file_combo = QComboBox()
        top_layout.addWidget(self.file_combo)
        main_layout.addLayout(top_layout)

        # 中部操作按钮
        btn_layout = QHBoxLayout()
        self.modify_button = QPushButton("插入宏点位并保存")
        self.delete_button = QPushButton("删除当前文件")
        btn_layout.addWidget(self.modify_button)
        btn_layout.addWidget(self.delete_button)
        main_layout.addLayout(btn_layout)

        # 菜单栏
        menubar = self.menuBar()
        file_menu = menubar.addMenu("文件")
        self.action_select_folder = file_menu.addAction("重新选择点位文件夹")
        self.action_open_folder = file_menu.addAction("打开点位文件夹")
        self.action_select_folder.triggered.connect(self.load_folder)
        self.action_open_folder.triggered.connect(self.open_folder)

        import_action = QAction("导入自定义点位模板", self)
        import_action.triggered.connect(self.import_custom_template)
        file_menu.addAction(import_action)

        # 关于菜单
        about_menu = menubar.addMenu("关于")
        action_manual = QAction("说明书", self)
        action_manual.triggered.connect(self.show_manual)
        about_menu.addAction(action_manual)

        action_author = QAction("by:我是很厉害厉害的哦", self)
        action_author.triggered.connect(self.open_author_page)
        about_menu.addAction(action_author)

        # 按钮事件
        self.modify_button.clicked.connect(self.modify_file)
        self.delete_button.clicked.connect(self.delete_file)

        # 初始化变量
        self.folder_path = None
        self.file_map = {}
        self.custom_template_path = None
        self.custom_keymaps = []

        # 初始化加载上次路径
        self.init_folder()

    def show_manual(self):
        manual_text = (
            "宏点位插入工具说明：\n\n"
            "主要功能：\n"
            "- 插入宏点位并保存：对选中的点位文件进行技能牌区域删除和新增宏点位操作，可以快速将无宏的点位添加宏，键位如下：\n"
            "  R 一键重开\n"
            "  空格 暂停\n"
            "  Ctrl 连点\n"
            "  QWE 点位\n"
            "  ASD 宏\n"
            "  Shift 变速\n"
            "  Alt 自动\n"
            "支持导入自定义模板功能，在文件内选择自己喜欢用的纯点位宏文件即可，不选择默认使用上面的布局\n\n"
            "其他功能：\n"
            "- 删除当前文件：删除选中的点位文件，删除后不可恢复。\n"
            "- 重新选择点位文件夹：选择存放点位JSON文件的文件夹。\n"
            "- 打开点位文件夹：直接打开已经当前选择的文件夹。"
        )
        QMessageBox.information(self, "说明书", manual_text)

    def import_custom_template(self):
        start_dir = self.folder_path if self.folder_path and os.path.exists(self.folder_path) else ""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择自定义模板文件",
            start_dir,
            "JSON Files (*.json)"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if "keymaps" not in data or not isinstance(data["keymaps"], list):
                    QMessageBox.warning(self, "错误", "该文件不是有效的点位模板！")
                    return
                self.custom_keymaps = data["keymaps"]
                self.custom_template_path = file_path
                template_name = os.path.basename(file_path)
                self.template_label.setText(f"新增宏点位模板：{template_name}")
                QMessageBox.information(self, "成功", f"已导入自定义模板：{template_name}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入模板失败：{str(e)}")

    def init_folder(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.folder_path = data.get("folder_path", "")
            except Exception:
                self.folder_path = ""
        if not self.folder_path or not os.path.exists(self.folder_path):
            QMessageBox.information(self, "提示", "未检测到已保存的点位路径，请选择点位文件夹。")
            self.load_folder()
        else:
            self.refresh_file_list()

    def save_folder_path(self, path):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump({"folder_path": path}, f, ensure_ascii=False, indent=2)

    def load_folder(self):
        folder = QFileDialog.getExistingDirectory(self,
                                                  r"选择点位文件夹  参考路径C:\Users\Admin\AppData\Roaming\Netease\MuMuPlayer\data\keymapConfig")
        if folder:
            self.folder_path = folder
            self.save_folder_path(folder)
            self.refresh_file_list()

    def open_folder(self):
        if self.folder_path and os.path.exists(self.folder_path):
            os.startfile(self.folder_path)
        else:
            QMessageBox.warning(self, "提示", "点位文件夹不存在，请先选择有效文件夹。")

    def refresh_file_list(self):
        self.file_combo.clear()
        self.file_map.clear()
        if not self.folder_path or not os.path.exists(self.folder_path):
            return
        excluded_files = {
            "com.nexon.bluearchive.json",
            "com.RoamingStar.BlueArchive.json",
            "com.RoamingStar.BlueArchive.bilibili.json",
            "com.RoamingStar.BlueArchive-默认操作方案.json",
            "com.nexon.bluearchive-默认操作模式.json",
            "com.RoamingStar.BlueArchive.bilibili-默认操作方案.json",
        }
        files_in_folder = [f for f in os.listdir(self.folder_path) if f.endswith(".json")]
        for file in files_in_folder:
            if file in excluded_files:
                continue
            display_name = file
            if file.startswith("com.nexon.bluearchive"):
                display_name = file.replace("com.nexon.bluearchive", "国际服点位")
            elif file.startswith("com.RoamingStar.BlueArchive.bilibili"):
                display_name = file.replace("com.RoamingStar.BlueArchive.bilibili", "B服点位")
            elif file.startswith("com.RoamingStar.BlueArchive"):
                display_name = file.replace("com.RoamingStar.BlueArchive", "官服点位")
            self.file_combo.addItem(display_name)
            self.file_map[display_name] = file
        if not self.file_map:
            QMessageBox.warning(self, "提示", "该文件夹下没有有效的点位文件。")

    def open_author_page(self):
        url = QUrl("https://space.bilibili.com/230141337")
        QDesktopServices.openUrl(url)

    def modify_file(self):
        if not self.file_combo.currentText():
            QMessageBox.warning(self, "警告", "请先选择一个点位文件！")
            return
        file_name = self.file_map[self.file_combo.currentText()]
        input_path = os.path.join(self.folder_path, file_name)
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # 删除指定区域点位
            filtered_keymaps = []
            for km in data.get("keymaps", []):
                rel_x = km.get("rel_work_position", {}).get("rel_x", 0)
                rel_y = km.get("rel_work_position", {}).get("rel_y", 0)
                if not (rel_x > 0.67 and rel_y > 0.79):
                    filtered_keymaps.append(km)
            # 使用自定义模板点位或默认新增点位
            if self.custom_keymaps:
                new_keymaps = self.custom_keymaps
            else:
                # 默认新增点位示例（请根据你的需求修改）
                new_keymaps = [
                    {
                        "editor_icon_scale": 1,
                        "icon": {
                            "background_color": "00000066",
                            "description": "",
                            "radius_correction": 1,
                            "rel_position": {
                                "rel_x": 0.9547079856972588,
                                "rel_y": 0.8686440677966102
                            },
                            "visibility": True
                        },
                        "key": {
                            "device": "keyboard",
                            "scan_code": 42,
                            "text": "Shift",
                            "virtual_key": 16
                        },
                        "rel_work_position": {
                            "rel_x": 0.9547079856972588,
                            "rel_y": 0.8686440677966102
                        },
                        "type": "Click"
                    },
                    {
                        "editor_icon_scale": 1,
                        "icon": {
                            "background_color": "00000066",
                            "description": "",
                            "radius_correction": 1,
                            "rel_position": {
                                "rel_x": 0.8649514894280045,
                                "rel_y": 0.8558014966721654
                            },
                            "visibility": True
                        },
                        "key": {
                            "device": "keyboard",
                            "scan_code": 32,
                            "text": "D",
                            "virtual_key": 68
                        },
                        "press_actions": [
                            "start_loop:until_release",
                            "curve_first_point_sleep_time:1",
                            "curve_last_point_sleep_time:until_release_cmd",
                            "curve_rel:(0.846246,0.896186);(0.851013,0.843220);mouse",
                            "curve_release",
                            "stop_loop"
                        ],
                        "rel_work_position": {
                            "rel_x": 0.8649514894280045,
                            "rel_y": 0.8558014966721654
                        },
                        "release_actions": [

                        ],
                        "type": "Macro"
                    },
                    {
                        "editor_icon_scale": 1,
                        "icon": {
                            "background_color": "00000066",
                            "description": "",
                            "radius_correction": 1,
                            "rel_position": {
                                "rel_x": 0.7824383719289509,
                                "rel_y": 0.8539144665041505
                            },
                            "visibility": True
                        },
                        "key": {
                            "device": "keyboard",
                            "scan_code": 31,
                            "text": "S",
                            "virtual_key": 83
                        },
                        "press_actions": [
                            "start_loop:until_release",
                            "curve_first_point_sleep_time:1",
                            "curve_last_point_sleep_time:until_release_cmd",
                            "curve_rel:(0.765793,0.893008);(0.771752,0.862288);mouse",
                            "curve_release",
                            "stop_loop"
                        ],
                        "rel_work_position": {
                            "rel_x": 0.7824383719289509,
                            "rel_y": 0.8539144665041505
                        },
                        "release_actions": [

                        ],
                        "type": "Macro"
                    },
                    {
                        "editor_icon_scale": 1,
                        "icon": {
                            "background_color": "00000066",
                            "description": "",
                            "radius_correction": 1,
                            "rel_position": {
                                "rel_x": 0.6959501557632397,
                                "rel_y": 0.8737541528239198
                            },
                            "visibility": True
                        },
                        "key": {
                            "device": "keyboard",
                            "scan_code": 16,
                            "text": "Q",
                            "virtual_key": 81
                        },
                        "rel_work_position": {
                            "rel_x": 0.6959501557632397,
                            "rel_y": 0.8737541528239198
                        },
                        "type": "Click"
                    },
                    {
                        "editor_icon_scale": 1,
                        "icon": {
                            "background_color": "00000066",
                            "description": "",
                            "radius_correction": 1,
                            "rel_position": {
                                "rel_x": 0.9665315542056766,
                                "rel_y": 0.05184377789044
                            },
                            "visibility": True
                        },
                        "key": {
                            "device": "keyboard",
                            "scan_code": 57,
                            "text": "Space",
                            "virtual_key": 32
                        },
                        "rel_work_position": {
                            "rel_x": 0.9665315542056766,
                            "rel_y": 0.05184377789044
                        },
                        "type": "Click"
                    },
                    {
                        "editor_icon_scale": 1,
                        "icon": {
                            "background_color": "00000066",
                            "description": "",
                            "radius_correction": 1,
                            "rel_position": {
                                "rel_x": 0.7713395638629283,
                                "rel_y": 0.8704318936877076
                            },
                            "visibility": True
                        },
                        "key": {
                            "device": "keyboard",
                            "scan_code": 17,
                            "text": "W",
                            "virtual_key": 87
                        },
                        "rel_work_position": {
                            "rel_x": 0.7713395638629283,
                            "rel_y": 0.8704318936877076
                        },
                        "type": "Click"
                    },
                    {
                        "editor_icon_scale": 1,
                        "icon": {
                            "background_color": "00000066",
                            "description": "",
                            "radius_correction": 1,
                            "rel_position": {
                                "rel_x": 0.8529595015576324,
                                "rel_y": 0.8748615725359912
                            },
                            "visibility": True
                        },
                        "key": {
                            "device": "keyboard",
                            "scan_code": 18,
                            "text": "E",
                            "virtual_key": 69
                        },
                        "rel_work_position": {
                            "rel_x": 0.8529595015576324,
                            "rel_y": 0.8748615725359912
                        },
                        "type": "Click"
                    },
                    {
                        "editor_icon_scale": 1,
                        "icon": {
                            "background_color": "00000066",
                            "description": "",
                            "radius_correction": 1,
                            "rel_position": {
                                "rel_x": 0.7075435470493948,
                                "rel_y": 0.8513726772712982
                            },
                            "visibility": True
                        },
                        "key": {
                            "device": "keyboard",
                            "scan_code": 30,
                            "text": "A",
                            "virtual_key": 65
                        },
                        "press_actions": [
                            "start_loop:until_release",
                            "curve_first_point_sleep_time:1",
                            "curve_last_point_sleep_time:until_release_cmd",
                            "curve_rel:(0.686532,0.856992);(0.694279,0.851695);mouse",
                            "curve_release",
                            "stop_loop"
                        ],
                        "rel_work_position": {
                            "rel_x": 0.7075435470493948,
                            "rel_y": 0.8513726772712982
                        },
                        "release_actions": [

                        ],
                        "type": "Macro"
                    },
                    {
                        "editor_icon_scale": 1,
                        "icon": {
                            "background_color": "00000066",
                            "description": "",
                            "radius_correction": 1,
                            "rel_position": {
                                "rel_x": 0.9673901811142316,
                                "rel_y": 0.10652879801825023
                            },
                            "visibility": True
                        },
                        "key": {
                            "device": "keyboard",
                            "scan_code": 19,
                            "text": "R",
                            "virtual_key": 82
                        },
                        "press_actions": [
                            "click_rel:(0.972586,0.081568)",
                            "sleep:50",
                            "click_rel:(0.972586,0.081568)",
                            "sleep:50",
                            "click_rel:(0.972586,0.081568)",
                            "sleep:500",
                            "click_rel:(0.439213,0.709746)",
                            "sleep:50",
                            "click_rel:(0.439213,0.709746)",
                            "sleep:50",
                            "click_rel:(0.439213,0.709746)",
                            "sleep:500",
                            "click_rel:(0.564958,0.695975)",
                            "sleep:50",
                            "click_rel:(0.564958,0.695975)",
                            "sleep:50",
                            "click_rel:(0.564958,0.695975)"
                        ],
                        "rel_work_position": {
                            "rel_x": 0.9673901811142316,
                            "rel_y": 0.10652879801825023
                        },
                        "release_actions": [

                        ],
                        "type": "Macro"
                    },
                    {
                        "editor_icon_scale": 1,
                        "icon": {
                            "background_color": "00000066",
                            "description": "",
                            "radius_correction": 1,
                            "rel_position": {
                                "rel_x": 0.9659486031789325,
                                "rel_y": 0.16279789247958604
                            },
                            "visibility": True
                        },
                        "key": {
                            "device": "keyboard",
                            "scan_code": 29,
                            "text": "Ctrl",
                            "virtual_key": 17
                        },
                        "press_actions": [
                            "start_loop:until_release",
                            "press_rel:mouse",
                            "sleep:16",
                            "release_rel:mouse",
                            "stop_loop"
                        ],
                        "rel_work_position": {
                            "rel_x": 0.9659486031789325,
                            "rel_y": 0.16279789247958604
                        },
                        "release_actions": [

                        ],
                        "type": "Macro"
                    },
                    {
                        "editor_icon_scale": 1,
                        "icon": {
                            "background_color": "00000066",
                            "description": "",
                            "radius_correction": 1,
                            "rel_position": {
                                "rel_x": 0.9547079856972588,
                                "rel_y": 0.9449152542372882
                            },
                            "visibility": True
                        },
                        "key": {
                            "device": "keyboard",
                            "scan_code": 56,
                            "text": "Alt",
                            "virtual_key": 18
                        },
                        "rel_work_position": {
                            "rel_x": 0.9547079856972588,
                            "rel_y": 0.9449152542372882
                        },
                        "type": "Click"
                    }
                ]
            filtered_keymaps.extend(new_keymaps)
            data["keymaps"] = filtered_keymaps
            with open(input_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "成功", f"文件已修改并保存：\n{file_name}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"修改文件时出错：{str(e)}")

    def delete_file(self):
        if not self.file_combo.currentText():
            QMessageBox.warning(self, "警告", "请先选择要删除的文件！")
            return
        display_name = self.file_combo.currentText()
        file_name = self.file_map[display_name]
        file_path = os.path.join(self.folder_path, file_name)
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除 {display_name} 吗？此操作不可恢复！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                os.remove(file_path)
                QMessageBox.information(self, "成功", f"{display_name} 已删除。")
                self.refresh_file_list()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除文件失败：{str(e)}")

if __name__ == "__main__":
    app = QApplication([])
    window = KeymapEditor()
    window.show()
    app.exec()
