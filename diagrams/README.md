# 可编辑模型图与报告插图

B交付v1.0，2026-11-13。三图均有Mermaid源、SVG和2倍像素PNG；模型字段/外键仍以逻辑/物理JSON为完整定义。图源与概念/逻辑设计内嵌图同步，导出身份、版本和像素见[manifest](exports/manifest.json)。

| 图 | 可编辑源 | 矢量版 | PNG |
|---|---|---|---|
| 图3-1 业务概念 | [mmd](conceptual-model.mmd) | [SVG](exports/conceptual-model.svg) | [PNG](exports/conceptual-model.png) |
| 图4-1 角色星型 | [mmd](star-schema.mmd) | [SVG](exports/star-schema.svg) | [PNG](exports/star-schema.png) |
| 图4-2 源行血缘 | [mmd](source-lineage.mmd) | [SVG](exports/source-lineage.svg) | [PNG](exports/source-lineage.png) |

星型图将日期/小时/站点的两角色合并在同一条标注边上，各角色都是1:N；并不减少实际FK。血缘中的三类去向是同一表的分类，不是三张新增物理表。PNG已逐图目视检查，初稿的标签换行/拥挤已调整；报告建议优先SVG按版心缩放，最终Word合并后再检查排版。

## 重建导出

使用官方[Mermaid CLI](https://github.com/mermaid-js/mermaid-cli) 11.12.0、Mermaid 11.17.2及本机Chrome，无需全局安装，不是工程运行依赖。渲染工具只装在被忽略的tmp目录，不提交node_modules。示例从工程根执行：

```powershell
$env:PUPPETEER_SKIP_DOWNLOAD='true'
npm.cmd install --prefix tmp/diagram-tools --no-audit --no-fund @mermaid-js/mermaid-cli@11.12.0 mermaid@11.17.2
# tmp/puppeteer.json 设为本机 Chrome 的 executablePath，勿写用户浏览器 profile。
node tmp/diagram-tools/node_modules/@mermaid-js/mermaid-cli/src/cli.js -i diagrams/star-schema.mmd -o diagrams/exports/star-schema.svg -c diagrams/mermaid-config.json -p tmp/puppeteer.json -w 2400 -H 1600 -s 2 -b white
```

换源文件名/扩展名导出其余SVG/PNG；Chrome路径是本机设置，不加入配置清单。当前[渲染配置](mermaid-config.json)使用Microsoft YaHei字体、白底、SVG文字标签。其他机器须有可显示中文字体，渲染后重新目视检查并更新导出清单；工具/字体变化可能改变像素，不改变模型语义。
