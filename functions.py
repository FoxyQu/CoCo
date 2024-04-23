# from nltk.tokenize import word_tokenize
import re
from create_db import db, Text, Metadata, Morph

def query_type(search_text):
    # отдельно храним паттерн и тип паттерна
    queries = []
    types = []
    tokens = search_text.split() # в идеале сделать NLTK
    # регулярки для определения типа паттерна
    if tokens:
        for token in tokens:
            queries.append(token)
            if re.match(r'"[а-яёА-ЯЁ]+"$', token):
                types.append('exact')
            elif re.match(r'[а-яёА-ЯЁ]+$', token):
                types.append('lemma')
            elif re.match(r'[a-zA-Z]+$', token):
                types.append('pos')
            elif re.match(r'"[а-яёА-ЯЁ]+"\+[a-zA-Z]+$', token):
                types.append('exact+pos')
            else:
                return ('Неверный запрос', '')
        return(queries, types)
    else:
        return ('Неверный запрос', '')

def get_all_info(all_tokens):
    out = []
    all_messages = []
    idxs = []
    wordinfs = []
    for token in all_tokens:
        all_messages.append(token.message_id_word)
        idxs.append((token.start_char, token.end_char))
        wordinf = ''
        wordinf += 'Токен: ' + token.token + '<br>'
        wordinf += 'Лемма: ' + token.lemma + '<br>'
        wordinf += 'Часть речи: ' + token.upos + '<br>'
        if token.feats:
            wordinf += 'Другие признаки: ' + token.feats.replace('|', ', ') + '<br>'
        else:
            print(token.lemma)
            print(db.session.query(Text).filter(Text.message_id == token.message_id_word).all()[0].text)
            wordinf += 'Другие признаки: ' + str(token.feats)
        wordinfs.append(wordinf)

    for i, m in enumerate(all_messages):
        message_info = [str(i + 1)+'.']
        txt = list(db.session.query(Text).filter(Text.message_id == m).all()[0].text)
        txt.insert(idxs[i][1], f'</b> <span class="description">{wordinfs[i]}</span>')
        txt.insert(idxs[i][0], '<b class="target">')
        beautiful_text = ''.join(txt)
        src = db.session.query(Metadata).filter(Metadata.message_id_meta == m).all()[0].source.source_name
        comm = db.session.query(Metadata).filter(Metadata.message_id_meta == m).all()[0].community.community_name
        thm = db.session.query(Metadata).filter(Metadata.message_id_meta == m).all()[0].theme.theme_name
        dt = db.session.query(Metadata).filter(Metadata.message_id_meta == m).all()[0].date
        beautiful_dt = ' '.join(dt.split('T'))
        message_info.extend([beautiful_text, src, comm, thm, beautiful_dt, wordinfs[i]])
        out.append(message_info)
    out.append(len(out))
    if out:
        return out
    else:
        return [['', 'Ничего не нашлось :('], 0]

def exact_search(query):
    form = query.strip('"')
    all_tokens = db.session.query(Morph).filter(Morph.token == form).all()
    return get_all_info(all_tokens)

def lemma_search(query):
    all_tokens = db.session.query(Morph).filter(Morph.lemma == query).all()
    return get_all_info(all_tokens)

def pos_search(query):
    all_tokens = db.session.query(Morph).filter(Morph.upos == query).all()
    return get_all_info(all_tokens)

def exact_pos_search(query):
    form, pos = query.split('+')
    form = form.strip('"')
    pos = pos.upper()
    all_tokens = db.session.query(Morph).filter(Morph.token == form).filter(Morph.upos == pos).all()
    return get_all_info(all_tokens)

def total_search(search_text):
    search_text = search_text.lower()
    queries, types = query_type(search_text)

    if type(queries) == str:
        return [['', queries], 0]

    if len(queries) > 1:
        return [['','Введите одно слово. Функция посика по n-граммам будет реализована позже'], 0]

    if types[0] == 'exact':
        return exact_search(queries[0])
    if types[0] == 'lemma':
        return lemma_search(queries[0])
    if types[0] == 'pos':
        return pos_search(queries[0])
    if types[0] == 'exact+pos':
        return exact_pos_search(queries[0])

