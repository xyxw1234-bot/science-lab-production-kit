# 跨智能体入口与项目级安装

## 不安装也能用

任何可读取仓库的智能体都可从根目录 START-HERE.md 和 SKILL.md 开始，按引用读取附件。网页摘要不等于已获取完整套件；不能访问资源的聊天窗口只能规划，不能声称完成开发或验收。

## Codex

官方文档说明项目技能目录为 `.agents/skills`；本仓库的 AGENTS.md 为项目指令入口。核对来源见 `references/sources.md`。

在可信本地克隆的套件根目录运行，目标替换为真实项目目录：

```sh
python3 scripts/install_skill.py --agent codex --project /path/to/project
python3 scripts/install_skill.py --agent codex --project /path/to/project --check
```

安装目标为 `.agents/skills/science-lab-production/`。在宿主中显式请求 `$science-lab-production`，或要求读取该目录SKILL.md；具体发现行为以当前宿主官方文档为准。

## Claude Code

```sh
python3 scripts/install_skill.py --agent claude --project /path/to/project
python3 scripts/install_skill.py --agent claude --project /path/to/project --check
```

安装目标为 `.claude/skills/science-lab-production/`，可显式请求 `/science-lab-production`。本仓库根CLAUDE.md只引用统一规范，不复制另一套相反规则。

## 安全与升级

安装器只复制本套件项目级文件，不改全局配置、不重启Agent、不接触模型账户或生产系统。对不属于安装清单的文件保持不动；发现用户改动或符号链接风险则拒绝覆盖。升级前先检查差异，不以强制删除修复冲突。

安装后的相对文件完整性由 `--check` 检查。安装成功不等于两个宿主已实际加载；需在实际宿主新会话显式调用确认。若当前环境无对应CLI，应如实标注未做该CLI端到端验证。
