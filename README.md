# 🏢 WIO Calculator | 办公室工作统计系统

A comprehensive Work In Office (WIO) tracking and management system built with Python Flask.

一个用Python Flask构建的全面的办公室工作(WIO)追踪和管理系统。

## 📋 Features | 功能特性

### English
- **📅 Calendar View**: Interactive monthly calendar to track daily work status
- **📊 Real-time Statistics**: Live calculation of WIO percentage and progress tracking
- **⚙️ Customizable Targets**: Set and modify your monthly WIO target percentage
- **🎄 Holiday Management**: Automatic Chinese holidays integration with custom holiday support
- **📱 Responsive Design**: Works seamlessly on desktop and mobile devices
- **💾 Data Persistence**: SQLite database ensures your data is always saved

### 中文
- **📅 日历视图**: 交互式月历，跟踪每日工作状态
- **📊 实时统计**: 实时计算WIO比例和进度跟踪
- **⚙️ 自定义目标**: 设置和修改每月WIO目标百分比
- **🎄 节假日管理**: 自动集成中国节假日，支持自定义节假日
- **📱 响应式设计**: 在桌面和移动设备上完美运行
- **💾 数据持久化**: SQLite数据库确保数据永久保存

## 🚀 Quick Start | 快速开始

### Prerequisites | 环境要求

- Python 3.7 or higher | Python 3.7或更高版本
- pip (Python package installer) | pip包管理器

### Installation & Running | 安装与运行

1. **Clone or download the project | 克隆或下载项目**
   ```bash
   git clone https://github.com/your-username/wio-calculator.git
   cd wio-calculator
   ```

2. **Install dependencies | 安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application | 运行应用程序**
   ```bash
   python server3.py
   ```

4. **Access the application | 访问应用程序**

   Open your web browser and navigate to: | 在浏览器中打开:
   ```
   http://127.0.0.1:8080
   ```

That's it! The application will automatically create the necessary database file (`wio_data.db`) on first run.

就是这样！应用程序将在首次运行时自动创建必要的数据库文件 (`wio_data.db`)。

## 📖 How to Use | 使用说明

### English

1. **Set Your WIO Target**: In the settings section, adjust your monthly WIO target percentage (default: 40%)

2. **Track Daily Status**: Click on any workday in the calendar to set your work status:
   - 🏢 **WIO**: Work in Office
   - 🏠 **WFH**: Work from Home
   - 🌴 **LEAVE**: Personal Leave
   - 🤒 **SICK**: Sick Leave

3. **Monitor Progress**: The statistics panel shows:
   - Current WIO percentage
   - Days worked in office
   - Days needed to reach target
   - Progress bar visualization

4. **Manage Holidays**: Add custom holidays or company-specific days off in the holiday management section

5. **Navigate Months**: Use the navigation arrows to view and plan for different months

### 中文

1. **设置WIO目标**: 在设置区域，调整你的月度WIO目标百分比（默认：40%）

2. **记录每日状态**: 点击日历中的任何工作日来设置工作状态:
   - 🏢 **WIO**: 办公室工作
   - 🏠 **WFH**: 居家办公
   - 🌴 **请假**: 个人假期
   - 🤒 **病假**: 病假

3. **监控进度**: 统计面板显示:
   - 当前WIO百分比
   - 办公室工作天数
   - 达到目标还需天数
   - 进度条可视化

4. **管理节假日**: 在节假日管理区域添加自定义节假日或公司特定假期

5. **导航月份**: 使用导航箭头查看和规划不同月份

## 🏗️ Technical Architecture | 技术架构

### Backend | 后端
- **Framework**: Flask 2.3.3
- **Database**: SQLite (file-based)
- **Holiday Data**: Chinese Calendar library for accurate holiday information
- **API**: RESTful endpoints for all data operations

### Frontend | 前端
- **Technologies**: HTML5, CSS3, Vanilla JavaScript
- **Design**: Modern gradient UI with responsive layout
- **Interactions**: AJAX-based dynamic updates without page refresh

### Data Model | 数据模型

#### Tables | 数据表
1. **daily_status**: Stores daily work status entries
2. **custom_holidays**: User-defined holidays and special days
3. **settings**: Application configuration (WIO targets, etc.)

## 📁 Project Structure | 项目结构

```
wio-calculator/
├── server3.py              # Main Flask application | 主Flask应用
├── requirements.txt        # Python dependencies | Python依赖
├── templates/
│   └── index.html         # Frontend interface | 前端界面
├── wio_data.db            # SQLite database (auto-created) | SQLite数据库（自动创建）
├── design.md              # Design documentation | 设计文档
└── README.md              # This file | 说明文件
```

## 🔧 API Endpoints | API接口

| Endpoint | Method | Description | 描述 |
|----------|--------|-------------|------|
| `/api/month_data` | GET | Get calendar and stats for specific month | 获取指定月份的日历和统计数据 |
| `/api/day_status` | POST | Update daily work status | 更新每日工作状态 |
| `/api/settings` | GET/POST | Manage application settings | 管理应用设置 |
| `/api/holidays` | GET/POST/DELETE | Manage custom holidays | 管理自定义节假日 |

## 🎯 WIO Calculation Logic | WIO计算逻辑

The WIO percentage is calculated as: | WIO百分比计算公式:

```
WIO % = (WIO Days / Total Workdays) × 100%
```

**Total Workdays exclude | 总工作日不包括:**
- Weekends | 周末
- Chinese public holidays | 中国法定节假日
- Custom holidays you've added | 你添加的自定义节假日
- Personal leave days | 个人请假天数
- Sick leave days | 病假天数

## 🛠️ Troubleshooting | 故障排除

### Common Issues | 常见问题

1. **ModuleNotFoundError: No module named 'chinesecalendar' | 找不到chinesecalendar模块**

   The app will work without this module (with basic weekend detection only). To install it:
   应用程序在没有此模块的情况下也能工作（仅基本周末检测）。要安装它：

   ```bash
   # For system Python | 系统Python
   pip install chinesecalendar

   # For virtual environment | 虚拟环境
   # Activate venv first | 先激活虚拟环境
   source venv/bin/activate  # Linux/Mac
   # or | 或者
   venv\Scripts\activate     # Windows
   pip install chinesecalendar
   ```

2. **Port already in use | 端口已被使用**
   ```bash
   # The app now runs on port 8080 by default | 应用现在默认在8080端口运行
   # If still conflicts, modify port in server3.py line 305
   # 如果仍有冲突，修改server3.py第305行的端口号
   ```

3. **Dependencies not installing | 依赖安装失败**
   ```bash
   # Upgrade pip first | 先升级pip
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Database permission issues | 数据库权限问题**

   Make sure the application directory is writable | 确保应用目录有写入权限

5. **Virtual environment issues | 虚拟环境问题**

   If virtual environment has issues, try running with system Python:
   如果虚拟环境有问题，尝试使用系统Python运行：

   ```bash
   # Install dependencies globally | 全局安装依赖
   pip install Flask Flask-CORS
   python server3.py
   ```


## 🤝 Contributing | 贡献

Contributions are welcome! Please feel free to submit a Pull Request.

欢迎贡献！请随时提交Pull Request。

## 📞 Support | 支持

If you encounter any issues or have questions, please:

如果遇到任何问题或有疑问，请:

1. Check this README for common solutions | 查看此README中的常见解决方案
2. Create an issue in the GitHub repository | 在GitHub仓库中创建issue
3. Ensure you're using the correct Python version | 确保使用正确的Python版本

---

**Happy tracking! | 愉快追踪！** 🎉
