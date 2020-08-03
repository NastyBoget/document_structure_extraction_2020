# Parser for documents in .docx format

[стандарт Office Open XML File Formats с. 28-62; 167-1301](http://www.ecma-international.org/publications/files/ECMA-ST/ECMA-376,%20Fifth%20Edition,%20Part%201%20-%20Fundamentals%20And%20Markup%20Language%20Reference.zip)

## Структура docx

docx — это zip архив который физически содержит 2 типа файлов:

* xml файлы с расширениями xml и rels
* медиа файлы (изображения и т.п.)

Логически — 3 вида элементов:

* Типы (Content Types) — список типов медиа файлов (например png) встречающихся в документе и типов частей документов (например документ, верхний колонтитул)

* Части (Parts) — отдельные части документа (например document.xml, footer1.xml, header1.xml, comments.xml, endnotes.xml), сюда входят как xml документы так и медиа файлы

* Связи (Relationships) идентифицируют части документа для ссылок (например связь между разделом документа и колонтитулом), а также тут определены внешние части (например гиперссылки)

docx, созданный с помощью текстового редактора имеет несколько дополнительных файлов.

* docProps/core.xml — основные метаданные документа согласно Open Packaging Conventions и Dublin Core

* docProps/app.xml — общая информация о документе: количество страниц, слов, символов, название приложения в котором был создан документ и т.п

* word/settings.xml — настройки относящиеся к текущему документу

* word/styles.xml — стили применимые к документу. Отделяют данные от представления

* word/webSettings.xml — настройки отображения HTML частей документа и настройки того, как конвертировать документ в HTML

* word/fontTable.xml — список шрифтов используемых в документе

* word/theme1.xml — тема (состоит из цветовой схемы, шрифтов и форматирования)

![alt text](./examples/namelist.png)

## Документация для word/document.xml

1) document

2) body

3) p - paragrath - основная форма хранения текста, параграфы разделяются символом новой строки
  pPr - свойства параграфа (например, выравнивание и отступ) (применяются независимо от стилей)

4) r - raw - элемент, составляющий текстовый регион с набором общих свойств (работает на уровне символов)
rPr - свойства элемента

5) в документах могут встречаться секции (sectPr - section properties) - наборы параграфов с общими свойствами

цифры в свойствах - двадцатые пункта

1440 двадцатых пункта = 1 дюйм

![alt text](examples/document_example.png)

### Свойства параграфа

* pBdr - граница параграфа (top, left, bottom, right)

* bidi - направление текста справа налево

* framePr - для параграфов в рамке

* ind - отступ (опускается, если сохраняются предыдущие настройки)

  * start - (0 по умолчанию) - отступ для начала параграфа (startChars в символах)

  * end (0 по умолчанию) - отступ для конца параграфа (endChars в символах)

  * firstLine - отступ для первой строки (относительно отступа в данном параграфе)

  * hanging - отступ влево для первой строки (относительно отступа в данном параграфе)

* js - выравнивание (ST_Jc - все значения)

  * center - по центру

  * right - по правому краю

* numPr - параграф является элементом нумерованного или маркированного списка

  * ilvl - уровень вложенности списка (вложенность в другие списки) начинается с нуля

  * numId - номер для данного списка (каждому списку нулевого уровня присваивается уникальный идентификатор)

* outlineLvl - уровень вложенности данного параграфа в документе (может быть не всегда, нужен для оглавления), значения 0-9, по умолчанию 9 (нет уровней вложенности в документе)

* pStyle - стиль параграфа (ST_String)

  * val (default, heading) - значение связано со styleId
  
  * внутри стиля может быть numPr, тогда к параграфу применятеся нумерация, но стиль параграфа будет стилем AbstractNum, без конкретного уровня списка

* shd (shading) - фоновый цвет параграфа

* spacing - расстояние между параграфами и строками в параграфе (если опущено, то применяются предыдущие настройки)

  * after - расстояние после параграфа (ST_TwipsMeasure)
  
  * afterLines - расстояние после последней строки параграфа (указывается в 1/100 строк) 
  
  * before - расстояние перед параграфом (ST_TwipsMeasure)
  
  * beforeLines (аналогично afterLines)
  
  * line - число вертикальных пробелов между строками в параграфе, это число может быть в разных единицах измерения в зависимости от значания атрибута lineRule
 
* suppressLineNumbers - не нумеровать данный параграф и не учитывать его при вычислении номера номеров других параграфов

если указаны разные значения в настройках соседних параграфов, выбирается наибольшее

* tabs - список табуляций для данного параграфа

* textAlignment - вертикальное выравнивание текста в строках параграфа

### Свойства элемента

* toggle properties - page 615

* b (bold) - жирный шрифт (page 264)

* bdr - граница текстового элемента

* caps - отображать все буквы заглавными

* color - цвет текста

* effect - эффект анимации для текста

* emboss - рельефный текст

* highlight - цвет фона текстового элемента

* i (italic) - курсив

* imprint - еще один эффект для текста

* kerning - расстояние между символами в шрифте

* lang - язык

* pgNum - нумерация страницы

* rFonts - список шрифтов для элемента

