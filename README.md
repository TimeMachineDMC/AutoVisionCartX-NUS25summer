# 🚗 智能配送小车 · AutoVisionCart X
> 基于 YOLOv8 和 Whisper 的多目标识别与自动驾驶演示项目  
> Smart Delivery Robot: YOLOv8&Whisper-based Multi-Object Detection & Autonomous Driving

---

## 作者

Deep Learning Expert Huang Zitong [@TimeMachineDMC](https://github.com/TimeMachineDMC)

Deep Learning Expert Wang Chenghao [@voldbaboon](https://github.com/voldbaboon)

Robotics Expert Liu Dingfu [@Severus-Snap](https://github.com/Severus-Snap)

Robotics Expert Zhou Nanxu [@Provence-24](https://github.com/Provence-24)

## 项目简介 | Project Introduction

我们开发了一个集成深度学习和机器人技术的智能订购和交付系统。基于 Flask 的网络界面结合语音识别功能，将客户和供应商连接起来。3D 打印产品通过 yolo 进行识别，由机械臂抓取，并通过自动驾驶汽车进行交付。一般来说，深度学习为物体识别提供动力，而机器人则负责自动取送操作。

We developed an intelligent ordering and delivery system integrating deep learning and robotics. A Flask-based web interface combined voice recognition  connects customers and vendors. 3D-printed products are recognized using yolo, grasped by a robotic arm, and delivered via autonomous vehicles. In general, deep learning powers object recognition, while robotics handles automated pick-and-deliver operations.

---

## 安装与运行 | Installation & Usage

### 环境安装 | Environment

建议使用 Python 3.12，推荐虚拟环境：

```bash
git clone https://github.com/TimeMachineDMC/AutoVisionCartX-NUS25summer
cd AutoVisionCartX-NUS25summer
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

This project supports objects including banana, book, elderly and young people.

All data are in YOLO annotation format, and label correction and batch modification are done with the help of scripts.

## 项目亮点 | Features
🚗 实时多目标识别与跟踪 | Real-time multi-target recognition and tracking

🌐 Web 控制 & 视频流展示 | Web Control & Video Streaming

🤖 自动化脚本 | Automation Script

⚡ 高效，适配树莓派/PC | Highly efficient, adaptable to Raspberry Pi/PC

## 致谢 | Acknowledgement
感谢 Ultralytics YOLOv8 社区与开源生态。

Thanks to the Ultralytics YOLOv8 community and open source ecosystem.

## License
MIT

--- 

如有任何问题欢迎提 issue / 联系作者！

Feel free to open an issue or contact for any question.


