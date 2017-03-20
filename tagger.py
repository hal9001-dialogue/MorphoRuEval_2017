from dictionary import *
from collections import defaultdict
import pickle

PUNCT = set('"\'/\\{}()[]<>«»*-.,:;!?…—')
collapse = lambda punct_list: ''.join(sorted(set(''.join(punct_list))))

def get_sentences(file_path):
    sent = {'punct':[], 'words':[]}
    for line in open(file_path, encoding='utf8'):
        if '\t' in line:
            splitted = line.rstrip().split('\t')
            if len(splitted) > 3:
                word, lemma, pos, feat = splitted[1:5]
            elif len(splitted) > 1:
                word = splitted[1]
                lemma = word.lower()
                pos, feat = 'PUNCT' if set(word) <= PUNCT else '_', '_'
            else:
                continue
            if pos == 'PUNCT':
                (sent['words'][-1] if sent['words'] else
                 sent)['punct'].append(word)
            else:
                sent['words'].append({'word': word,
                                      'lemma': lemma,
                                      'tag': pos + '\t' + feat,
                                      'punct': []})
        else:
            if any(sent.values()):
                yield sent
                sent = {'punct':[], 'words':[]}

def dumps_sentence(sent):
    lines = []
    def push_punct_seq(punct_seq):
        lines.extend(['\t'.join([punct, punct, 'PUNCT', '_'])
                      for punct in punct_seq]) 
    push_punct_seq(sent['punct'])
    for word in sent['words']:
        lines.append('\t'.join([word['word'], word['lemma'], word['tag']]))
        push_punct_seq(word['punct'])
    return '\n'.join(str(i) + '\t' + line
                     for i,line in enumerate(lines, start=1))

def dump_sents(sent_seq, file_path):
    open(file_path, 'w', encoding='utf8').write(
        '\n\n'.join(map(dumps_sentence, sent_seq)))

def dump_sents_incr(sent_seq, file_path):
    out = open(file_path, 'w', encoding='utf8')
    for sent in map(dumps_sentence, sent_seq):
        out.write(sent + '\n\n')
    out.close()

class BFTagger():
    def __init__(self, dictionary=None, data_path=None):
        (self.set_dict if type(dictionary) == type(Dictionary())
         else self.load_dict)(dictionary)
        self.load(data_path)
    def save(self, path):
        pickle.dump([self.LIM, self.POW, self.freq, self.hi, self.lo],
                    open(path, 'wb'))
        return self
    def load(self, path):
        try:
            self.LIM, self.POW, self.freq, self.hi, self.lo =\
                      pickle.load(open(path, 'rb'))
        except:
            self.LIM = 1000
            self.POW = [1, 1, -1, 1, 1, -1, -1]
            self.freq = {}
            self.hi, self.lo = defaultdict(int), defaultdict(int)
        return self
    def load_dict(self, path):
        self.dict = Dictionary(path)
        return self
    def set_dict(self, dictionary):
        self.dict = dictionary
        return self
    def load_freq(self, path):
        self.freq = {w:i for i,w in enumerate(open(path, encoding='utf8'
                                                   ).read().splitlines())}
        return self
    def learn_files(self, path_seq):
        for path in path_seq:
            self.learn_file(path)
        return self
    def learn_file(self, path):
        for sent in get_sentences(path):
            self.learn(sent)
        return self
    def learn(self, sent):
        lt, lp, lg, lw = '#', collapse(sent['punct']), frozenset(), ''
        for word in sent['words']:
            ct, cp = word['tag'], collapse(word['punct'])
            cw = word['word'].upper()
            cg = frozenset(self.dict[cw].keys())
            self.lo[('wt',cw,ct)] += 1
            if self.freq.get(cw, self.LIM) < self.LIM:
                self.hi[('tptg',cw,lt,lp,ct,cg)] += 1
                self.hi[('gtpt',cw,lg,lt,lp,ct)] += 1
                self.hi[('tpt',cw,lt,lp,ct)] += 1
                self.hi[('tt',cw,lt,ct)] += 1
                self.hi[('gt',cw,cg,ct)] += 1
            else:
                self.lo[('tptg',lt,lp,ct,cg)] += 1
                self.lo[('gtpt',lg,lt,lp,ct)] += 1
                self.lo[('tpt',lt,lp,ct)] += 1
                self.lo[('tt',lt,ct)] += 1
                self.lo[('gt',cg,ct)] += 1
                self.lo[('t',ct)] += 1
            lt, lp, lg, lw = ct, cp, cg, cw
        return self
    def prob_lo(self, lt, ct, lp, lw, cw, lg, cg):
        return self.lo.get(('tptg',lt,lp,ct,cg), 1) ** self.POW[0] *\
               self.lo.get(('gtpt',lg,lt,lp,ct), 1) ** self.POW[1] *\
               self.lo.get(('tpt',lt,lp,ct), 1) ** self.POW[2] *\
               self.lo.get(('tt',lt,ct), 1) ** self.POW[3] *\
               self.lo.get(('wt',cw,ct), 1) ** self.POW[4] *\
               self.lo.get(('gt',cg,ct), 1) ** self.POW[5] *\
               self.lo.get(('t',ct), 1) ** self.POW[6]
    def prob_hi(self, lt, ct, lp, lw, cw, lg, cg):
        return self.hi.get(('tptg',cw,lt,lp,ct,cg), 1) ** self.POW[0] *\
               self.hi.get(('gtpt',cw,lg,lt,lp,ct), 1) ** self.POW[1] *\
               self.hi.get(('tpt',cw,lt,lp,ct), 1) ** self.POW[2] *\
               self.hi.get(('tt',cw,lt,ct), 1) ** self.POW[3] *\
               self.lo.get(('wt',cw,ct), 1) ** self.POW[4] *\
               self.hi.get(('gt',cw,cg,ct), 1) ** self.POW[5] *\
               self.lo.get(('wt',cw,ct), 1) ** self.POW[6]
    def prob(self, word):
        return (self.prob_hi if self.freq.get(word, self.LIM) < self.LIM else
                self.prob_lo)
    def tag_file(self, path_input, path_output=None):
        if not path_output:
            split_path = path_input.split('.')
            split_path.insert(-1, 'tagged')
            path_output = '.'.join(split_path)
        dump_sents_incr(map(self.tag, get_sentences(path_input)), path_output)
        return self
    def tag(self, sent):
        if not sent['words']:
            return sent
        cw = sent['words'][0]['word'].upper()
        cg = frozenset(self.dict[cw].keys())
        lp, lg, lw = collapse(sent['punct']), frozenset(), ''
        prob_ = self.prob(cw)
        var = [[prob_('#',t,lp,lw,cw,lg,cg), t] for t in cg]
        lp, lg, lw = collapse(sent['words'][0]['punct']), cg, cw
        for word in sent['words'][1:]:
            cw = word['word'].upper()
            cg = frozenset(self.dict[cw].keys())
            prob_ = self.prob(cw)
            new_var = []
            for t in cg:
                best = max(var, key =
                           lambda x:x[0]*prob_(x[-1],t,lp,lw,cw,lg,cg)).copy()
                best[0] *= prob_(best[-1],t,lp,lw,cw,lg,cg)
                new_var.append(best + [t])
            var = new_var
            if len(var) == 1:
                var[0][0] = 1.
            lp, lg, lw = collapse(word['punct']), cg, cw
        tags = max(var, key=lambda x:x[0])[1:]
        result = sent.copy()
        for word,tag in zip(result['words'], tags):
            word['tag'] = tag
            word['lemma'] = self.dict[word['word']][tag]
        return result
