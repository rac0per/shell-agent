# RAG 扩库配额清单（按类别）

## 目标与范围
- 周期：4 周（可滚动复用）
- 当前基线：53 chunks
- 阶段目标：4 周后达到 200+ chunks，且优先覆盖 A/B 失败 query
- 核心原则：先补失败点，再扩同义表达与边界场景

## 当前失败 query（优先覆盖）
- copy with permissions
- extract archives
- move and rename
- port listen check
- audit logging spec
- pre execution validation checklist
- batch permission fix
- disk capacity emergency
- scheduled task rotation
- temp file cleanup
- 我现在要处理 copy with permissions，该怎么做？

## 周配额总览
- Week 1：新增 20 文档，约 55 chunks
- Week 2：新增 18 文档，约 50 chunks
- Week 3：新增 16 文档，约 45 chunks
- Week 4：新增 14 文档，约 40 chunks
- 4 周合计：68 文档，约 190 chunks

## Week 1（失败点修复周）
- commands：8 文档 / 22 chunks
- tasks：6 文档 / 18 chunks
- safety：4 文档 / 11 chunks
- patterns：2 文档 / 4 chunks

覆盖失败 query：
- copy with permissions
- extract archives
- move and rename
- port listen check
- temp file cleanup

文档模板要求：
- 每篇包含：适用场景、标准步骤、参数说明、风险、回滚、常见误用、同义问法（>=8 条）

验收：
- 上述 5 个 query 在 A/B 中 source_hit 至少提升到 0.8

## Week 2（安全与SOP增强周）
- tasks：7 文档 / 20 chunks
- safety：6 文档 / 17 chunks
- commands：3 文档 / 8 chunks
- patterns：2 文档 / 5 chunks

覆盖失败 query：
- audit logging spec
- pre execution validation checklist
- batch permission fix
- disk capacity emergency
- scheduled task rotation

文档模板要求：
- 每篇补充：失败前置条件、二次确认语句、审计字段示例

验收：
- 上述 5 个 query 的 keyword_hit 提升到 0.9

## Week 3（同义表达与跨类边界周）
- commands：6 文档 / 17 chunks
- tasks：5 文档 / 14 chunks
- safety：3 文档 / 8 chunks
- patterns：2 文档 / 6 chunks

重点动作：
- 为每个高频 query 增补中英混合同义问法 >= 15 条
- 补“易混类”对照文档（例如 commands vs tasks）

验收：
- 跨类误召回样本数较 Week 1 下降 40%

## Week 4（收口与稳定性周）
- commands：4 文档 / 12 chunks
- tasks：4 文档 / 12 chunks
- safety：4 文档 / 11 chunks
- patterns：1 文档 / 3 chunks
- examples：1 文档 / 2 chunks

重点动作：
- 失败案例反向扩写：每个失败 query 至少新增 1 篇“反例+正例”文档
- 补“短问句/口语问法”示例文档

验收：
- A/B 对比中：MRR 与 nDCG 稳定提升，且 Top-10 失败样本中跨类误召回降至 <= 5 条

## 每周执行命令（建议）
```bash
python src/build_rag_index.py --reindex --source docs
python src/evaluate_rag.py --dataset data/rag_eval_docs_only.json --top-k 5 --output data/rag_eval_report_weekN.json
python src/run_rag_ab.py --dataset data/rag_eval_docs_only.json --top-k 5 --output data/rag_ab_report_weekN.json
```

## 每周汇报指标（固定）
- Source HitRate
- Keyword HitRate
- Source Recall@1/3/5
- MRR
- nDCG
- Elapsed(sec)
- Top-10 失败样本分类计数（跨类误召回/同义词丢失/文档粒度不合适/重排误伤）
