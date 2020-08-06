import zipfile
from bs4 import BeautifulSoup
from styles_extractor import StylesExtractor
from properties_extractor import change_properties
from data_structures import BaseProperties, Paragraph, Raw
import re
import os

bad_file_num = 0
# pages 691 - 733 in the documentation

# page 1424
numFmtList = {"decimal": "1",  # 1, 2, 3, ..., 10, 11, 12, ...
              "lowerLetter": "a",  # a, b, c, ..., y, z, aa, bb, cc, ..., yy, zz, aaa, bbb, ccc, ...
              "lowerRoman": "i",  # i, ii, iii, iv, ..., xviii, xix, xx, xxi, ...
              "none": "",
              "russianLower": "а",  # а, б, в, ..., ю, я, аа, бб, вв, ..., юю, яя, ааа, ббб, ввв, ...
              "russianUpper": "А",  # А, Б, В, ..., Ю, Я, АА, ББ, ВВ, ..., ЮЮ, ЯЯ, ААА, БББ, ВВВ, ...
              "upperLetter": "A",  # A, B, C, ..., Y, Z, AA, BB, CC, ..., YY, ZZ, AAA, BBB, CCC, ...
              "upperRoman": "I",  # I, II, III, IV, ..., XVIII, XIX, XX, XXI, ...
              }


def get_next_item(num_fmt: str,
                  shift: int):
    """
    computes the next item of the list sequence
    :param num_fmt: some value from numFmtList
    :param shift: shift from the beginning of list numbering
    :return: string representation of the next numbering item
    """
    if num_fmt == "none":
        return numFmtList[num_fmt]
    if num_fmt == "decimal":
        return str(int(numFmtList[num_fmt]) + shift)
    if num_fmt == "lowerLetter" or num_fmt == "upperLetter":
        shift1, shift2 = shift % 26, shift // 26 + 1
        return chr(ord(numFmtList[num_fmt]) + shift1) * shift2
    if num_fmt == "russianLower" or num_fmt == "russianUpper":
        shift1, shift2 = shift % 32, shift // 32 + 1
        return chr(ord(numFmtList[num_fmt]) + shift1) * shift2
    if num_fmt == "lowerRoman" or num_fmt == "upperRoman":
        # 1 = I, 5 = V, 10 = X, 50 = L, 100 = C, 500 = D, 1000 = M.
        mapping = [(1000, 'm'), (500, 'd'), (100, 'c'),
                   (50, 'l'), (10, 'x'), (5, 'v'), (1, 'i')]
        result = ""
        for number, letter in mapping:
            cnt, shift = shift // number, shift % number
            if num_fmt == "upperRoman":
                letter = chr(ord(letter) + ord('A') - ord('a'))
            result += letter * cnt
        return result


# page 1402
getSuffix = {"nothing": "",
             "space": " ",
             "tab": "\t"}


