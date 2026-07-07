"""SQL queries for the catraca client."""

QueryUserInfo = """
    SELECT u.nome, u.saldo_atual, g.nome_categoria
    FROM Usuario_RU u
    JOIN Grupo_Acesso g ON u.id_categoria = g.id_categoria
    WHERE u.id_usuario = %s
"""

QueryCatracaInfo = """
    SELECT c.id_catraca, r.nome_refeitorio, ru.nome_ru, r.id_refeitorio
    FROM Catraca c
    JOIN Refeitorio r ON c.id_refeitorio = r.id_refeitorio
    JOIN Restaurante_Universitario ru ON r.id_ru = ru.id_ru
    WHERE c.id_catraca = %s
"""

QueryFastPassValido = """
    SELECT id_bilhete, horario_inicio, horario_fim
    FROM Bilhete_FastPass
    WHERE id_usuario = %s
      AND status_uso = 'Pendente'
      AND id_refeitorio = %s
      AND %s BETWEEN horario_inicio AND horario_fim
    LIMIT 1
"""
