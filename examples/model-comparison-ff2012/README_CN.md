# 单篇论文模型对照：Fama–French 国际动量

[English](README.md)

**本轮结果：** Sol 与随后探索性运行的 Sol＋QuantGlean 提交了逐月完全相同的四地区因子序列；Luna 与 Luna＋QuantGlean 都把来源文件其他区段混入了月度数据，提交的序列有重复行。每组只运行一次，因此这次试跑**没有证明 QuantGlean 提高复现质量或 Alpha 质量**。

三组收到同一任务：阅读 Fama 与 French 的[《Size, Value, and Momentum in International Stock Returns》](https://www.johnhcochrane.com/s/Fama_French_size_value_momentum_JFE.pdf)，用 [Ken French 官方资料库](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html)的四地区“规模×动量”六组合收益，重建月度赢家减输家因子。第三组另读了仓库的通用 `SKILL.md`。模型只接触四个六组合 ZIP；四个官方 Mom 因子 ZIP 留给独立评分。

## 官方数据

八个压缩包于 2026-11-05 下载至 `D:\Github\QuantGlean\local-work\source-inputs\ff2012`，只供本地核对；仓库没有转发原始数据。用户可直接从官方地址获取：

| 地区 | 六组合收益 | 官方 Mom 因子 |
|---|---|---|
| 北美 | [CSV ZIP](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/North_America_6_Portfolios_ME_Prior_12_2_CSV.zip) | [CSV ZIP](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/North_America_Mom_Factor_CSV.zip) |
| 欧洲 | [CSV ZIP](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Europe_6_Portfolios_ME_Prior_12_2_CSV.zip) | [CSV ZIP](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Europe_Mom_Factor_CSV.zip) |
| 日本 | [CSV ZIP](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Japan_6_Portfolios_ME_Prior_12_2_CSV.zip) | [CSV ZIP](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Japan_Mom_Factor_CSV.zip) |
| 日本外亚太 | [CSV ZIP](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Asia_Pacific_ex_Japan_6_Portfolios_ME_Prior_12_2_CSV.zip) | [CSV ZIP](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Asia_Pacific_ex_Japan_MOM_Factor_CSV.zip) |

文件标记为 **202609 Bloomberg** 数据版本。四地区各有 431 个重合月份，范围为 1990 年 11 月至 2026 年 9 月。这是当前版本的已发布组合收益，不能当作论文原始个股级数据。[国际组合构造说明](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/six_portfolios_momentum_developed.html)适用于本轮地区数据；[美国 Mom 说明](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_mom_factor.html)采用不同股票范围与断点，不能混用。

## 数值核对

指定公式为 `0.5 × (小盘赢家＋大盘赢家－小盘输家－大盘输家)`，单位是**百分点**，只读取六组合文件中的“月度市值加权收益”区段。公布值经过舍入，独立核对中有三个“地区×月份”的差异达到 0.02 个百分点；因此不宣称逐月完全相同。

| 组别 | 输出行数 | 不重复的地区×月份 | 重复行 | 日期格式错误行 | 数值结论 |
|---|---:|---:|---:|---:|---|
| Sol | 1,724 | 1,724 | 0 | 0 | 有效；相对官方 Mom 平均绝对误差 0.00391 个百分点 |
| Sol＋QuantGlean（后续探索性运行） | 1,724 | 1,724 | 0 | 0 | 有效；1,724 个数值与 Sol 完全相同；平均绝对误差同为 0.00391 个百分点 |
| Luna | 6,896 | 1,724 | 5,172 | 0 | 月度序列无效，不计算精度分 |
| Luna＋QuantGlean | 7,093 | 1,724 | 5,172 | 197 | 月度序列无效，不计算精度分 |

两个 Luna 版本均混入其他数据区段。看到标准答案后挑选最接近的一行，会改变原提交结果，所以保留失败原貌。Luna 首次遇到输出目录问题，创建目录后继续执行，任务内容未更改。

在看过第一次结果后，我给四种语言的 Skill 都补上了“先锁定数据区段、拒绝重复日期键”的要求，并进行了**开发性复跑**。Luna＋QuantGlean 仍输出 6,896 行，重复 5,172 行。由于修改发生在看到结果之后，这一轮不并入原三组公平对照。结果说明单靠文字指令没有可靠执行数据契约，需要程序化区段解析与唯一键检查。

用户随后要求比较 Sol 与 Sol＋QuantGlean。我保留原 Sol 输出，让新的 Sol 运行读取修订后的通用 Skill（SHA-256：`00c7617d3a51622077ba43f26cec559e5155580a9fd6f0f23a20626f7e3421eb`）和相同的四个输入文件。两组 1,724 个地区×月份数值完全相同。由于 Skill 是在第一次结果后修订的，且每组只有一次运行，这只是探索性观察，不能估计稳定的 Skill 增量。

[独立因子核对程序](../../scripts/audit-french-momentum.py)计算来源哈希、重合月份和差异；[模型输出评分程序](../../scripts/score-french-momentum-arms.py)检查五次运行提交的原始 CSV。将八个官方 ZIP 下载至本地私有目录，并把五份输出分别放入 `sol`、`sol_qg`、`luna`、`luna_qg`、`luna_qg_v2` 子目录后，可运行：

```sh
python scripts/audit-french-momentum.py 私有数据目录
python scripts/score-french-momentum-arms.py 私有数据目录 三组输出的父目录
```

本轮是一次流程试跑。最初三组文字回答都意识到公开组合数据不足以重建论文的个股研究；数值任务中 Sol 正确选取了月度区段，而 QuantGlean 没能改善 Luna 的错误。后续 Sol＋QuantGlean 的数值结果与 Sol 相同。所有组别均未完成策略扩展回测，**Alpha 质量尚无法比较**；要检验各组提出的流动性或卖空机制，还需要有使用权的点时个股、交易与成本数据。