class AbstractNum:

    def __init__(self,
                 tree: BeautifulSoup,
                 styles_extractor: StylesExtractor):
        """
        :param tree: BeautifulSoup tree with abstractNum content
        :param styles_extractor: StylesExtractor
        """
        self.styles_extractor = styles_extractor
        self.abstract_num_id = tree['w:abstractNumId']
        self.properties = {}  # properties for all levels {"styleLink", "restart"}

        if tree.numStyleLink:
            # styleLink-> abstractNumId of the other numbering
            self.properties['styleLink'] = tree.numStyleLink['w:val']
        else:
            self.properties['styleLink'] = None

        try:
            if tree['w15:restartNumberingAfterBreak']:
                self.properties['restart'] = bool(int(tree['w15:restartNumberingAfterBreak']))
        except KeyError:
            self.properties['restart'] = False  # TODO check this behaviour
        # properties for each list level {level number: properties}
        # properties = {"lvlText", "numFmt", "start", "lvlRestart", "restart", "suff", "styleId", "pPr", "rPr"}
        self.levels = {}

    def parse(self,
              lvl_list: list):
        """
        save information about levels in self.levels
        :param lvl_list: list with BeautifulSoup trees which contain information about levels
        """
        # isLgl (only mention)
        # lvlText (val="some text %num some text")
        # numFmt (val="bullet", "decimal")
        # pPr -> ind
        # pStyle -> pPr
        # rPr -> sz, bold, italic, underlined
        # start (w:val="1")
        # suff (w:val="nothing", "tab" - default, "space")
        # lvlRestart (w:val="0")
        # restart - startOverride for each level
        for lvl in lvl_list:
            ilvl = lvl['w:ilvl']
            if ilvl not in self.levels:
                self.levels[ilvl] = {}
            if lvl.lvlText:
                self.levels[ilvl]['lvlText'] = lvl.lvlText['w:val']
            elif 'lvlText' not in self.levels[ilvl]:
                self.levels[ilvl]['lvlText'] = ""

            if lvl.isLgl:
                self.levels[ilvl]['numFmt'] = 'decimal'
            else:
                if lvl.numFmt:
                    self.levels[ilvl]['numFmt'] = lvl.numFmt['w:val']
                elif 'numFmt' not in self.levels[ilvl]:
                    self.levels[ilvl]['numFmt'] = 'none'

            if lvl.start:
                self.levels[ilvl]['start'] = int(lvl.start['w:val'])
            elif 'start' not in self.levels[ilvl]:
                self.levels[ilvl]['start'] = 1

            if lvl.lvlRestart:
                self.levels[ilvl]['lvlRestart'] = bool(int(lvl.lvlRestart['w:val']))
            elif 'lvlRestart' not in self.levels[ilvl]:
                self.levels[ilvl]['lvlRestart'] = True
            if 'restart' not in self.levels[ilvl]:
                self.levels[ilvl]['restart'] = self.properties['restart']

            if lvl.suff:
                self.levels[ilvl]['suff'] = getSuffix[lvl.suff['w:val']]
            elif 'suff' not in self.levels[ilvl]:
                self.levels[ilvl]['suff'] = getSuffix["tab"]

            # TODO check override case
            # extract information from paragraphs and raws properties
            if lvl.pStyle:
                self.levels[ilvl]['styleId'] = lvl.pStyle['w:val']
            elif 'styleId' not in self.levels[ilvl]:
                self.levels[ilvl]['styleId'] = None

            # paragraph -> raw
            if lvl.pPr:
                self.levels[ilvl]['pPr'] = lvl.pPr
            elif 'pPr' not in self.levels[ilvl]:
                self.levels[ilvl]['pPr'] = None

            if lvl.rPr:
                self.levels[ilvl]['rPr'] = lvl.rPr
            elif 'rPr' not in self.levels[ilvl]:
                self.levels[ilvl]['rPr'] = None


class Num(AbstractNum):

    def __init__(self,
                 num_id: str,
                 abstract_num_list: dict,
                 num_list: dict,
                 styles_extractor: StylesExtractor):
        """
        :param num_id: numId for num element
        :param abstract_num_list: dictionary with abstractNum BeautifulSoup trees
        :param num_list: dictionary with num BeautifulSoup trees
        :param styles_extractor: StylesExtractor
        """
        self.num_id = num_id
        num_tree = num_list[num_id]
        abstract_num_tree = abstract_num_list[num_tree.abstractNumId['w:val']]
        super().__init__(abstract_num_tree, styles_extractor)  # create properties
        # extract the information from numStyleLink
        while self.properties['styleLink']:
            for abstract_num in abstract_num_list.values():
                if abstract_num.find('w:styleLink', attrs={'w:val': self.properties['styleLink']}):
                    abstract_num_tree = abstract_num
                    break
            super().__init__(abstract_num_tree, styles_extractor)
        self.parse(abstract_num_tree.find_all('w:lvl'))

        # override some of abstractNum properties
        if num_tree.lvlOverride:
            lvl_list = num_tree.find_all('w:lvlOverride')
            self.parse(lvl_list)
            # w:startOverride
            for lvl in lvl_list:
                if lvl.startOverride:
                    self.levels[lvl['w:ilvl']]['restart'] = True
                    self.levels[lvl['w:ilvl']]['start'] = int(lvl.startOverride['w:val'])

    def get_level_info(self,
                       level_num: str):
        return self.levels[level_num].copy()


