import random
import os
import unicodedata
from datetime import datetime, timedelta

SQL_SEED_SCRIPT = os.path.join(os.path.dirname(__file__), "..", "seed.sql")

# BLOBs dummy (só o cabeçalho do arquivo) para os campos binários
FOTO_DUMMY = bytes.fromhex("89504E47")  # PNG
PDF_DUMMY = bytes.fromhex("25504446")  # "%PDF"

N_ESTUDANTES = 40
N_DOCENTES = 15
N_VISITANTES = 10
N_ACESSOS = 150
N_RECARGAS = 60
N_SORTEIOS = 6

CATRACAS_ATIVAS = [1, 2, 3, 5, 6, 7, 8, 9, 10, 11]
REFEITORIOS = list(range(1, 12))

PRIMEIROS_NOMES = [
    "Ana",
    "Bruno",
    "Carla",
    "Daniel",
    "Eduarda",
    "Felipe",
    "Gabriela",
    "Henrique",
    "Isabela",
    "João",
    "Karina",
    "Lucas",
    "Mariana",
    "Nicolas",
    "Otávio",
    "Paula",
    "Rafael",
    "Sofia",
    "Thiago",
    "Vitória",
    "Yasmin",
    "Antônio",
    "Beatriz",
    "Caio",
    "Débora",
    "Enzo",
    "Fernanda",
    "Gustavo",
    "Helena",
    "Igor",
]
SOBRENOMES = [
    "Silva",
    "Santos",
    "Oliveira",
    "Souza",
    "Rodrigues",
    "Ferreira",
    "Alves",
    "Pereira",
    "Lima",
    "Gomes",
    "Costa",
    "Ribeiro",
    "Martins",
    "Carvalho",
    "Almeida",
    "Lopes",
    "Soares",
    "Fernandes",
    "Vieira",
    "Barbosa",
    "Rocha",
    "Dias",
    "Nunes",
    "Mendes",
    "Moreira",
]
DEPARTAMENTOS = [
    "Ciência da Computação",
    "Matemática",
    "Física",
    "Engenharia",
    "Medicina",
    "Direito",
    "Economia",
    "Química",
    "Biologia",
    "História",
    "Letras",
    "Estatística",
]
MOTIVOS_VISITA = [
    "Palestra",
    "Reunião Administrativa",
    "Visita Guiada",
    "Manutenção Técnica",
    "Evento Científico",
    "Competição Esportiva",
    "Entrega de Documentos",
]
METODOS_PAGAMENTO = [
    "PIX",
    "Cartão de Crédito",
    "Cartão de Débito",
    "Boleto",
    "Dinheiro",
]
STATUS_DOC = ["Aprovado", "Em Análise", "Rejeitado"]
STATUS_BILHETE = ["Pendente", "Utilizado", "Expirado"]


def _nome():
    return f"{random.choice(PRIMEIROS_NOMES)} {random.choice(SOBRENOMES)}"


def _slug(nome):
    """Remove acentos e espaços para montar e-mails (ex.: 'João Silva' -> 'joao.silva')."""
    s = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return s.lower().replace(" ", ".")


def _horario_refeicao(dia, tipo):
    """Um datetime aleatório no horário da refeição (desjejum de manhã, refeição no almoço/jantar)."""
    if tipo == "Desjejum":
        hora = random.choice([7, 8, 9])
    else:
        hora = random.choice([11, 12, 13, 18, 19])
    return datetime(
        dia.year, dia.month, dia.day, hora, random.randint(0, 59), random.randint(0, 59)
    )


def _carregar_dados_fixos(cursor):
    with open(SQL_SEED_SCRIPT, encoding="utf-8") as f:
        cursor.execute(f.read())

    while cursor.nextset():
        pass


