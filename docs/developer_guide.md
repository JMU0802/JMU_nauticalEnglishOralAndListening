# 开发者指南

## 1. 代码结构

- `src/main.py`：程序入口。
- `src/nautical_english/ui/`：PyQt6 界面层。
- `src/nautical_english/ui/app_controller.py`：UI 与业务的控制器。
- `src/nautical_english/ui/worker.py`：模型加载与会话运行线程。
- `src/nautical_english/asr|nlp|feedback|training`：核心能力层。

## 2. UI 联动约定

1. `PracticeView` 只负责采集输入与触发事件。
2. `AppController` 负责模型状态、短语选择与会话执行。
3. `ResultView` 与 `ProgressView` 为纯展示层。
4. `MainWindow` 负责信号绑定与页面跳转。

## 3. 本地开发命令

1. 安装依赖：`pip install -r requirements.txt`
2. 运行测试：`pytest tests/ -v`
3. 覆盖率：`pytest tests/ --cov=nautical_english --cov-report=term-missing`
4. 启动应用：`cd src; python main.py`

## 4. 性能与打包

1. 基准脚本：`python scripts/benchmark.py`
2. 生成 spec：`python scripts/build_installer.py --spec-only`
3. 正式打包：`python scripts/build_installer.py`

## 5. 扩展建议

1. 将管理员看板接入真实聚合查询。
2. 增加 UI 自动化测试（QtBot）。
3. 将模型加载状态缓存到本地，减少冷启动等待。
