from datetime import datetime
import re
from sqlalchemy.orm import joinedload
from create_db import db, Text, Metadata, Morph, Theme, Community
from sqlalchemy.sql import exists
from sqlalchemy import func



def get_all_info(all_tokens, full_q_flag=False):
    """
    Форматирует результаты поиска для отображения в шаблоне.
    """
    out = []
    i = 0
    for token in all_tokens:
        message_info = []
        i += 1
        if full_q_flag:
            txt = token.text
            # print(txt)
            metadata = token.my_metadata  # Используем relationship
        else:
            # Получаем текст сообщения
            text_record = token.text  # Используем relationship
            if not text_record:
                continue
            txt = list(text_record.text)

            # Получаем метаданные
            metadata = token.text.my_metadata  # Используем relationship
        if metadata:
            src = metadata.source.source_name if metadata.source else 'Неизвестно'
            comm = metadata.community.community_name if metadata.community else 'Неизвестно'
            thm = metadata.theme.theme_name if metadata.theme else 'Неизвестно'
            dt = str(metadata.date).replace('T', ' ') if metadata.date else 'Неизвестно'
            if not full_q_flag:
                # Формируем грамматическую информацию о слове
                wordinf = f'Tокен: {token.token}<br>Лемма: {token.lemma}<br>Часть речи: {token.upos}'
                if token.feats:
                    wordinf += f'<br><span>Другие признаки: {token.feats.replace("|", ", ")}</span>'

                # Вставляем HTML-теги для выделения найденного слова
                if token.start_char is not None and token.end_char is not None:
                    txt.insert(token.start_char, '<span class="found-word"><b class="target">')
                    txt.insert(token.end_char + 1, f'</b><span class="description">{wordinf}</span></span>')

                beautiful_text = ''.join(txt)

            else:
                beautiful_text = txt
                wordinf = ''

            message_info.extend([
                str(i) + '.',  # Номер по пороядку вывода
                beautiful_text,  # Текст сообщения с выделенным словом
                src,  # Источник
                comm,  # Сообщество
                thm,  # Тема
                dt,  # Время
                wordinf  # Грамматическая информация о слове
            ])
            out.append(message_info)
    return out


# Обновленные функции поиска с использованием paginate

def exact_search(query, register):
    print(f"Received query: {query}, register == None: {register is None}")
    if not register:
        print('Executing case-insensitive search')
        # query = query.lower()
        # print(func.lower(query))
        pagination_query = Morph.query.options(
            joinedload(Morph.text).joinedload(Text.my_metadata)
        ).filter(func.lower(Morph.token) == query.lower())
    else:
        print('Executing case-sensitive search')
        pagination_query = Morph.query.options(
            joinedload(Morph.text).joinedload(Text.my_metadata)
        ).filter(Morph.token == query)

    return pagination_query


def lemma_search(query):
    pagination_query = Morph.query.options(
        joinedload(Morph.text).joinedload(Text.my_metadata)
    ).filter(Morph.lemma == query)
    return pagination_query


def pos_search(query):
    pagination_query = Morph.query.options(
        joinedload(Morph.text).joinedload(Text.my_metadata)
    ).filter(Morph.upos == query)
    return pagination_query


def exact_pos_search(from_q, pos_q):
    pos_q = pos_q.upper()
    pagination_query = Morph.query.options(
        joinedload(Morph.text).joinedload(Text.my_metadata)
    ).filter(Morph.token == from_q, Morph.upos == pos_q)
    return pagination_query


def lemma_exact_search(lemma_q, form_q):
    pagination_query = Morph.query.options(
        joinedload(Morph.text).joinedload(Text.my_metadata)
    ).filter(Morph.lemma == lemma_q, Morph.token == form_q)
    return pagination_query


def lemma_pos_search(lemma_q, pos_q):
    pos_q = pos_q.upper()
    pagination_query = Morph.query.options(
        joinedload(Morph.text).joinedload(Text.my_metadata)
    ).filter(Morph.lemma == lemma_q, Morph.upos == pos_q)
    return pagination_query