class NumberingExtractor:

    def __init__(self,
                 xml: BeautifulSoup,
                 styles_extractor: StylesExtractor):
        """
        :param xml: BeautifulSoup tree with numberings
        :param styles_extractor: StylesExtractor
        """
        if xml:
            self.numbering = xml.numbering
            if not self.numbering:
                raise Exception("there are no numbering")
        else:
            raise Exception("xml must not be empty")

        if styles_extractor:
            self.styles_extractor = styles_extractor
        else:
            raise Exception("styles extractor must not be empty")

        self.numerations = {}  # {(abstractNumId, ilvl): current number for list element}
        self.prev_num_id = None
        self.prev_abstract_num_id = None
        self.prev_ilvl = {}  # {abstractNumId: ilvl} previous ilvl for list element with given numId
        self.prev_numId = {}  # {abstractNumId: numId} previous numId for list element with given numId

        abstract_num_list = {abstract_num['w:abstractNumId']: abstract_num
                             for abstract_num in xml.find_all('w:abstractNum')}
        num_list = {num['w:numId']: num for num in xml.find_all('w:num')}

        # dictionary with num properties
        self.num_list = {num_id: Num(num_id, abstract_num_list, num_list, styles_extractor) for num_id in num_list}

    def get_list_text(self, ilvl, num_id):
        if num_id not in self.num_list:
            return ""
        abstract_num_id = self.num_list[num_id].abstract_num_id
        lvl_info = self.num_list[num_id].get_level_info(ilvl)
        # there is the other list
        if self.prev_abstract_num_id and self.prev_num_id and self.prev_abstract_num_id != abstract_num_id \
                and self.num_list[self.prev_num_id].properties['restart']:
            del self.prev_ilvl[self.prev_abstract_num_id]
        # there is the information about this list
        if abstract_num_id in self.prev_ilvl:
            prev_ilvl = self.prev_ilvl[abstract_num_id]
            # startOverride:
            if abstract_num_id in self.prev_numId:
                prev_num_id = self.prev_numId[abstract_num_id]
            else:
                prev_num_id = None
            if prev_num_id and prev_num_id != num_id and lvl_info['restart']:
                self.numerations[(abstract_num_id, ilvl)] = lvl_info['start']
            # it's a new level
            elif prev_ilvl < ilvl and lvl_info['lvlRestart'] or (abstract_num_id, ilvl) not in self.numerations:
                self.numerations[(abstract_num_id, ilvl)] = lvl_info['start']
            # it's a continue of the old level
            else:
                self.numerations[(abstract_num_id, ilvl)] += 1
        # there isn't the information about this list
        else:
            self.numerations[(abstract_num_id, ilvl)] = lvl_info['start']
        # print("numId = {}, prevNumId = {}, abstractNumId = {}, prevAbstractNumId = {},"
        #       " lvl = {}".format(num_id, self.prev_num_id, abstract_num_id,
        #                          self.prev_abstract_num_id, ilvl))
        self.prev_ilvl[abstract_num_id] = ilvl
        self.prev_numId[abstract_num_id] = num_id
        self.prev_abstract_num_id = abstract_num_id
        self.prev_num_id = num_id

        text = lvl_info['lvlText']
        levels = re.findall(r'%\d+', text)
        # print("lvl_info = {}, numerations = {}".format(lvl_info, self.numerations))
        for level in levels:
            # level = '%level'
            level = level[1:]
            text = re.sub(r'%\d+', self.get_next_number(num_id, level), text, count=1)
        text += lvl_info['suff']
        return text

    def get_next_number(self, num_id, level):
        abstract_num_id = self.num_list[num_id].abstract_num_id
        # level = ilvl + 1
        ilvl = str(int(level) - 1)
        lvl_info = self.num_list[num_id].get_level_info(ilvl)
        if lvl_info['numFmt'] == "bullet":
            return lvl_info['lvlText']

        try:
            shift = self.numerations[(abstract_num_id, ilvl)] - 1
        except KeyError as err:
            # TODO handle very strange list behaviour
            # print('=================')
            # print("abstractNumId = {}, ilvl = {}".format(abstract_num_id, ilvl))
            # print('=================')
            # if we haven't found given abstractNumId we use previous
            # TODO check proposal lowering ilvl
            try:
                shift = self.numerations[(self.prev_abstract_num_id, ilvl)] - 1
            except KeyError:
                self.numerations[(abstract_num_id, ilvl)] = 1
                shift = 0
        num_fmt = get_next_item(lvl_info['numFmt'], shift)
        return num_fmt

    def parse(self,
              xml: BeautifulSoup,
              paragraph_properties: BaseProperties,
              raw_properties: BaseProperties):
        """
        parses numPr content and extracts properties for paragraph for given numId and list level
        changes old_paragraph properties according to list properties
        changes raw_properties adding text of numeration and it's properties
        :param xml: BeautifulSoup tree with numPr from document.xml or styles.xml (style content)
        :param paragraph_properties: Paragraph for changing
        :param raw_properties: Raw for changing
        """
        if not xml:
            return None
        ilvl, num_id = xml.ilvl, xml.numId
        if not num_id or num_id['w:val'] not in self.num_list:
            return None
        else:
            num_id = num_id['w:val']

        if not ilvl:
            try:
                style_id = xml['w:styleId']
                num = self.num_list[num_id]
                # find link on this styleId in the levels list
                for level_num, level in num.levels.items():
                    if 'styleId' in level and level['styleId'] == style_id:
                        ilvl = level_num
            except KeyError:
                # print('=================')
                # print("error in numbering style")
                # print('=================')
                return None
        else:
            ilvl = ilvl['w:val']

        lvl_info = self.num_list[num_id].get_level_info(ilvl)
        text = self.get_list_text(ilvl, num_id)
        if lvl_info['styleId']:
            self.styles_extractor.parse(lvl_info['styleId'], paragraph_properties, "numbering")
            if hasattr(paragraph_properties, 'r_pr') and paragraph_properties.r_pr:
                change_properties(raw_properties, paragraph_properties.r_pr)
        if lvl_info['pPr']:
            change_properties(paragraph_properties, lvl_info['pPr'])
        if lvl_info['rPr']:
            change_properties(raw_properties, lvl_info['rPr'])
        raw_properties.text = text