* rStyle - стиль элемента

* характеристики элемента рассматриваются "справа налево"

* shd (shading) - фоновый цвет элемента

* spacing - сколько добавить "дополнительных пробелов" между символами в тексте

* sz - размер шрифта

* t - текст элемента, отображающийся в документе

* u (underline) - подчеркивание

* vanish - не показывать содержимое элемента

* w - сжатие / расширение текста

* tab, br, cr, sym - специальные символы, которые могут встретиться в тексте элемента

### Сводка по bold

1. Может быть <w:b val='1'/> либо val='0', то есть явное указание значения, есть жирность или нет

2. В стилях <w:b /> может также встречаться в свойствах элементов, тогда шрифт считается жирным

3. Может быть ситуация <w:b />, то есть без указания значения 
    * Если <w:b /> встречается и в параграфе, и в элементе, то весь параграф жирный
    * Если <w:b /> встречается в отдельных элементах, то жирные только они
    

Аналогичная ситуация с курсивом

## Numbering

в файле word/numberings.xml содержится информация обо всех типах списков, используемых в документе и их настройках

* abstractNum - описание свойств конкретного типа списка, этому типу присваивается номер (abstractNumId), который используется в word/document.xml (свойства наследуются)

    * styleLink - определение свойств списка, на это название в w:val могут ссылаться другие списки
    
    * numStyleLink - ссылка на другой abstractNum (чьи свойства используются), в w:val прописано значение, написанное в w:val для styleLink нужного нам abstractNum
    
    * restartNumberingAfterBreak
    
* abstractNumId (val="...") - уникальный идентификатор типа списка

* ilvl (val="...") - уровень вложенности

* lvl - описывает свойства списка определенного уровня внутри lvlOverride или внутри abstractNum
      
   * isLgl - если указан этот тег, то независимо от других настроек список (все уровни в тексте данного уровня) будет пронумерован арабскими цифрами  
  
   * lvlText (val="some text %num some text") - текстовое представление для нумерации (вместо %num подставляется нумерация конкретного стиля, num - номер уровня (<= текущего, больший игнорируется)) № уровня больше на 1, чем ilvl
    
    * numFmt - стиль ("upperLetter", "lowerRoman" ... с. 1415), если опущен, то это просто десятичные числа
    
    * pPr (ind - отступ) - свойства пронумерованного параграфа (перекрываются pPr свойствами параграфа в word/document.xml)
    
    * pStyle - стиль пронумерованного параграфа ???
    
    * rPr - свойства элемента - применяются к содержимому lvlText
    
    * start - стартовое значение нумерации
    
    * suff - разделитель между текстом нумерации и текстом параграфа (tab по умолчанию)

    * lvlJc (Justification) - выравнивание для данного уровня (val="start"/"end")
    
    * lvlRestart - начать отсчет элементов списка сначала для данного уровня (иначе рестарт после использования списков с меньшим значением глубины). Если val="0", то список не рестартится

* lvlOverride (Numbering Level Definition Override) - ипользуется внутри num, перегружает свойства конкретного уровня, отнаследованные от abstractNum и заменяет их

    * startOverride - переустановить нумерацию сначала для данного уровня

* num - тег для word/numberings.xml

* numId - номер экземпляра типа списка

![alt text](./examples/numbering_example.png)

## Стили

**Иерархия стилей:** 

![alt text](./examples/inheritance.png)

documentDefault -> таблицы -> параграфы -> нумерация -> символы -> прямое форматирование, то есть все, что не в стилях (document.xml)

* toggle properties: bold, italic - если их значения различаются в иерархии стилей, берется первое в иерархии значение (TODO более подробно расписать этот пункт)

* w:styles -> w:style; атрибуты:

    * default - стиль по умолчанию для данного типа стиля
    
    * styleId - уникальный идентификатор (имя) стиля
    
    * type: character, numbering, paragraph, table
    
* aliases - другие имена стилей

* basedOn - наследование стилей (параграфы и символы наследуют свойства параграфов и символов соответственно, нумерация не наследуется)

* name - имя стиля

* next - имя стиля для следующего создаваемого параграфа

* qFormat - если есть, то стиль - первичный для данного документа

* uiPriority - приоритет стиля

* Document Defaults

    * docDefaults - настройки стиля по умолчанию
    
    * pPr, pPrDefault
    
    * rPr, rPrDefault 
    
* Numbering Styles (type="numbering") в pPr указывается только numPr

* Paragraph Styles (type="paragraph")

    * w:pStyle w:val="..."
    
    * numbering in paragraph style - numPr внутри стиля, не используется уровень списка. В numbering.xml для данного numId есть AbstractNum, внутри которого какой-то уровень ссылается на данный стиль. Этот уровень и выбирается, и применяются его стили
    
    * pPr - свойства параграфа
    
* Run styles (type="character")
    
    * rPr - свойства элемента

## Headers and footers

сам текст находится в отдельных файлах (например word/header1.xml, word/footer1.xml) 

* hdr - содержимое header (аналогично содержимому body для документа)

* ftr - содержимое footer (аналогично содержимому body для документа)

