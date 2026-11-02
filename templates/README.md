# 合同与证据填写说明

所有模板中的 pending 都是待研究/待实现，不是建议的学生文案。`init`生成骨架不构造来源、截图或已通过结论。参数名保持代码标识，学生可见文字另作儿童语言审核。

## project-contract.json

- `product_intent`：孩子在这个世界能做什么，为什么需要数字实验室。
- `subjects`、`exploration_map`：主题与探索区域；每区写真实问题、深度、边界及存在的scene_ids。不能只列名词。
- `preservation`：已认可功能、生产保护目标、改动范围和明确不做的内容。new模式可无旧目标；iterate必须先审现有项目。
- `representative_scene`：选择最能暴露关键科学/体验/模型风险的场景；通过实际审查后填写reviewed、真实reviewer与相对记录路径。不把尚未认可的候选当样板。
- `design_review`：真实审查记录，审查人身份如实写明人工/智能体及其能力边界，不把模型角色当医学专家资质。
- `ui`：主要触点44px、少而大、顶部导航、紧凑布局、竖屏重排；布尔值只是合同承诺，不能代替像素测量。
- `scenes`：逐场景复制scene-contract填充；id唯一，必须与探索地图和证据对应。
- `deployment`：只有授权并实际发布验证后才写verified、真实URL和immutable_release。没有公网验证，release检查应失败；可继续交付本地候选，不伪造网址。

## scene-contract.json

`learning_goal/student_action/causal_chain/observable_feedback/replay`写成可实际执行和观察的关系，不是概念名单。每个场景另行回答目标、动作、反馈、差异结果、再玩理由。

`sources`须记录对象或科学命题身份、原始URL、许可/可用范围、类型、实际核查状态。可按项目增加作者、访问日期、源文件、派生方式和SHA256；`verified`不能仅由URL存在自动推断。

`model_boundaries`区分真实原件、来源派生、教学重建和艺术表现，单位未知就明确未知、停用精确测量，不补造尺寸。

`dynamic_behavior`默认true，须有真实运动/暂停证据。真正静态的原件参照可设false，但要写`static_reference_reason`并留审查记录，说明为何保持原始数据不动；不能借此掩盖本应实现的动态过程。

`narration.implementation`仅为prerecorded/tts/live。首讲自动、整句、同页不重启、切场停旧音、实验音效独立均需落实。live无真实服务不得固定短句假回退。预合成音轨与实时AI不是同一个能力。

`video.status`为none/pending/ready；未就绪不得有死播放按钮，也不能替代核心因果互动。视频生产详见video-task.json；既有工程审查使用brownfield-audit.json。

## evidence.json 与 capture-record.json

证据绑定实际origin.url、source_revision及源/构建文件SHA256。项目仅测了本地就写本地，未部署不得填成公网验证。

每个场景×六种视口各一条capture，viewport精确为：1440x1000、1024x768、820x1180、390x844、360x640、844x390。使用capture-record作为结构骨架，但观察必须来自实际运行。

每条capture填写：

- `scene_id/viewport/origin_url/source_revision`。
- `screenshot: {path,sha256}`：实际PNG/JPEG/WebP、非空相对路径、不得同一文件路径充六视口。
- `runtime/mouse/touch/sound/pause_motion/narration/layout`：各自 `{status,observation,record:{path,sha256}}`。
- sound额外记录`voice_audible/effects_independent`。媒体时间推进、信号与完整人耳试听分别写范围，不能仅调用play就认为可听。
- narration额外记录`automatic_on_scene/complete_sentences/same_page_no_repeat/stop_previous_on_switch`。
- pause_motion额外记录`changed_while_running/stable_while_paused`。静态参照须明确status=not-applicable及科学理由和记录，不伪造动态。
- layout额外记录`minimum_primary_touch_px/navigation_centered/unobstructed_scene`。390/360窄屏导航溢出时可记录`navigation_overflow_scroll=true`与`navigation_first_last_reachable=true`，但不能借此放宽Pad/PC居中。

部署证据必须包含目标HTTP检查、实际发布文件内容哈希、与origin源文件对应；iterate另有受保护旧入口的before/after原值、哈希和记录。

所有证据路径必须在项目内，不允许符号链接逃逸。模板不包含任何真实通过结果。自动工具无法鉴定“人为伪造后计算哈希”的证据，仍需独立核对实际浏览器与源状态。儿童试用/物理设备/专家审核各自如实记录，不由模板自动授予。
