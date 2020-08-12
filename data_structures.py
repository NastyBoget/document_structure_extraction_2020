from bs4 import BeautifulSoup
import re
from properties_extractor import change_paragraph_properties, change_run_properties
from typing import Dict, List, Union, Tuple, Optional


class BaseProperties:

    def __init__(self,
                 styles_extractor: "StylesExtractor",
                 properties: Optional["BaseProperties"] = None):
        """
        contains properties for paragraphs and runs
        jc, indent, size, bold, italic, underlined
        :param styles_extractor: StylesExtractor
        :param properties: Paragraph or Run for copying it's properties
        """
        if properties:
            self.jc = properties.jc
            self.indent = properties.indent.copy()
            self.size = properties.size
            self.bold = properties.bold
            self.italic = properties.italic
            self.underlined = properties.underlined
            properties.underlined = properties.underlined
        else:
            self.jc = 'left'
            self.indent = {'firstLine': 0, 'hanging': 0, 'start': 0, 'left': 0}
            self.size = 0
            self.bold = False
            self.italic = False
            self.underlined = False
        self.styles_extractor = styles_extractor


class Run(BaseProperties):

    def __init__(self,
                 properties: BaseProperties,
                 styles_extractor: "StylesExtractor"):
        """
        contains information about run properties
        :param properties: Paragraph or Run for copying it's properties
        :param styles_extractor: StylesExtractor
        """

        self.text = ""
        super().__init__(styles_extractor, properties)

    def get_text(self,
                 xml: BeautifulSoup):
        """
        makes the text of run
        :param xml: BeautifulSoup tree with run properties
        """
        for tag in xml:
            if tag.name == 't' and tag.text:
                self.text += tag.text
            elif tag.name == 'tab':
                self.text += '\t'
            elif tag.name == 'br':
                self.text += '\n'
            elif tag.name == 'cr':
                self.text += '\r'
            elif tag.name == 'sym':
                try:
                    self.text += chr(int("0x" + tag['w:char'], 16))
                except KeyError:
                    pass

    def __eq__(self,
               other: "Run") -> bool:
        """
        :param other: Run
        """
        if not isinstance(other, Run):
            return False
        return self.size == other.size and self.bold == other.bold \
               and self.italic == other.italic and self.underlined == other.underlined


class Paragraph(BaseProperties):

    def __init__(self,
                 xml: BeautifulSoup,
                 styles_extractor: "StylesExtractor",
                 numbering_extractor: "NumberingExtractor"):
        """
        contains information about paragraph properties
        :param xml: BeautifulSoup tree with paragraph properties
        :param styles_extractor: StylesExtractor
        :param numbering_extractor: NumberingExtractor
        """
        self.numbering_extractor = numbering_extractor
        self.runs = []
        # level of list of the paragraph is a list item
        self.list_level = None

        self.xml = xml
        super().__init__(styles_extractor)
        self.parse()

    def parse(self) -> None:
        """
        makes the list of paragraph's runs according to the style hierarchy
        """
        # hierarchy: properties in styles -> direct properties (paragraph, character)
        # 1) documentDefault (styles.xml)
        # 2) tables (styles.xml)
        # 3) paragraphs styles (styles.xml)
        # 4) numbering styles (styles.xml, numbering.xml)
        # 5) characters styles (styles.xml)
        # 6) paragraph direct formatting (document.xml)
        # 7) numbering direct formatting (document.xml, numbering.xml)
        # 8) character direct formatting (document.xml)

        # 1) docDefaults
        self.styles_extractor.parse(None, self, "paragraph")
        # 2) we ignore tables

        # 3) paragraph styles
        # 4) numbering styles within styles_extractor
        if self.xml.pStyle:
            self.styles_extractor.parse(self.xml.pStyle['w:val'], self, "paragraph")

        # 5) character style parsed later for each run
        # 6) paragraph direct formatting
        if self.xml.pPr:
            change_paragraph_properties(self, self.xml.pPr)

        # 7) numbering direct formatting
        numbering_run = self._get_numbering_formatting()
        if numbering_run:
            self.runs.append(numbering_run)

        # 8) character direct formatting
        self._make_run_list()

    def _get_numbering_formatting(self) -> Optional[Run]:
        """
        if the paragraph is a list item applies it's properties to the paragraph
        adds numbering run to the list of paragraph runs
        :returns: numbering run if there is the text in numbering else None
        """
        if self.xml.numPr and self.numbering_extractor:
            numbering_run = Run(self, self.styles_extractor)
            self.numbering_extractor.parse(self.xml.numPr, self, numbering_run)
            if numbering_run.text:
                if self.xml.pPr.rPr:
                    change_run_properties(numbering_run, self.xml.pPr.rPr)
                return numbering_run
        return None

    def _make_run_list(self):
        """
        makes runs of the paragraph and adds them to the paragraph list
        """
        run_list = self.xml.find_all('w:r')
        for run_tree in run_list:
            new_run = Run(self, self.styles_extractor)
            if run_tree.rStyle:
                self.styles_extractor.parse(run_tree.rStyle['w:val'], new_run, "character")
                if self.xml.pPr and self.xml.pPr.rPr:
                    change_run_properties(new_run, self.xml.pPr.rPr)
            if run_tree.rPr:
                change_run_properties(new_run, run_tree.rPr)
            new_run.get_text(run_tree)
            if not new_run.text:
                continue

            if self.runs and self.runs[-1] == new_run:
                self.runs[-1].text += new_run.text
            else:
                self.runs.append(new_run)


