# 验证分层

## 套件自身

运行：

```sh
python3 -m unittest discover -s tests -v
node --test examples/energy-play/*.test.mjs
python3 scripts/audit_repository.py
```

检查文档依赖、版本一致、脚手架拒覆盖、输入安全、合同不误报完成、证据文件/哈希、安装与升级的所有权边界。GitHub Actions执行同样的可确定性测试，不宣称CI已经替项目进行浏览器/儿童试用。

## 生产项目

`kit.py validate --stage design`检查设计结构与必需信息，不判断研究结论真实性。新骨架中pending必须保留。

`--stage release`检查发布所需合同和证据条件，不具有鉴定真伪的能力。文件哈希只证明文件一致，无法证明截图确由浏览器生成；独立审查须核实际运行与源状态。不得为通过工具填写虚假证据。

详见 `references/review-rubric.md`。自动检查、科学审核、视觉体验、目标年龄儿童试用、物理设备试验分别记状态。任何一项未做不扩大成全通过。

## 参考示例

按 `examples/energy-play/README.md`启动。验证真实指针按住与松开、负载增加的可见差异、曲线不占主体验、自动导师语音与字幕、同页不重启、切场停止旧音和静音控制。测试合成失败/浏览器拒音时必须显示真实状态，不能仅靠文件存在宣称已经听到声音。
