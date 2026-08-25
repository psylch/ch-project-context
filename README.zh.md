# ch-project-context

[English](README.md)

一个通过 [skills.sh](https://skills.sh/) 分发的项目上下文管理技能，支持 Claude Code、Codex 或同时支持两者。

## 功能

运行 `/ch-project-context init` 后：

1. 创建用于计划、决策、研究、已知问题和归档的结构化 `docs/` 目录。
2. 安装会话启动、子 agent 上下文和文档校验 hooks。
3. 按目标写入 `.claude/`、`.codex/` 或两者，并保持配置格式相互独立。
4. 将文档导航块写入 `CLAUDE.md`、`AGENTS.md` 或两者。
5. 在文件尚不存在时创建 `docs/architecture.md`。

Claude Code 使用 `SessionStart` 和 `PreToolUse` 增强子 agent 提示；Codex 使用原生 `SessionStart` 与 `SubagentStart` 注入上下文。

## 安装

```bash
npx skills add psylch/ch-project-context -g -y
```

需要 Python 3.6+，脚本没有第三方依赖。

Codex 的项目级 hooks 要求所选项目根目录是 Git 仓库；仅初始化 Claude 时仍可用于非 Git 项目目录。

## 使用

在 agent 会话中运行：

```text
/ch-project-context init
```

技能会询问目标环境（`claude`、`codex` 或 `both`）和文档语言，检查已有文件，完成初始化并验证生成的 hooks。

也可以直接运行底层脚本：

```bash
python3 skills/ch-project-context/scripts/init.py \
  --root /path/to/project \
  --target codex
```

为保持向后兼容，直接运行脚本时默认使用 `--target claude`。

Codex 的项目级 hooks 在运行前需要通过 `/hooks` 检查并信任。

## 许可证

MIT