class ParagraphInfo:

    def __init__(self,
                 paragraph: Paragraph):
        """
        extracts information from paragraph properties
        :param paragraph: Paragraph for extracting it's properties
        """
        self.text = ""
        self.list_level = paragraph.list_level
        self.properties = []
        for run in paragraph.runs:
            start, end = len(self.text), len(self.text) + len(run.text)
            if start == end:
                continue
            if not self.text:
                self.text = run.text
            else:
                self.text += run.text
            properties = dict()
            properties['indent'] = paragraph.indent.copy()
            properties['alignment'] = paragraph.jc
            if run.size:
                properties['size'] = run.size
            else:
                properties['size'] = paragraph.size
            properties['bold'] = run.bold
            properties['italic'] = run.italic
            properties['underlined'] = run.underlined
            self.properties.append([start, end, properties])

    def _get_hierarchy_level(self) -> Optional[Tuple[int, int]]:
        """
        defines the type of paragraph and it's level according to it's type
        :return: hierarchy level if the paragraph isn't raw text
        """
        # 0 - Глава, Параграф
        # 1 - Статья, Пункт
        # 2 - list item
        if self.list_level:
            return 2, self.list_level
        if re.match(r"^(Глава|Параграф)\s*(\d\\.)*(\d\\.?)?", self.text):
            return 0, 0
        if re.match(r"^(Статья|Пункт)\s*(\d\\.)*(\d\\.?)?", self.text):
            return 1, 0
        return None

    def get_info(self) -> Dict[str, Union[str, Optional[Tuple[int, int]],
                                          List[List[Union[int, int,
                                                          Dict[str, Union[int, bool, str, Dict[str, int]]]]]]]]:
        """
        returns paragraph properties in special format
        :return: dictionary {"text": "",
        "type": ""("paragraph" ,"list_item", "raw_text"), "level": (1,1) or None (hierarchy_level),
        "properties": [[start, end, {"indent", "size", "alignment", "bold", "italic", "underlined"}], ...] }
        start, end - character's positions begin with 0, end isn't included
        indent = {"firstLine", "hanging", "start", "left"}
        """
        hierarchy_level = self._get_hierarchy_level()
        if not hierarchy_level:
            return {"text": self.text, "type": "raw_text", "level": hierarchy_level, "properties": self.properties}
        if hierarchy_level[0] == 0 or hierarchy_level[0] == 1:
            paragraph_type = "paragraph"
        elif hierarchy_level[0] == 2:
            paragraph_type = "list_item"
        else:
            paragraph_type = "raw_text"
        return {"text": self.text, "type": paragraph_type, "level": hierarchy_level, "properties": self.properties}

    @property
    def get_text(self) -> str:
        """
        :return: text of the paragraph
        """
        return self.text