в файле word/document.xml находятся ссылки в свойствах секции

* sectPr

    * headerReference (type: first, default, even etc.)
    
    * footerReference
    
внутри секции хедеры и футеры могут быть трёх типов - для четных, нечетных страниц и первой страницы (для каждого типа отдельный файл)
 
Аналогично:

* footnote + footnoteReference

* endnote + endnoteReference

## TODO 

ind - if any single attribute on this element is omitted on a given paragraph, its value is determined by the setting previously set at any level of the style hierarchy (i.e. that previous setting remains unchanged).

numPr - The presence of this element specifies that the paragraph inherits the properties specified by the numbering definition in the num element (§17.9.15) at the level specified by the level specified in the lvl element (§17.9.6) and shall have an associated number positioned before the beginning of the text flow in this paragraph. When this element appears as part of the paragraph formatting for a paragraph style, then any numbering level defined using the ilvl element shall be ignored, and the pStyle element (§17.9.23) on the associated abstract numbering definition shall be used instead.

outlineLvl - This element specifies the outline level which shall be associated with the current paragraph in the document. The outline level specifies an integer which defines the level of the associated text. This level shall not affect the appearance of the text in the document, but shall be used to calculate the TOC field (§17.16.5.68) if the appropriate field switches have been set, and can be used by consumers to provide additional application behaviour.
The outline level of text in the document (specified using the val attribute) can be from 0 to 9, where 9 specifically indicates that there is no outline level specifically applied to this paragraph. If this element is omitted, then the outline level of the content is assumed to be 9 (no level).

suppressLineNumbers - This element specifies whether line numbers shall be calculated for lines in this paragraph by the consumer when line numbering is requested using the lnNumType element (§17.6.8) in the paragraph's parent section settings. This element specifies whether the current paragraph's lines should be exempted from line numbering which is applied by the consumer on this document, not just suppressing the display of the numbering, but removing these lines from the line numbering calculation.
If this element is omitted on a given paragraph, its value is determined by the setting previously
set at any level of the style hierarchy (i.e. that previous setting remains unchanged). If this setting is never specified in the style hierarchy, then the default line number settings for the section, as specified in the lnNumType element shall apply to each line of this paragraph.

[Example: Consider a document with three paragraphs, each of which are displayed on five lines , all contained in a section which has the lnNumType element specified. If the second paragraph should be exempted from that line numbering, this requirement would be specified using the following WordprocessingML:
  <w:pPr>
    <w:suppressLineNumbers />
</w:pPr>
The paragraph would then be exempted from line by a consumer at display time, which would result in paragraph one using line numbers one through five, the second paragraph having no line numbers, and the third paragraph using line numbers six through ten. end example]

vanish - This element specifies whether the contents of this run shall be hidden from display at display time in a document. [Note: The setting should affect the normal display of text, but an application can have settings to force hidden text to be displayed. end note]
This formatting property is a toggle property (§17.7.3).
If this element is not present, the default value is to leave the formatting applied at previous level in the style hierarchy .If this element is never applied in the style hierarchy, then this text shall not be hidden when displayed in a document.

[Example: Consider a run of text which must have the hidden text property turned on for the contents of the run. This constraint is specified using the following WordprocessingML:
  <w:rPr>
    <w:vanish />
</w:rPr>
This run declares that the vanish property is set for the contents of this run, so the contents of this run is hidden when the document contents are displayed. end example]

br - This element specifies that a break shall be placed at the current location in the run content. A break is a special character which is used to override the normal line breaking that would be performed based on the normal layout of the document’s contents. [Example: Normal breaking for English would occur only after a breaking space or optional hyphen character. end example]
The behavior of this break character (the location where text shall be restarted after this break) shall be determined by its type and clear attribute values, described below.

[Example: Consider the following sentence in a WordprocessingML document: This is a simple sentence.
Normally, just as shown above, this sentence would be displayed on a single line as it is not long enough to require line breaking (given the width of the current page). However, if a text wrapping break character (a typical line break) were inserted after the word is, as follows:
<w:r>
<w:t>This is</w:t>
<w:br/>
<w:t xml:space="preserve"> a simple sentence.</w:t>
</w:r>
This would imply that this break must be treated as a simple line break, and break the line after that word:
This is

a simple sentence.
The break character forced the following text to be restarted on the next available line in the document. end example]


cr - This element specifies that a carriage return shall be placed at the current location in the run content. A carriage return is the equivalent of Unicode character 000D, and is used to end the current line of text in WordprocessingML.
The behavior of a carriage return in run content shall be identical to a break character with null type and clear attributes, which shall end the current line and find the next available line on which to continue.

sym - This element specifies the presence of a symbol character at the current location in the run’s content. A symbol character is a special character within a run’s content which does not use any of the run fonts specified in the rFonts element (§17.3.2.26) (or by the style hierarchy).

lvlRestart - This element specifies a one-based index which determines when a numbering level should restart to its start value (§17.9.25). A numbering level restarts when an instance of the specified numbering level, which shall be higher (earlier than this level) or any earlier level is used in the given document's contents.

[Example: If this value is 2, then both level two and level one reset this value. end example]