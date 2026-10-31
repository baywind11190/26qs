# Windows原生V9验证（1030口径）

唯一活动规则为[POLICY.md](POLICY.md)，流程修订v9-official1030-r1。入口validate_windows_v9.cmd；V8入口退役，旧身份和历史证据保留原义。

## 执行

Windows PowerShell，工作目录D:/codex/0000_26qs。先运行只读plan，确认身份、九例、预计次数及blocked=[]，再按已获授权运行一次run：

```powershell
& .\scripts\pmux_validation\validate_windows_v9.cmd plan fd24aa7c8fd98ac4c8463d4a25b15af146ff7b57 --integration-profile p3-arith
& .\scripts\pmux_validation\validate_windows_v9.cmd run fd24aa7c8fd98ac4c8463d4a25b15af146ff7b57 --integration-profile p3-arith
```

plan不创建轮次或编译。身份/计量/证据故障时停止并查原始日志；有效指标FAIL仍完成规定步骤，不补样择优。

## 新基座及集成

两侧共同采用官方公开d0e71cfb7bcafe2b437f3edc1789b69e99ecd55a（0.69+24），ABC子模块1e3d9abd7934ee0376a9fd474655a85780069776。官方dirty修改未公布，不声称逐字节复现。旧基座、安装、缓存和日志全部保留。新工具与缓存独立，工具及运行依赖闭包必须逐项匹配。

p3-arith依次调用早期pmux_opt -arith、pmux_opt，不含ABC9后LUT重构。补丁、顺序、次数、导出边界及算术共享1/0私有探针均核验；旧三调用身份保留供追溯，1030活动run禁止后端LUT。

## 九例测量及功能证明

全部九例使用默认参数和同一ABC9策略。测量开始前原版每例预热10次，一批90次；该数量为用户采用的本地解释。首次原版全部后优化版全部共18次；时间增幅>5%且原版<10秒的用例另复核5对，共108+10k次。C147确认1—10秒复核；恰好5%不触发，恰好10秒不复核。首次内存及绝对限值不被复核替代。

计量保持v9-nodebugheap-r1：同次Measure-Command墙钟与Yosys主进程退出事件PeakWorkingSetSize；启动前_NO_DEBUG_HEAP=1并核验，失败不回退。两侧方法相同，记录后台及安全软件状态，不自动关闭安全软件。

首次18份post_abc作为原始RTL→两侧网表的独立功能输入，mapped用于资源。eqy-zero-init-r1仅补未定义FF初值0，保留显式初值、复位及组合X/Z；仅改证明副本并审计。完整原生EQY最终状态、分区/断言覆盖、前提SAT及日志联合判定，不能仅凭退出0。test3原生合并depth16，其余depth5，每链600秒。

DFF仅记录；逐例逻辑不增、九例平均缩减至少10%、IO和其他硬件不增；功能、资源、时间和内存分别判定。C149第一问回答不明确，不宣称所有前端规则已获官方批准。

## 结果与开发检查

D:/0026_qs_result的r/e/c/a分别保存轮次、受管理短EQY现场、自检/构建缓存和开发证据。主报告00_report.md，归档逐文件核验，历史不改判不混算。

在本验证目录以固定Python .tools/msys64/mingw64/bin/python3.exe及PYTHONUTF8=1运行unittest discover -p "test_*.py"。负对照应检出真实错误；人工微型冒烟不冒充官方case。

本次不制作交付包，交付NOT_RUN。C152要求测试环境预装OSS CAD Suite并告知路径，后续交付单独核验。本地PASS不等于官方认可。
