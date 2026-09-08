# deepTools GC 极小测试数据

原样取自官方稳定 tag `4.0.0` / commit
`fd19d2ec84f00392282787d925eb1c8317121b5b` 的
`pydeeptools/deeptools/test/test_data/`。上游 MIT 许可原文保存在相邻
`upstream-notices/LICENSE.txt`，镜像中也保留；这是上游果蝇 chr2L 极小片段，
不是生产参考、模型或完整测序数据。

| 文件 | SHA256 |
| --- | --- |
| `sequence.2bit` | `4248afd6a110661ad08a5b0ddcc639d97f7ddbe1b1d3017c7eaa38e88176494e` |
| `paired_chr2L.bam` | `7d20ec958c3a106c392d1d42c7dfbc112504fc6199f4b2fc05ef83e9ffedfb90` |
| `paired_chr2L.bam.bai` | `e788df8db9942dbeeeef123ba6b725780431a74a88edaeae10da5724ab2f1bec` |
| `computeGCBias_result1.tabular` | `fd050f4c1603e752f54f0b7d21eedd68a6980d4efdd52bc9ff6f72044c35a123` |

GC correction 用上游已固定频率表检查非空有效 BAM，避免把随机抽样计数写成
跨架构精确数值承诺；computeGCBias 另行运行。合成 BAM/regions 由
`make_testdata.py` 生成。全部测试不修改这些只读输入。
