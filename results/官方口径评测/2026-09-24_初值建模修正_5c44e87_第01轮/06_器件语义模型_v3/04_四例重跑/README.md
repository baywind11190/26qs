# 四例重跑（器件语义模型 v3）

- 入口：`run_reproof_v3.py`（唯一变化 = dffeas 模型换为 `02_model_v3/form_cells_cycloneiv_v3.v` + 跑前支持配置预检）。
- 协议其余部分与 `03_重跑受影响证明`（v2 重跑）逐行一致：输入、工具链、链定义、
  策略（simple / use sat / depth 5）、EQY 自生成 run.ys 原样使用。
- 独立暂存：`results/_reproof_ascii_v3_5c44e87/inputs/`（不触碰旧暂存与旧证据）。
- 预检：`precheck_report.txt` + `precheck_report.json`（违例即阻断，不启动 EQY）。
- 产物：`run01/<case>/<chain>/{config.eqy, eqy.log, work/}`、`inputs_manifest.json`、
  `reproof_v3_summary.json/csv`（含与 v2 重跑、第 03 轮的逐分区对照）。
- 固定提交 5c44e87…；不改算法/官方输入/网表；不重跑性能；不提交推送。

> 说明：v3 同时修正了“清零（clrn）”与“时钟使能（ena）”两条此前缺失的路径，
> 并保持初值处理与 v2 相同（power_up low→0、high→1）；这些正是此前
> “跨 reset 边界反例”的最小复现所指向的缺陷（见 03_模型检查/00_结论.md）。
