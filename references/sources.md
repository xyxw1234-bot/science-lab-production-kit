# 外部兼容性依据

核读日期：2026-11-02。链接是外部事实来源，不是项目的额外秘密依赖；未来宿主变化须重新核实。

| 用途 | 官方来源 | 本套件采用的事实 | 边界 |
|---|---|---|---|
| 跨工具Skill格式 | https://agentskills.io/specification | SKILL.md配name/description与相对资源，渐进加载 | 不保证所有产品都支持所有扩展字段 |
| Codex Skill | https://developers.openai.com/codex/skills/ （当前转至 https://learn.chatgpt.com/docs/build-skills ） | 项目`.agents/skills`、显式调用、支持附件 | 目录检查不等于实际CLI调用验收 |
| Codex项目指令 | https://developers.openai.com/codex/guides/agents-md/ （当前转至 https://learn.chatgpt.com/docs/agent-configuration/agents-md ） | 根AGENTS.md与分层发现 | 不覆盖用户全局配置或扩大权限 |
| Claude Code Skill | https://code.claude.com/docs/en/skills | 项目`.claude/skills`、显式`/技能名`、SKILL与资源 | 不依赖Claude专有动态注入；只采用可跨工具字段 |
| Claude项目指令 | https://code.claude.com/docs/en/memory | CLAUDE.md作为项目入口 | 单独存在不证明模型已经读完规范 |
| 无障碍触点参考 | https://www.w3.org/WAI/WCAG22/Understanding/target-size-enhanced.html | 主要触点44×44 CSS像素为本套件儿童项目基线 | 属项目标准，不声称所有界面由此自动符合WCAG |
| 儿童科学与工程实践 | https://www.nextgenscience.org/resources/ngss-appendices | 官方附录索引中Appendix F按年段列科学与工程实践，可作设计研究入口 | 索引搜索可核；原实践页面正文提取失败，未在此声称全文核读或学习效果实验 |
| 安全内容来源入口 | https://cpr.heart.org/en/resuscitation-science/cpr-and-ecc-guidelines | 涉及急救须查适用的现行指南及年龄/地区边界 | 此入口不是经审核急救教程；套件不提供未核动作指令 |

关于发电带动负载的参考示例：数学关系为明确标注的教学近似，不是由权威数据校准的实物发电机。其目的是演示统一状态、输入—负载反馈和语音生命周期，不把模型自写公式包装成实测结果。