if __name__ == "__main__":
    wrong_files = []
    bad_zip_files = []
    file_without_lists = 0
    i = 0
    choice = input()
    if choice == 'test':
        filenames = os.listdir('examples/docx/docx')
    else:
        filenames = [choice]
    total = len(filenames)
    try:
        for filename in filenames:
            i += 1
            try:
                if choice == "test":
                    document = zipfile.ZipFile('examples/docx/docx/' + filename)
                else:
                    document = zipfile.ZipFile('examples/' + filename)
                try:
                    numbering_bs = BeautifulSoup(document.read('word/numbering.xml'), 'xml')
                except KeyError:
                    file_without_lists += 1
                else:
                    document_bs = BeautifulSoup(document.read('word/document.xml'), 'xml')
                    styles_bs = BeautifulSoup(document.read('word/styles.xml'), 'xml')
                    se = StylesExtractor(styles_bs)
                    ne = NumberingExtractor(numbering_bs, se)
                    se.numbering_extractor = ne
                    for paragraph in document_bs.body:
                        if choice != 'test':
                            paragraph_text = map(lambda x: x.text, paragraph.find_all('w:t'))
                            res = ""
                            for item in paragraph_text:
                                res += item
                        else:
                            res = ""
                        if paragraph.numPr:
                            p = Paragraph(paragraph, se, ne)
                            r = Raw(None, se)
                            ne.parse(paragraph.numPr, p, r)
                            if choice != 'test':
                                print(p)
                                print(res)
                        else:
                            if choice != 'test':
                                print(res)
                if choice == 'test':
                    print(f"\r{i} objects are processed...", end='', flush=True)
            except zipfile.BadZipFile:
                bad_zip_files.append(filename)
            except KeyError:
                bad_file_num += 1
                wrong_files.append(filename)
    except Exception:
        # total: 2193, bad files: 371, without lists: 289
        if choice == 'test':
            print('total: {}, bad files: {}, without lists: {}'.format(total, bad_file_num, file_without_lists))
            print('bad zip: ', bad_zip_files)
            print('wrong_files: ', wrong_files)
