# Windows原生V9验证

唯一活动规则见[POLICY.md](POLICY.md)。入口validate_windows_v9.cmd；V8入口已退役，旧证据不改判。

在Windows PowerShell、工程D:/codex/0000_26qs中执行：

```powershell
& .\scripts\pmux_validation\validate_windows_v9.cmd plan 17f9361099dcda757c16bb81caa18ddb52d74c4e --integration-profile p3-local-lut
& .\scripts\pmux_validation\validate_windows_v9.cmd run 17f9361099dcda757c16bb81caa18ddb52d74c4e --integration-profile p3-local-lut
```

plan只读，预期九例、预热90/首次18/最多复核90、blocked为空；有阻断则查具体字段，不启动run。run仅在已授权后使用，预期生成D:/0026_qs_result/r新轮次；指标FAIL也保留证据，不再次运行以筛选成绩。工具失败停止，不补样。

预热逐例原版10次；首次原版全九例后优化版全九例。时间>5%且首次原版<10秒的case另复核5对，比较两侧平均时间；首次单独保留。官方不足1秒许可与用户1—10秒扩展分开标注。内存与绝对限值用首次；首次18网表用于EQY，复核网表逐份哈希/资源一致。

目录：r轮次，e确定性短EQY现场，c验证缓存，a开发证据，均位于D:/0026_qs_result。原工具构建保留；旧V8缓存不作为V9合格证据。EQY归档必须逐文件核验，现场不自动清理。

开发检查：在本目录使用工程固定Python执行 `python3.exe -m unittest discover -p "test_*.py"`；失败先核对日志，不启动正式轮次。人工微型冒烟不得伪装官方case。

DFF只记录；逐例逻辑不增、九例平均至少10%、IO/其他硬件不增保持。所有用例固定同一ABC9策略。安全软件状态只读记录，不自动关闭。交付包独立NOT_RUN；本地结果不代表官方认可。

## V9计量修订 v9-nodebugheap-r1

目标进程启动前统一设置 `_NO_DEBUG_HEAP=1`；首次调试启动断点读取x64进程及NT堆标志，确认调试堆未开启。策略、修订、实际环境值与根PID绑定原始计量证据；缺失、不符或读取失败即计量无效，不回退。保持同次PowerShell墙钟与退出事件峰值内存，预热/首次/复核和5%/15%规则不变。旧自检指纹失效，历史轮次原判定保留。