def _seed_estudantes(cursor, cat_map):
    ids = []
    for i in range(N_ESTUDANTES):
        nome = _nome()
        email = f"{_slug(nome)}.{i}@aluno.unb.br"
        categoria = random.choices([1, 2, 4], weights=[1, 4, 2])[0]
        saldo = round(random.uniform(0, 40), 2)
        prioridade = random.random() < 0.1

        cursor.execute(
            "INSERT INTO Usuario_RU (nome, email, saldo_atual, prioridade_legal, foto_perfil, id_categoria) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (nome, email, saldo, prioridade, FOTO_DUMMY, categoria),
        )
        uid = cursor.lastrowid

        matricula = 200000000 + i
        dias = random.randint(0, 15)
        cursor.execute(
            "INSERT INTO Estudante (matricula, dias_sem_fastpass, id_usuario) VALUES (%s, %s, %s)",
            (matricula, dias, uid),
        )
        cat_map[uid] = categoria
        ids.append(uid)
    return ids


def _seed_docentes(cursor, cat_map):
    ids = []
    for i in range(N_DOCENTES):
        nome = _nome()
        email = f"{_slug(nome)}.{i}@unb.br"
        saldo = round(random.uniform(0, 60), 2)

        cursor.execute(
            "INSERT INTO Usuario_RU (nome, email, saldo_atual, prioridade_legal, foto_perfil, id_categoria) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (nome, email, saldo, False, FOTO_DUMMY, 3),
        )
        uid = cursor.lastrowid

        siape = 1000000 + i
        cursor.execute(
            "INSERT INTO Servidor_Docente (siape, departamento, id_usuario) VALUES (%s, %s, %s)",
            (siape, random.choice(DEPARTAMENTOS), uid),
        )
        cat_map[uid] = 3
        ids.append(uid)
    return ids


def _seed_visitantes(cursor, cat_map):
    ids = []
    for i in range(N_VISITANTES):
        nome = _nome()
        email = f"{_slug(nome)}.{i}@email.com"
        saldo = round(random.uniform(0, 30), 2)

        cursor.execute(
            "INSERT INTO Usuario_RU (nome, email, saldo_atual, prioridade_legal, foto_perfil, id_categoria) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (nome, email, saldo, False, None, 3),
        )
        uid = cursor.lastrowid

        cursor.execute(
            "INSERT INTO Visitante (motivo_visita, id_usuario) VALUES (%s, %s)",
            (random.choice(MOTIVOS_VISITA), uid),
        )
        cat_map[uid] = 3
        ids.append(uid)
    return ids


