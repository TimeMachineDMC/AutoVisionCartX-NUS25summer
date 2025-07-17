# 🚗 智能配送小车 · AutoVisionCart X
> 基于 YOLOv8 的多目标识别与自动驾驶演示项目  
> Smart Delivery Robot: YOLOv8-based Multi-Object Detection & Autonomous Driving

---

## 项目简介 | Project Introduction

本项目实现了一个基于深度学习的智能小车，可识别多种目标（如香蕉、书、elderly、young）并进行自动驾驶。系统集成了目标检测（YOLOv8）、摄像头流、Web 控制、批量数据标注与自动修正等功能，可实时运行于树莓派/PC。

This project demonstrates a deep-learning-powered delivery robot that can recognize multiple objects (banana, book, elderly, young, etc.) and drive autonomously. The system integrates object detection (YOLOv8), camera streaming, web control, batch labeling & data fixing tools, and can run in real time on Raspberry Pi or PC.

---

## 安装与运行 | Installation & Usage

### 环境安装 | Environment

建议使用 Python 3.12，推荐虚拟环境：

```bash
git clone https://github.com/yourname/yourrepo.git
cd yourrepo
python -m venv venv
source venv/bin/activate   # Windows 用 venv\Scripts\activate
pip install -r requirements.txt
```

### 数据检测/推理 | Detection Demo

实时检测所有目标（每秒检测一次）：

```bash
python yolo_keep_detect_all.py
```

### 主控/前端界面 | Main Controller (Web + Autopilot)

```bash
python main_controller.py
```

## 数据集说明 | Dataset
本项目支持 banana、book、elderly、young 四类对象。

所有数据采用 YOLO 标注格式，标签修正和批量修改均有脚本辅助完成。

## 项目亮点 | Features
🚗 实时多目标识别与跟踪

🌐 Web 控制 & 视频流展示

🔄 支持批量修正 YOLO 标签格式

🤖 支持自定义类别扩展

⚡ 高效，适配树莓派/PC

## 致谢 | Acknowledgement
感谢 Ultralytics YOLOv8 社区与开源生态。

## License
MIT

如有任何问题欢迎提 issue / 联系作者！
Feel free to open an issue or contact for any question.


