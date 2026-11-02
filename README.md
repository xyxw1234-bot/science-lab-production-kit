# 超级科学实验室开发套件

面向小学1—4年级，供 Codex、Claude Code 及其他能读文件的智能体开发、审查和迭代互动科学实验室。

**科学准确、内容扎实、模型可信；操作直观、因果可玩、导师自然陪伴。**

## 最简单的使用方式

把本仓库链接发给智能体，附上一句话：

> 读取这个仓库的 START-HERE.md、SKILL.md 及必读附件，按完整规范开发“某某主题实验室”。先做探索地图与一个代表性可玩场景，再按验收流程扩展。

迭代已有项目时，再给项目源码位置及需要改变的目标。无需粘贴私人聊天背景。

- [智能体统一入口](SKILL.md)
- [首次接手与能力边界](START-HERE.md)
- [Codex / Claude Code 项目安装](adapters/README.md)
- [产品、科学、儿童体验规范](references/product-and-learning.md)
- [AI导师与多媒体](references/ai-mentor-and-media.md)
- [验收门槛](VALIDATION.md)
- [本版本实际验证范围](VERIFICATION.md)
- [主题地图](references/topic-map.md)
- [可运行因果与语音参考示例](examples/energy-play/README.md)

主链接始终跟随 `main`；Tag和Release用于审计与复现，不作为日常入口。

## 不只是提示词

本仓库包括主Skill、七项专项规范、合同与证据模板、Python标准库脚手架/校验/安装器、实际可运行示例及回归测试。工具不替代科学审核、真实截图、语音检查和儿童试用。

```sh
python3 scripts/kit.py init --name "天气与水实验室" --slug weather-water --output ../weather-water
python3 scripts/kit.py validate --project ../weather-water --stage design
python3 -m unittest discover -s tests -v
node --test examples/energy-play/*.test.mjs
python3 scripts/audit_repository.py
```

新建合同保留未知和待办，不能直接通过发布检查。不要伪造来源、截图、浏览器运行或部署记录来满足校验器。

## 适用与不适用

适用：新主题、既有主题迭代、模型与交互审查、低龄游戏化及导师语音接入。

不适用：以固定课程四步替代自由探索、只产目录/卡片、以预录旁白冒充实时AI、未经授权修改生产、危险儿童实操。

参考示例是一个小型因果/语音工程管线，不是现成的完整能源实验室，也不是模型品质标杆。套件不附带商业模型账户、生产服务器、全主题三维资产或儿童试用结果。缺项须诚实报告。

## 文件与许可

所有核心规则可脱离特定助手的记忆使用。见 [维护与版本](MAINTAINING.md)、[许可](LICENSE)、[第三方说明](THIRD_PARTY.md)。不包含私人聊天、学校学生数据、服务器凭据或会话缓存。
