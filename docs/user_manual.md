# 用户手册

## 1. 安装

1. 安装后双击 `maritime_english_trainer.exe` 启动。
2. 首次运行前确认以下目录存在并可写：
- `models/whisper`
- `models/sbert`
- `corpus/db`

## 2. 首次准备

1. 下载模型：`python scripts/download_models.py`
2. 初始化语料库：`python scripts/seed_corpus.py`
3. 启动客户端：`cd src; python main.py`

## 3. 学生端使用流程

1. 在 Practice 页输入学号（Student ID）。
2. 可按类别筛选题目，点击 `Next Phrase` 切题。
3. 按住 `HOLD TO SPEAK` 录音，松开结束。
4. 点击 `Submit` 等待评分。
5. 在 Result 页查看分数、等级、差异高亮与错误词。
6. 在 Progress 页查看历史趋势与近次记录。

## 4. 常见问题

1. 麦克风报错：检查系统麦克风权限并重启应用。
2. 模型加载慢：首次加载 Whisper 属正常现象。
3. 无成绩记录：确认 `Student ID` 非空且提交后无报错。
