# ch-project-context

[English](README.md)

一个 [skills.sh](https://skills.sh/) 技能，用于 Claude Code，一条命令即可为项目搭建上下文管理系统。

## 功能

在 Claude Code 会话中运行 `/ch-project-context init` 将会：

1. 创建结构化的 `docs/` 目录（`exec-plans/`、`decisions/`、`research/`、`known-issues/`、`archive/`）
2. 安装两个 Claude Code hooks：
   - **session-start** -- 每次新会话自动注入活跃计划、已知问题和工作流规则
   - **quality-gate** -- 阻止子 agent 完成，直到构建通过并有验证证据
3. 将 hooks 写入 `.claude/settings.json`
4. 在 `CLAUDE.md` 中追加文档导航块
5. 可选创建 `docs/architecture.md` 骨架

所有生成的文档使用 YAML frontmatter，便于 hooks 程序化解析。

## 安装

### 通过 skills.sh（推荐）

```bash
npx skills add psylch/ch-project-context -g -y
```

### 手动安装

```bash
git clone https://github.com/psylch/ch-project-context.git ~/.claude/skills/ch-project-context
```

安装后需重启 agent。

## 前置条件

- 支持 [skills.sh](https://skills.sh/) 的 AI 编程 agent（Claude Code、Cursor、Windsurf 等）
- **Python 3.6+**（运行技能脚本，零外部依赖）

## 使用方法

在任意 Claude Code 会话中：

```
/ch-project-context init
```

技能会自动检测项目根目录，检查已有文件（覆盖前会提示确认），运行初始化脚本，并报告创建了哪些内容。

## 自定义

初始化后可以自定义：

- **`.claude/hooks/quality-gate.py`** -- 将 `BUILD_CMD` 从 `['npx', 'tsc', '--noEmit']` 改为你项目的构建检查命令（如 `['cargo', 'check']`、`['ruff', 'check', '.']`）
- **`docs/workflow.md`** -- 创建此文件，自动将团队工作流规则注入每次会话

## 许可证

MIT