def triple_search(lemma_q, form_q, pos_q):
    pos_q = pos_q.upper()
    pagination_query = Morph.query.options(
        joinedload(Morph.text).joinedload(Text.my_metadata)
    ).filter(Morph.lemma == lemma_q, Morph.upos == pos_q, Morph.token == form_q)
    return pagination_query


def thema_search(pagination_query, theme_names):
    # Получаем идентификаторы тем на основе их названий
    theme_ids = db.session.query(Theme.theme_id).filter(Theme.theme_name.in_(theme_names)).all()

    # Преобразуем результат в список
    theme_ids = [theme_id[0] for theme_id in theme_ids]
    print(theme_ids)
    # Применяем фильтр по найденным идентификаторам тем
    pagination_query = pagination_query.filter(
        exists().where(
            (Metadata.message_id_meta == Morph.message_id_word) &
            (Metadata.theme_id_meta.in_(theme_ids))
        )
    )

    return pagination_query


def community_search(pagination_query, comm_q):
    # Получаем идентификаторы тем на основе их названий
    comm_ids = db.session.query(Community.community_id).filter(Community.community_name.in_(comm_q)).all()
    # Преобразуем результат в список
    comm_ids = [comm_id[0] for comm_id in comm_ids]
    print('айди сообществ', comm_ids)
    pagination_query = pagination_query.filter(
        exists().where(
            (Metadata.message_id_meta == Morph.message_id_word) &
            (Metadata.community_id_meta.in_(comm_ids))
        )
    )
    return pagination_query


def data_search(pagination_query, after_datetime_q=None, before_datetime_q=None):
    if after_datetime_q and before_datetime_q:
        after_datetime_q = datetime.strptime(after_datetime_q, '%Y-%m-%dT%H:%M')
        before_datetime_q = datetime.strptime(before_datetime_q, '%Y-%m-%dT%H:%M')
        pagination_query = pagination_query.filter(
            exists().where(
                (Metadata.message_id_meta == Morph.message_id_word) &
                (Metadata.date > after_datetime_q) & (Metadata.date < before_datetime_q)
            )
        )
    elif after_datetime_q:
        after_datetime_q = datetime.strptime(after_datetime_q, '%Y-%m-%dT%H:%M')
        pagination_query = pagination_query.filter(
            exists().where(
                (Metadata.message_id_meta == Morph.message_id_word) &
                (Metadata.date> after_datetime_q)
            )
        )
    elif before_datetime_q:
        before_datetime_q = datetime.strptime(before_datetime_q, '%Y-%m-%dT%H:%M')
        pagination_query = pagination_query.filter(
            exists().where(
                (Metadata.message_id_meta == Morph.message_id_word) &
                (Metadata.date < before_datetime_q)
            )
        )
    return pagination_query


def full_text_search(query):
    """
    Выполняет полнотекстовый поиск, возвращая только те тексты, которые совпадают с запросом полностью.
    """
    print('Выполняется полнотектосвый поиск')
    # Приводим query к нижнему регистру, чтобы сделать поиск регистронезависимым
    query_lower = query.lower()

    pagination_query = Text.query.filter(
        func.lower(Text.text) == query
    )

    return pagination_query


