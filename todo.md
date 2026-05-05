# 毕设论文待办总清单（更新于 2026-05-06）

## 当前仍存在的问题（按优先级）

- [ ] 补写致谢（200字以内）
  - 文件：thesis/template/chapters/acknowledgement.tex
  - 现状：仍为 TODO 占位。

- [ ] 替换图 3-2 的占位框为真实截图
  - 文件：thesis/template/chapters/c3_system.tex
  - 标签：fig:cli-runtime

- [ ] 替换图 5-2 的占位框为真实截图
  - 文件：thesis/template/chapters/c5_safety.tex
  - 标签：fig:safety-blocked

- [ ] 替换图 6-2 的占位框为真实截图
  - 文件：thesis/template/chapters/c6_experiments.tex
  - 标签：fig:exp-stepwise-case

## 本轮核查结论（已完成）

- [x] 主文档可编译通过（xelatex 最近一次返回码 0）。
- [x] 未发现未解析引用、未解析文献、Overfull/Underfull 警告（main_thesis.log 关键字扫描）。
- [x] 图 3-1（fig:arch）已完成（TikZ 架构图）。
- [x] 图 4-1（fig:routing）已完成（路由流程图已在正文中定义与引用）。
- [x] 图 5-1（fig:pipeline）已完成（TikZ 流水线图）。
- [x] 图 6-1（fig:recall-k）已完成（引用 data/reports/fig_recall_natural_4configs.png，文件存在）。

## 提交前最短闭环

- [ ] 三张占位图替换完成后，执行完整两轮编译（建议：xelatex -> bibtex -> xelatex -> xelatex）。
- [ ] 通读最终 PDF 1 次，重点检查：图注、图号连续、分页、截图清晰度。
- [ ] 打包提交材料：tex 源码、bib、图片资源、最终 PDF。

## 建议但不强制

- [ ] 若有时间，补 1 张“第6章 A/B 四指标柱状图”（用于答辩展示更直观）。
