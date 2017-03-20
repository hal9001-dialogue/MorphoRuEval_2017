try:
    import ujson as json
except:
    import json

from tagged.clean import normalize

SET_DIGIT = set('0123456789:.,-')
SET_ROMAN = set('IVXLCM-')
SET_GUESS = set(open('guess', encoding='utf8').read().splitlines())
SET_NOUN = set(filter((lambda x: x.startswith('NOUN')), SET_GUESS))
SET_ADJ = set(filter((lambda x: x.startswith('ADJ')), SET_GUESS))
SET_CYR = set(chr(x) for x in range(ord('А'), ord('Я')+1)) | set('Ё')
OPEN_POS = {'NOUN', 'ADJ', 'VERB'}

class Dictionary:
    def __init__(self, path=None, map_path=None):
        self.data = {}
        self.pred = {}
        if not path:
            return
        if map_path:
            self.parse(path, map_path)
        else:
            self.load(path)
    def parse(self, dict_path, map_path):
        tag_map = dict([line.split('\t')
                        for line in open(map_path).read().splitlines()])
        is_lemma, lemma = True, ''
        if 'aot' in map_path:
            enc, sep1, sep2 = 'cp1251', ';', ';'
        else:
            enc, sep1, sep2 = 'utf8', '\t', ' '
        for line in open(dict_path, encoding=enc):
            if sep1 not in line:
                is_lemma = True
            else:
                word, tags = line.rstrip().split(sep1, 1)
                if is_lemma:
                    is_lemma, lemma = False, word.lower()
                tags = '|'.join(filter(None,
                                      map(tag_map.get, tags.replace(
                                          sep2, ',').split(','))))
                if '#SKIP' in tags or word.startswith('('):
                    continue
                tags = normalize(tags)
                if word in self.data:
                    self.data[word][tags] = lemma
                else:
                    self.data[word] = {tags: lemma}
        return self
    def update(self, path):
        for line in open(path, encoding='utf8'):
            word, lemma, tags = line.rstrip().split('\t', 2)
            if word in self.data:
                self.data[word][tags] = lemma
            else:
                self.data[word] = {tags: lemma}
        return self
    def yoficate(self):
        for word in list(filter(lambda w: 'Ё' in w, self.data)):
            werd = word.replace('Ё', 'Е')
            if werd in self.data:
                self.data[werd].update(self.data[word])
            else:
                self.data[werd] = self.data[word]
        return self
    def learn(self):
        self.pred = {}
        for word, info in self.data.items():
            if len(word) < 4: continue
            for tag in info:
                if tag.split('\t')[0] in OPEN_POS:
                    w3 = word[-3:]
                    if w3 in self.pred:
                        self.pred[w3].add(tag)
                    else:
                        self.pred[w3] = {tag}
        return self
    def load(self, path):
        self.data = json.load(open(path))
        self.learn()
    def save(self, path):
        json.dump(self.data, open(path, 'w'), ensure_ascii=False)
    def get(self, word):
        WORD = word.upper()
        if WORD in self.data:
            return self.data[WORD]
        if 'Ё' in WORD:
            WERD = WORD.replace('Ё', 'Е')
            if WERD in self.data:
                return self.data[WERD]
        if '_' in WORD:
            WRD = WORD.replace('_', '')
            if WRD in self.data:
                return self.data[WRD]
        SW = set(WORD)
        if set(WORD) <= SET_DIGIT:
            return {'NUM\tNumForm=Digit': word}
        if WORD.endswith('.'):
            return {g:word.lower() for g in SET_ADJ}
        if not SET_CYR | SW:
            return {'X\t_': word}
        if WORD.endswith('.'):
            return {g:word.lower() for g in SET_NOUN}
        if len(WORD) > 3 and WORD[-3:] in self.pred:
            return {g:word.lower() for g in self.pred[WORD[-3:]]}
        return {g:word.lower() for g in SET_GUESS}
    def __getitem__(self, word):
        return self.get(word)
