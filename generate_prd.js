const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun, Header, Footer, AlignmentType, PageOrientation, LevelFormat, ExternalHyperlink, InternalHyperlink, Bookmark, FootnoteReferenceRun, PositionalTab, PositionalTabAlignment, PositionalTabRelativeTo, PositionalTabLeader, TabStopType, TabStopPosition, Column, SectionType, TableOfContents, HeadingLevel, BorderStyle, WidthType, ShadingType, VerticalAlign, PageNumber, PageBreak } = require('docx');
const fs = require('fs');

// Create document
const doc = new Document({
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    children: [
      new Paragraph({
        heading: HeadingLevel.HEADING_1,
        children: [new TextRun({ text: 'TikTok跨境电商全自动运营系统', bold: true, size: 32, font: 'Arial' })]
      }),
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun({ text: '产品需求文档 (PRD)', bold: true, size: 28, font: 'Arial' })]
      }),
      new Paragraph({ text: '' }),
      new Paragraph({ text: '文档版本：V1.0' }),
      new Paragraph({ text: '创建日期：2025-04-01' }),
      new Paragraph({ text: '编制：AI Assistant' }),
      new Paragraph({ text: '状态：评审稿' }),
      new Paragraph({ text: '' }),
      new Paragraph({ text: '' }),
      new Paragraph({
        heading: HeadingLevel.HEADING_1,
        children: [new TextRun({ text: '1. 产品概述', bold: true, size: 32, font: 'Arial' })]
      }),
      new Paragraph({ text: '' }),
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun({ text: '1.1 产品定位', bold: true, size: 28, font: 'Arial' })]
      }),
      new Paragraph({
        text: 'TikTok跨境电商全自动运营系统是面向TikTok Shop跨境电商卖家的全链路无人化智能运营SaaS平台，基于多AI Agent协同架构，实现从选品调研、素材生成、商品上架、流量运营、订单履约、智能客服到财务核算的全流程自动化决策与执行。'
      }),
      new Paragraph({ text: '' }),
      new Paragraph({ text: '核心定位：' }),
      new Paragraph({
        numbering: { reference: 'bullets', level: 0 },
        children: [new TextRun({ text: '用户群体：中小型跨境卖家（1-10人团队）、大型卖家/品牌商家（50-200人团队）、跨境电商服务商' })]
      }),
      new Paragraph({
        numbering: { reference: 'bullets', level: 0 },
        children: [new TextRun({ text: '商业模式：SaaS订阅制（月费2000-5000元）+ 私有化部署（年费50-200万元）' })]
      }),
      new Paragraph({
        numbering: { reference: 'bullets', level: 0 },
        children: [new TextRun({ text: '技术架构：云原生微服务 + 多AI Agent协同 + 数据中台' })]
      }),
      new Paragraph({
        numbering: { reference: 'bullets', level: 0 },
        children: [new TextRun({ text: '核心价值：7×24小时无人化运营，人力成本降低90%，运营效率提升5-10倍' })]
      }),
      new Paragraph({ text: '' }),
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun({ text: '1.2 产品目标', bold: true, size: 28, font: 'Arial' })]
      }),
      new Paragraph({ text: '' }),
      new Paragraph({ text: '1.2.1 业务目标', bold: true }),
      new Paragraph({ text: '' }),
      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [3000, 3000, 3360],
        rows: [
          new TableRow({
            children: [
              new TableCell({
                borders: { top: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, bottom: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, left: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, right: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' } },
                width: { size: 3000, type: WidthType.DXA },
                shading: { fill: 'D5E8F0', type: ShadingType.CLEAR },
                children: [new Paragraph({ children: [new TextRun({ text: '目标维度', bold: true, font: 'Arial' })] })]
              }),
              new TableCell({
                borders: { top: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, bottom: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, left: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, right: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' } },
                width: { size: 3000, type: WidthType.DXA },
                shading: { fill: 'D5E8F0', type: ShadingType.CLEAR },
                children: [new Paragraph({ children: [new TextRun({ text: '具体指标', bold: true, font: 'Arial' })] })]
              }),
              new TableCell({
                borders: { top: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, bottom: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, left: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, right: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' } },
                width: { size: 3360, type: WidthType.DXA },
                shading: { fill: 'D5E8F0', type: ShadingType.CLEAR },
                children: [new Paragraph({ children: [new TextRun({ text: '衡量标准', bold: true, font: 'Arial' })] })]
              })
            ]
          }),
          new TableRow({
            children: [
              new TableCell({
                borders: { top: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, bottom: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, left: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, right: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' } },
                width: { size: 3000, type: WidthType.DXA },
                children: [new Paragraph({ children: [new TextRun({ text: '用户增长' })] })]
              }),
              new TableCell({
                borders: { top: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, bottom: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, left: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, right: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' } },
                width: { size: 3000, type: WidthType.DXA },
                children: [new Paragraph({ children: [new TextRun({ text: '上线12个月累计付费用户1000+' })] })]
              }),
              new TableCell({
                borders: { top: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, bottom: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, left: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, right: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' } },
                width: { size: 3360, type: WidthType.DXA },
                children: [new Paragraph({ children: [new TextRun({ text: '付费用户数、续费率>80%' })] })]
              })
            ]
          })
        ]
      }),
      new Paragraph({ text: '' }),
      new Paragraph({
        heading: HeadingLevel.HEADING_1,
        children: [new TextRun({ text: '2. 用户角色与权限', bold: true, size: 32, font: 'Arial' })]
      }),
      new Paragraph({ text: '' }),
      new Paragraph({ text: '系统采用RBAC（基于角色的访问控制）模型，定义以下核心角色：' }),
      new Paragraph({ text: '' }),
      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [2000, 2500, 2500, 2360],
        rows: [
          new TableRow({
            children: [
              new TableCell({
                borders: { top: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, bottom: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, left: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, right: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' } },
                width: { size: 2000, type: WidthType.DXA },
                shading: { fill: 'D5E8F0', type: ShadingType.CLEAR },
                children: [new Paragraph({ children: [new TextRun({ text: '角色', bold: true, font: 'Arial' })] })]
              }),
              new TableCell({
                borders: { top: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, bottom: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, left: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, right: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' } },
                width: { size: 2500, type: WidthType.DXA },
                shading: { fill: 'D5E8F0', type: ShadingType.CLEAR },
                children: [new Paragraph({ children: [new TextRun({ text: '核心职责', bold: true, font: 'Arial' })] })]
              }),
              new TableCell({
                borders: { top: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, bottom: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, left: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, right: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' } },
                width: { size: 2500, type: WidthType.DXA },
                shading: { fill: 'D5E8F0', type: ShadingType.CLEAR },
                children: [new Paragraph({ children: [new TextRun({ text: '功能权限', bold: true, font: 'Arial' })] })]
              }),
              new TableCell({
                borders: { top: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, bottom: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, left: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, right: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' } },
                width: { size: 2360, type: WidthType.DXA },
                shading: { fill: 'D5E8F0', type: ShadingType.CLEAR },
                children: [new Paragraph({ children: [new TextRun({ text: '数据权限', bold: true, font: 'Arial' })] })]
              })
            ]
          }),
          new TableRow({
            children: [
              new TableCell({
                borders: { top: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, bottom: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, left: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, right: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' } },
                width: { size: 2000, type: WidthType.DXA },
                children: [new Paragraph({ children: [new TextRun({ text: '超级管理员' })] })]
              }),
              new TableCell({
                borders: { top: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, bottom: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, left: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, right: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' } },
                width: { size: 2500, type: WidthType.DXA },
                children: [new Paragraph({ children: [new TextRun({ text: '系统全局管理' })] })]
              }),
              new TableCell({
                borders: { top: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, bottom: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, left: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, right: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' } },
                width: { size: 2500, type: WidthType.DXA },
                children: [new Paragraph({ children: [new TextRun({ text: '所有功能' })] })]
              }),
              new TableCell({
                borders: { top: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, bottom: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, left: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, right: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' } },
                width: { size: 2360, type: WidthType.DXA },
                children: [new Paragraph({ children: [new TextRun({ text: '所有数据' })] })]
              })
            ]
          }),
          new TableRow({
            children: [
              new TableCell({
                borders: { top: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, bottom: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, left: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, right: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' } },
                width: { size: 2000, type: WidthType.DXA },
                children: [new Paragraph({ children: [new TextRun({ text: '老板/CEO' })] })]
              }),
              new TableCell({
                borders: { top: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, bottom: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, left: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, right: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' } },
                width: { size: 2500, type: WidthType.DXA },
                children: [new Paragraph({ children: [new TextRun({ text: '战略决策、财务审批' })] })]
              }),
              new TableCell({
                borders: { top: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, bottom: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, left: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, right: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' } },
                width: { size: 2500, type: WidthType.DXA },
                children: [new Paragraph({ children: [new TextRun({ text: '数据看板、财务、风控、审批' })] })]
              }),
              new TableCell({
                borders: { top: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, bottom: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, left: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' }, right: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' } },
                width: { size: 2360, type: WidthType.DXA },
                children: [new Paragraph({ children: [new TextRun({ text: '全公司数据' })] })]
              })
            ]
          })
        ]
      }),
      new Paragraph({ text: '' }),
      new Paragraph({ text: '' })
    ]
  }],
  numbering: {
    config: [
      { reference: 'bullets', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: 'numbers', levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }
    ]
  },
  styles: {
    default: { document: { run: { font: 'Arial', size: 24 } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { size: 32, bold: true, font: 'Arial' }, paragraph: { spacing: { before: 240, after: 240 }, outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { size: 28, bold: true, font: 'Arial' }, paragraph: { spacing: { before: 180, after: 180 }, outlineLevel: 1 } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { size: 26, bold: true, font: 'Arial' }, paragraph: { spacing: { before: 120, after: 120 }, outlineLevel: 2 } }
    ]
  }
});

// Save document
Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync('/Users/iskywong/工作目录/project_code/TikTok跨境电商全自动运营系统-PRD-V1.0.docx', buffer);
  console.log('PRD文档已生成：/Users/iskywong/工作目录/project_code/TikTok跨境电商全自动运营系统-PRD-V1.0.docx');
}).catch(err => {
  console.error('生成失败：', err);
});