def query_type(lemma_q, form_q, pos_q):
    # emoji_re = re.compile(
    #     r"[\U0001F600-\U0001F64F]"  # Emoticons
    #     r"|[\U0001F300-\U0001F5FF]"  # Symbols & Pictographs
    #     r"|[\U0001F680-\U0001F6FF]"  # Transport & Map Symbols
    #     r"|[\U0001F700-\U0001F77F]"  # Alchemical Symbols
    #     r"|[\U0001F780-\U0001F7FF]"  # Geometric Shapes Extended
    #     r"|[\U0001F800-\U0001F8FF]"  # Supplemental Arrows-C
    #     r"|[\U0001F900-\U0001F9FF]"  # Supplemental Symbols & Pictographs
    #     r"|[\U0001FA00-\U0001FA6F]"  # Chess Symbols
    #     r"|[\U0001FA70-\U0001FAFF]"  # Symbols and Pictographs Extended-A
    #     r"|[а-яёА-ЯЁ]+"  # Russian words
    #     r"|[a-zA-Z]+"  # English words
    # )
    pattern_word = re.compile(r'^[а-яёА-ЯЁ]+$')
    pattern_pos = re.compile(r'^[a-zA-Z]+$')
    if lemma_q and form_q and pos_q:
        if pattern_word.match(lemma_q) and pattern_word.match(form_q) and pattern_pos.match(pos_q):
            return 'triple'
    if lemma_q and form_q:
        if pattern_word.match(lemma_q) and pattern_word.match(form_q):
            return 'lemma+form'
    if lemma_q and pos_q:
        if pattern_word.match(lemma_q) and pattern_pos.match(pos_q):
            return 'lemma+pos'
    if form_q and pos_q:
        if pattern_pos.match(pos_q) and pattern_word.match(form_q):
            return 'form+pos'
    if lemma_q:
        if pattern_word.match(lemma_q):
            return 'lemma'
    if form_q:
        if pattern_word.match(form_q):
            return 'form'
    if pos_q:
        if pattern_pos.match(pos_q):
            return 'pos'
    return 'Неверный запрос'


def total_search(page, per_page,
                 lemma_q=None,
                 form_q=None,
                 pos_q=None,
                 theme_ids=None,
                 comm_q=None,
                 after_datetime_q=None,
                 before_datetime_q=None,
                 register=None,
                 remove_duplicates=None,
                 full_q=None):
    """
    Выбирает подходящую функцию поиска в зависимости от типа запроса
    """
    if full_q:
        print(full_q)
        full_q_flag = True
        pagination_query = full_text_search(full_q)
    else:
        full_q_flag = False
        q_type = query_type(lemma_q, form_q, pos_q)

        if q_type == 'form':
            pagination_query = exact_search(form_q, register)
        elif q_type == 'lemma':
            pagination_query = lemma_search(lemma_q)
        elif q_type == 'pos':
            pagination_query = pos_search(pos_q)
        elif q_type == 'form+pos':
            pagination_query = exact_pos_search(form_q, pos_q)
        elif q_type == 'lemma+pos':
            pagination_query = lemma_pos_search(lemma_q, pos_q)
        elif q_type == 'lemma+form':
            pagination_query = lemma_exact_search(lemma_q, form_q)
        elif q_type == 'triple':
            pagination_query = triple_search(lemma_q, form_q, pos_q)
        else:
            return [['', 'Неверный запрос']], 0

    # Поиск по метаинформации
    # фильтр по нескольким темам, если передан список theme_ids
    if theme_ids:
        pagination_query = thema_search(pagination_query, theme_ids)

    if comm_q:
        if comm_q[0]:
            pagination_query = community_search(pagination_query, comm_q)

    # филтр по дате, если указана дата до или после которой должно быть сообщение
    if after_datetime_q or before_datetime_q:
        pagination_query = data_search(pagination_query, after_datetime_q, before_datetime_q)

    # убираем дубликаты на уровне идентификаторв
    # pagination_query = pagination_query.join(Text, Morph.text).group_by(Text.message_id)
    # опционально убираем дубликаты на уровне текста
    if remove_duplicates:
        pagination_query = pagination_query.join(Text, Morph.text).group_by(Text.text) #проверить что не убирает лишние


    # Пагинация
    pagination = pagination_query.paginate(page=page, per_page=per_page, error_out=False)
    # Получаем результат
    all_tokens = pagination.items
    data = get_all_info(all_tokens, full_q_flag)

    return data, pagination.total
