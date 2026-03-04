// Default Typst source template
export const DEFAULT_TYPST_SOURCE = `
#set page(
  paper: "a4",
  margin: (x: 1cm, y: 1cm),
)

// ── Watermark "ตัวอย่าง" ────────────────────────────────────────────────
#place(
  center + horizon,
  clearance: 0cm,
)[
  #rotate(-37deg)[
    #text(
      size: 145pt,
      fill: rgb("#d32f2f").lighten(55%).transparentize(65%),  // แดงอ่อนโปร่งใส
      weight: "extrabold",
      tracking: 0.2em,
    )[ตัวอย่าง]
  ]
]

// ── Document Settings ───────────────────────────────────────────────────
#set text(
  font: "TH Sarabun New",
  size: 12pt,
  lang: "th",
  region: "TH",
)
#set par(leading: 0.45em, spacing: 0.55em)

#let primary    = rgb("#004d99")
#let accent     = rgb("#0066cc")
#let gray       = rgb("#555555")
#let light-gray = rgb("#f0f5ff")

// Header
#grid(
  columns: (1fr, auto),
  align: (left + horizon, right + horizon),
  gutter: 6cm,
  [
    #text(weight: "bold", fill: primary, size: 15pt)[บริษัท ออพติค แว่นตา ดีไซน์ จำกัด] 
    #text(fill: gray)[
      123/45 อาคารสีลมคอมเพล็กซ์ ชั้น 7 ถนนสีลม แขวงสีลม เขตบางรัก กรุงเทพมหานคร 10500  
      เลขประจำตัวผู้เสียภาษี 0105558001234  
      โทร 02-123-4567 • 091-234-5678  
      อีเมล: contact//@opticdesign.co.th
    ]
  ],
  [
    #block(
      fill: light-gray,
      inset: (x: 12pt, y: 10pt),
      radius: 6pt,
      stroke: 1pt + accent,
    )[
      #align(center)[
        #text(fill: accent, weight: "bold", size: 16pt)[ใบเสร็จรับเงิน / ใบกำกับภาษี] #v(0.1cm)
        #text(fill: gray, size: 12pt)[Receipt / Tax Invoice] #v(0.1cm)
        #text(fill: primary, weight: "bold", size: 14pt)[ต้นฉบับ / Original]
      ]
    ]
  ]
)

#v(0.7cm)

// Customer & Document Info
#grid(
  columns: (1fr, 1fr),
   gutter: 6cm,
  align: (left, right),
  [
    #text(weight: "bold", fill: primary)[ลูกค้า / Customer] #v(0.15cm)
    นาย วีระชัย สุขใจ  
    45/12 หมู่ 8 ถนนเพชรเกษม แขวงบางหว้า เขตภาษีเจริญ กรุงเทพมหานคร 10160  
    เลขประจำตัวผู้เสียภาษี 1234567890123  
    โทร 089-765-4321  
    อีเมล: veerachai.s//@gmail.com
  ],
  [
    #set text(fill: gray)
    #strong[เลขที่เอกสาร] #h(1cm) RTV-2567-0913001 #v(0.15cm)
    #strong[วันที่] #h(1.3cm) 13 กันยายน 2567 #v(0.15cm)
    #strong[พนักงานขาย] #h(1.1cm) คุณภัทริดา สนามชัย
  ]
)

#v(0.6cm)

// Product Table
#table(
  columns: (0.6fr, 3.4fr, 0.9fr, 0.9fr, 1.4fr, 1.1fr, 1.6fr),
  align: (center, left, center, center, right, right, right),
  stroke: none,
  gutter: 0.2cm,
  table.cell(
    colspan: 7,
    fill: light-gray,
    stroke: (bottom: 1pt + primary, top: 1pt + primary),
    text(weight: "bold", size: 12pt)[
      ลำดับ #h(1cm) รายการสินค้า / Description #h(2.5cm) จำนวน #h(1cm) หน่วย #h(1cm) ราคาต่อหน่วย #h(1cm) ส่วนลด #h(1cm) จำนวนเงิน (บาท)
    ]
  ),
  [1],
  [แว่นสายตากรอบ TR90 สีดำด้าน + เลนส์ชั้นสูง 1.67 Aspheric Anti-Reflective + UV400],
  [1], [ชิ้น], [6,800.00], [—], [6,800.00],
  [2],
  [เคลือบป้องกันรอยนิ้วมือ + กันแสงสีฟ้า (Blue Light Filter)],
  [1], [ชิ้น], [800.00], [—], [800.00],
  [3],
  [ผ้าไมโครไฟเบอร์พรีเมียม + กล่องหนัง PU แบบแข็ง],
  [1], [ชุด], [450.00], [—], [450.00],
)

#line(length: 100%, stroke: 1pt + primary)
#v(0.4cm)

// Summary
#align(right)[
  #grid(
    columns: (auto, 1.2cm, auto),
    align: (right, right, left),
    gutter: 1cm,
    row-gutter: 0.8em,
    [*รวมเป็นเงิน (ก่อนภาษี)*], [7,450.47], [*บาท*],
    [*ส่วนลดพิเศษ*], [0.00], [*บาท*],
    [*ราคาหลังหักส่วนลด*], [7,450.47], [*บาท*],
    [*ภาษีมูลค่าเพิ่ม 7%*], [521.53], [*บาท*],
    grid.cell(
      colspan: 3,
      stroke: (top: 1pt + primary),
      none
    ),
    [*รวมเงินทั้งสิ้น*],
    text(weight: "bold", size: 13pt)[7,972.00],
    text(weight: "bold", size: 13pt)[*บาท*],
  )
]

#v(1.3cm)

// Remarks + Signature
#grid(
  columns: (1fr, 1fr),
  gutter: 1cm,
  [
    #text(fill: primary, weight: "semibold", size: 12pt)[หมายเหตุ / Remark] #v(0.25cm)
    • รับประกันกรอบแว่น 1 ปี (แตก/หักจากความเสียหายปกติ)  
    • เลนส์รับประกันเคลือบ 6 เดือน  
    • สินค้าสั่งทำพิเศษไม่สามารถคืนหรือเปลี่ยนได้
  ],
  [
    #align(center + bottom)[
      #rect(
        width: 7.5cm,
        height: 2.4cm,
        stroke: (top: 1pt + gray),
        inset: (top: 1cm)
      )[
        #align(center)[
          #text(size: 10pt, fill: gray)[ลายเซ็นผู้รับเงิน / Received by]
        ]
      ]
    ]
  ]
)

#v(0.9cm)

#align(center)[
  #text(size: 10pt, fill: gray, style: "italic")[
    ขอบคุณที่ไว้วางใจให้ บริษัท ออพติค แว่นตา ดีไซน์ จำกัด ดูแลสายตาของท่าน  
    Thank you for trusting us with your vision
  ]
]
`.trim();