def _seed_documentacao(cursor, estudante_ids):
    for uid in random.sample(estudante_ids, k=len(estudante_ids) // 3):
        data_envio = datetime(2026, random.randint(1, 6), random.randint(1, 28)).date()
        cursor.execute(
            "INSERT INTO Documentacao_Assistencia (data_envio, status_aprovacao, comprovante_pdf, id_usuario) "
            "VALUES (%s, %s, %s, %s)",
            (data_envio, random.choice(STATUS_DOC), PDF_DUMMY, uid),
        )


def _seed_recargas(cursor, todos_ids):
    for _ in range(N_RECARGAS):
        uid = random.choice(todos_ids)
        valor = round(random.uniform(5, 30), 2)
        data = datetime(
            2026, 6, random.randint(1, 30), random.randint(8, 20), random.randint(0, 59)
        )
        cursor.execute(
            "INSERT INTO Recarga_Saldo (valor_adicionado, data_hora_recarga, metodo_pagamento, id_usuario) "
            "VALUES (%s, %s, %s, %s)",
            (valor, data, random.choice(METODOS_PAGAMENTO), uid),
        )


def _seed_acessos(cursor, todos_ids, cat_map):
    hoje = datetime.now().date()

    cursor.execute(
        "SELECT id_categoria, valor_refeicao, valor_desjejum FROM Grupo_Acesso"
    )
    precos = {cat: (ref, des) for cat, ref, des in cursor.fetchall()}

    cursor.execute(
        "SELECT c.id_catraca FROM Catraca c "
        "JOIN Refeitorio r ON c.id_refeitorio = r.id_refeitorio "
        "WHERE r.tipo_servico = 'Executivo'"
    )
    catracas_executivas = {row[0] for row in cursor.fetchall()}

    inseridos = 0
    tentativas = 0
    while inseridos < N_ACESSOS and tentativas < N_ACESSOS * 5:
        tentativas += 1
        uid = random.choice(todos_ids)
        catraca = random.choice(CATRACAS_ATIVAS)

        tipo = "Desjejum" if random.random() < 0.2 else "Refeicao"

        if catraca in catracas_executivas:
            valor = round(random.uniform(5, 40), 2)
            peso = round(random.uniform(0.30, 1.20), 2)
        else:
            valor_ref, valor_des = precos[cat_map[uid]]
            valor = valor_des if tipo == "Desjejum" else valor_ref
            peso = None

        cursor.execute(
            "SELECT saldo_atual FROM Usuario_RU WHERE id_usuario = %s", (uid,)
        )
        saldo = cursor.fetchall()[0][0]
        if saldo < valor:
            continue

        # ~30% dos acessos são "de hoje" para o relatório de fluxo (CURDATE) mostrar dados
        if random.random() < 0.3:
            dia = hoje
        else:
            dia = hoje - timedelta(days=random.randint(1, 30))

        data_hora = _horario_refeicao(dia, tipo)

        if catraca in catracas_executivas:
            cursor.execute(
                "INSERT INTO Acesso_RU (data_hora_entrada, valor_cobrado, peso_prato_kg, id_usuario, id_catraca) "
                "VALUES (%s, %s, %s, %s, %s)",
                (data_hora, valor, peso, uid, catraca),
            )
        else:
            cursor.execute(
                "INSERT INTO Acesso_RU (data_hora_entrada, peso_prato_kg, id_usuario, id_catraca) "
                "VALUES (%s, %s, %s, %s)",
                (data_hora, peso, uid, catraca),
            )
        inseridos += 1


def _seed_sorteios_bilhetes(cursor, estudante_ids):
    for i in range(N_SORTEIOS):
        dia = datetime(2026, 6, 20) + timedelta(days=i)
        inicio = dia.replace(hour=11, minute=30)
        fim = dia.replace(hour=12, minute=30)
        vagas = random.choice([50, 60, 80, 100])

        cursor.execute(
            "INSERT INTO Sorteio_Diario (horario_inicio, horario_fim, quantidade_vagas) VALUES (%s, %s, %s)",
            (inicio, fim, vagas),
        )
        id_sorteio = cursor.lastrowid

        ganhadores = random.sample(
            estudante_ids, k=min(len(estudante_ids), random.randint(5, 15))
        )
        for uid in ganhadores:
            cursor.execute(
                "INSERT INTO Bilhete_FastPass "
                "(horario_inicio, horario_fim, status_uso, id_sorteio, id_usuario, id_refeitorio) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    inicio,
                    fim,
                    random.choice(STATUS_BILHETE),
                    id_sorteio,
                    uid,
                    random.choice(REFEITORIOS),
                ),
            )


def run_seed(conn):
    random.seed(42)
    cursor = conn.cursor()

    cat_map = {}

    _carregar_dados_fixos(cursor)

    estudante_ids = _seed_estudantes(cursor, cat_map)
    docente_ids = _seed_docentes(cursor, cat_map)
    visitante_ids = _seed_visitantes(cursor, cat_map)
    todos_ids = estudante_ids + docente_ids + visitante_ids

    _seed_documentacao(cursor, estudante_ids)
    _seed_recargas(cursor, todos_ids)
    _seed_acessos(cursor, todos_ids, cat_map)
    _seed_sorteios_bilhetes(cursor, estudante_ids)

    conn.commit()
    cursor.close()
    print(
        f"[seed] {len(todos_ids)} usuários inseridos "
        f"({len(estudante_ids)} estudantes, {len(docente_ids)} docentes, {len(visitante_ids)} visitantes)"
    )


if __name__ == "__main__":
    from db import make_connection, DB_NAME

    conn = make_connection()
    conn.database = DB_NAME
    try:
        run_seed(conn)
    finally:
        conn.close()
