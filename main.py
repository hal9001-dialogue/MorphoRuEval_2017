from tagger import *
from collections import defaultdict

def make_update():
    A = set()
    for tag in ['ADP','CONJ','H','PART','PRON']:
        print(tag)
        for line in open('lists/'+tag+'.txt', encoding='utf8'):
            if line > 'яя':
                continue
            W = line.rstrip().upper()
            L = W.lower()
            A.add('\t'.join([W,L,tag,'_']))
    for line in open('errors', encoding='utf8'):
        n,l = line.split('\t',1)
        if int(n) > 100 or any(a in l for a in
                               ['DET','PRON','H','\tнет\t','ADJ\tDegree=Cmp']):
            if 'PROPN\t_' in l:
                continue
            if 'NUM\tNumForm=Digit' in l:
                continue
            if any(a in l.split('\t')[0] for a in '.IXLCM0123456789',):
                continue
            A.add(l.rstrip().replace('PROPN','NOUN'))
    open('update_auto', 'w', encoding='utf8').write('\n'.join(sorted(A)))

def collect_errors(dictionary, path_list):
    err_count = defaultdict(int)
    def add_error(word, lemma, tag):
        if feat == 'X\t_': return
        ce['\t'.join([word, lemma, tag])] += 1
    for path in path_list:
        pname = path.split('/')[-1].split('.')[0]
        for line in open(path, encoding = 'utf8'):
            if '\t' in line and not 'PUNCT' in line:
                w,l,p,f = line.rstrip().split('\t')[1:5]
                t = p + '\t' + f
                W,l = w.upper(), l.lower()
                tag_var = dictionary[W]
                if len(tag_var) == 1:
                    dic_t = list(tag_var)[0]
                    if dic_t == 'X\t_': #No prediction
                        add_error(W, l, t)
                    elif dic_t.startswith('NUM'):
                        pass
                    elif dic_t == PF:
                        pass
                    elif dic_t.startswith(P):
                        if f != '_' and
                        not set(dic_t.split('\t')[1].split('|')) >=\
                            set(f.split('|')):
                            add_error(W, l, t)
                    else:
                        add_error(W, l, t)
                else:
                    if t not in tag_var:
                        tag_sim = list(filter(lambda x: x.startswith(p),
                                              tag_var))
                        if tag_sim:
                            s = set(F.split('|'))
                            if F != '_' and
                            not any(set(t.split('\t')[1].split('|')) >=\
                                    s for t in tag_sim):
                                add_error(W, l, t)
                        else:
                            add_error(W, l, t)
    err_file = open('errors', 'w', encoding='utf8')
    for error in sorted(err_count, key=lambda x:-err_count[x]):
        err_file.write(str(err_count[error]) + '\t' + error)
        err_file.write('\n')
    err_file.close()
##==============================================================================
LIST = ['tagged/c_gikrya_fixed.txt',
        'tagged/c_gikrya_new_test.out',
        'tagged/c_gikrya_new_train.out',
        'tagged/c_syntagrus_full.ud',
        'tagged/c_RNCgoldInUD_Morpho.conll',
        'tagged/c_unamb_sent_14_6.conllu']

OUT = ['test_set/JZ.txt',
       'test_set/Lenta.txt',
       'test_set/VK.txt']

try:
    D = Dictionary('dict.json')
except:
    D = Dictionary().parse(
        'dict.opcorpora.txt', 'map_oc').parse(
            'dict.aot.txt', 'map_aot').yoficate()
    collect_errors(D, LIST)
    make_update()
    D = Dictionary().parse(
        'dict.opcorpora.txt', 'map_oc').parse(
            'dict.aot.txt', 'map_aot').update(
                'update_auto').update('update_manual').yoficate()
    D.save('dict.json')

try:
    T = BFTagger(D, 'tagger.pickle')
except:
    T = BFTagger(D).load_freq('frequency')
    T.LIM = 1800
    T.POW = [1.5, 2.5, -1, 0.5, 2, -0.5, -1]
    T.learn_files(LIST)
    for counter in [T.hi, T.lo]:
        for k,v in list(counter.items()):
            if v <= 3:
                del counter[k]
    T.save('tagger.pickle')

for file in OUT:
    T.tag_file(file)
