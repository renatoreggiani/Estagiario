import spacy
from nltk import RSLPStemmer
from spacy.tokens import Doc
from spacy.matcher import Matcher
from datetime import date, timedelta

nlp = spacy.load('pt_core_news_sm')


##
def remove_stopwords(doc, manter=[]):
    """Remove stopwords da sentenca, lista das stopwords podem ser consultadas com comando
    spacy.lang.pt.stop_words.STOP_WORDS
    Parametros:
    manter: mantem a(s) palavra(s) mesmo estando na lista de stopword
    """
    doc_sem_stopwords = [p.orth_ for p in doc if (not any([p.is_stop, p.is_punct]) or p.orth_ in manter)]
    doc_sem_stopwords = nlp(' '.join(doc_sem_stopwords))
    return doc_sem_stopwords


## dbt tec transformar numeros por extenso em numero antes de remover stopwords
def date_getter(doc):
    """Transforma data no texto em obj datetime.date, numeros devem ser passados no formato numerico"""
    meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
             "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
    palav_chave = ['dia', 'mês', 'ano']
    d_ref = ['amanhã', 'hoje', 'ontem', 'anteontem']
    doc = remove_stopwords(doc, manter=meses + palav_chave + d_ref)
    matcher_mes = Matcher(nlp.vocab)
    pattern_meses = [{"ORTH": {"IN": meses}}]
    matcher_mes.add('MESES_PATTERN', None, pattern_meses)

    matcher_palav_chave = Matcher(nlp.vocab)
    matcher_palav_chave.add('PALAVRAS_PATTERN', None, [{"ORTH": {"IN": palav_chave}}])

    matcher_d_ref = Matcher(nlp.vocab)
    matcher_d_ref.add('HOJE_PATTERN', None, [{"ORTH": {"IN": d_ref}}])

    matches = {'mes': matcher_mes(doc),
               'd_ref': matcher_d_ref(doc),
               'palav_chave': matcher_palav_chave(doc)
               }

    if any(matches.values()):
        if matches['mes']:
            for match_id, start, end in matches['mes']:
                mes_nome = doc[start:end].orth_
                mes_num = meses.index(mes_nome) + 1
                index_mes = [p.orth_ for p in doc].index(mes_nome)
                dia = next(iter([int(p.orth_) for p in doc[index_mes].lefts if p.is_digit]), False)
                ano = next(iter([int(p.orth_) for p in doc[index_mes].rights if p.is_digit]), False)
                dt = date(ano if ano else date.today().year,
                          mes_num,
                          dia if dia else 1)
                return dt

        if matches['d_ref']:
            for match_id, start, end in matches['d_ref']:
                match = doc[start:end].orth_
                d_ref_num = d_ref.index(match)
                dt = date.today() - timedelta(days=d_ref_num - 1)
                return dt

        if matches['palav_chave']:
            dict_palav = {'dia': None, 'mês': None, 'ano': None}
            for match_id, start, end in matches['palav_chave']:
                index_palav = [p.orth_ for p in doc].index(doc[start:end].orth_)
                num = doc[index_palav].nbor().orth_ if doc[index_palav].nbor().is_digit else None
                dict_palav[doc[start:end].orth_] = int(num)
            dt = date(dict_palav['ano'] if dict_palav['ano'] else date.today().year,
                      dict_palav['mês'] if dict_palav['mês'] else date.today().month,
                      dict_palav['dia'] if dict_palav['dia'] else 1)
            return dt


##
Doc.set_extension("get_date", getter=date_getter, force=True)


##
def identifica_comando(frase):
    stemmer = RSLPStemmer()  # usado para pegar o radical da palavra
    doc = nlp(frase)
    dic_cmd = {}
    index_root = next(iter([palavra.i for palavra in doc if palavra.dep_ == 'ROOT']), False)

    if type(index_root) == int:
        # print('entrou')
        dic_cmd['acao'] = doc[index_root].orth_
        dic_cmd['acao_rad'] = stemmer.stem(dic_cmd['acao'])
        complemento = next(iter([palavra.orth_ for palavra in doc[index_root].rights]), False)
        if complemento:
            dic_cmd['complem'] = complemento
            dic_cmd['complem_rad'] = stemmer.stem(complemento)

    dt = doc._.get_date
    if type(dt) == date:
        dic_cmd['date'] = dt

    return dic_cmd
