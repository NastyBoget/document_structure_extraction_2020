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

* shd (shading) - фоновый цвет параграфа

* spacing - расстояние между параграфами и строками в параграфе (если опущено, то применяются предыдущие настройки)

  * after - расстояние после параграфа (ST_TwipsMeasure)
  
  * afterLines - расстояние после последней строки параграфа (указывается в 1/100 строк) 
  
  * before - расстояние перед параграфом (ST_TwipsMeasure)
  
  * beforeLines (аналогично afterLines)
  
  * line - число вертикальных пробелов между строками в параграфе, это число может быть в разных единицах измерения в зависимости от значания атрибута lineRule
  

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

* w - сжатие / расширение текста

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

    * isLgl - если указан этот тег, то независимо от других настроек список будет пронумерован арабскими цифрами
    
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

documentDefault -> таблицы -> параграфы -> нумерация -> символы -> прямое форматирование (document.xml)

* toggle properties: bold, italic

* w:styles -> w:style; атрибуты:

    * default - стиль по умолчанию для данного типа стиля
    
    * styleId - уникальный идентификатор (имя) стиля
    
    * type: character, numbering, paragraph, table
    
* aliases - другие имена стилей

* basedOn - наследование стилей

* name - имя стиля

* next - имя стиля для следующего параграфа

* qFormat - если есть, то стиль - первичный для данного документа

* uiPriority - приоритет стиля

* Document Defaults

    * docDefaults - настройки стиля по умолчанию
    
    * pPr, pPrDefault
    
    * rPr, rPrDefault 
    
* Numbering Styles (type="numbering")

* Paragraph Styles (type="paragraph")

    * w:pStyle w:val="..."
    
    * numbering in paragraph style - numPr внутри стиля, ссылается на abstractNum, перекрывает стиль в abstractNum
    
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
