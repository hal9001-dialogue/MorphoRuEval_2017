def normalize(tags):
    tags = tags.replace('\t','|')
    if '|' in tags:
        P, F = tags.split('|',1)
        F = F.replace('_','')
    else:
        P, F = tag, ''
    F = dict(a.split('=') for a in F.split('|') if '=' in a)
    if P == "NOUN":
        keys = ["Gender", "Number", "Case"]
    elif P == "ADJ":
        keys = ["Gender", "Number", "Case", "Variant", 'Degree']
    elif P == "PRON":
        keys = ["Gender", "Number", "Case", 'Person']
    elif P == "DET":
        keys = ["Gender", "Number", "Case"]
    elif P == "VERB":
        keys = ["Gender", "Number", "VerbForm", "Mood", "Tense", 'Person']
    elif P == "ADV":
        keys = ["Variant",'Degree']
    elif P == "NUM":
        keys = ["Gender", "Number", "Case", "NumForm"]
    else:
        keys = []
    for k in list(F):
        if k not in keys:
            del F[k]
    if 'Variant' in F:
        if F['Variant'] == 'Brev':
            F['Variant'] = 'Short'
        elif F['Variant'] == 'Full':
            del F['Variant']
    F = '|'.join(sorted(k+'='+v for k,v in F.items()))
    if not F: F = '_'
    return P + '\t' + F

def clean(input_path):
    output_path = 'c_'+input_path
    output = open(output_path, 'w', encoding='utf8')
    for line in open(input_path, encoding='utf8'):
        if '\t' in line:
            i,W,L,PF = line.rstrip().split('\t',3)
            L = L.lower()
            output.write('\t'.join([i,W,L,normalize(PF)]))
        output.write('\n')
    output.close()

try:
    open('c_gikrya_fixed.txt').close()
except:
    list(map(clean, ['gikrya_fixed.txt',
                     'gikrya_new_test.out',
                     'gikrya_new_train.out',
                     'RNCgoldInUD_Morpho.conll',
                     'syntagrus_full.ud',
                     'unamb_sent_14_6.conllu']))
