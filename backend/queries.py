QueryUser = """
        SELECT 
            u.id_usuario, 
            u.nome, 
            u.email, 
            u.saldo_atual, 
            u.prioridade_legal, 
            g.nome_categoria AS categoria, 
            g.valor_refeicao, 
            g.valor_desjejum,
            e.matricula, 
            e.dias_sem_fastpass,
            s.siape, 
            s.departamento,
            v.motivo_visita
        FROM Usuario_RU u
        INNER JOIN Grupo_Acesso g ON u.id_categoria = g.id_categoria
        LEFT JOIN Estudante e ON u.id_usuario = e.id_usuario
        LEFT JOIN Servidor_Docente s ON u.id_usuario = s.id_usuario
        LEFT JOIN Visitante v ON u.id_usuario = v.id_usuario
        WHERE u.id_usuario = %s;
        """

QueryBalance = """
        SELECT
            u.id_usuario,
            u.nome,
            u.saldo_atual,
            g.nome_categoria AS categoria
        FROM Usuario_RU u
        INNER JOIN Grupo_Acesso g
            ON u.id_categoria = g.id_categoria
        WHERE u.id_usuario = %s;
        """

QueryAcessos = """
        SELECT
            a.id_acesso,
            a.data_hora_entrada,
            a.tipo_refeicao,
            a.valor_cobrado,
            a.peso_prato_kg,
            c.id_catraca,
            r.nome_refeitorio,
            r.tipo_servico,
            ru.nome_ru AS restaurante
        FROM Acesso_RU a
        INNER JOIN Catraca c ON a.id_catraca = c.id_catraca
        INNER JOIN Refeitorio r ON c.id_refeitorio = r.id_refeitorio
        INNER JOIN Restaurante_Universitario ru ON r.id_ru = ru.id_ru
        WHERE a.id_usuario = %s
        ORDER BY a.data_hora_entrada DESC

        LIMIT %s OFFSET %s;
        """

QueryAdminUsuariosBase = """
    SELECT
        id_usuario,
        nome,
        email,
        saldo_atual,
        prioridade_legal,
        id_categoria
    FROM Usuario_RU
    WHERE 1=1
"""

QueryBilheteBase = """
    SELECT 
        b.id_bilhete,
        b.horario_inicio,
        b.horario_fim,
        b.status_uso,
        r.nome_refeitorio,
        ru.nome_ru AS restaurante,
        s.id_sorteio
    FROM Bilhete_FastPass b
    INNER JOIN Refeitorio r ON b.id_refeitorio = r.id_refeitorio
    INNER JOIN Restaurante_Universitario ru ON r.id_ru = ru.id_ru
    INNER JOIN Sorteio_Diario s ON b.id_sorteio = s.id_sorteio
    WHERE b.id_usuario = %s
"""
QueryRelatorioFluxo = """
    SELECT
        *
    FROM vw_relatorio_fluxo_ru;
"""

QueryRefeitorios = """
    SELECT r.id_refeitorio, r.nome_refeitorio, r.tipo_servico, ru.nome_ru
    FROM Refeitorio r
    JOIN Restaurante_Universitario ru ON r.id_ru = ru.id_ru
    ORDER BY ru.nome_ru, r.nome_refeitorio
"""

QueryRechargeInsert = """
    INSERT INTO Recarga_Saldo (valor_adicionado, data_hora_recarga, metodo_pagamento, id_usuario)
    VALUES (%s, %s, %s, %s)
"""

QuerySaldoAfterRecharge = """
    SELECT saldo_atual FROM Usuario_RU WHERE id_usuario = %s
"""

QueryUsuarioInsert = """
    INSERT INTO Usuario_RU (nome, email, saldo_atual, prioridade_legal, foto_perfil, id_categoria)
    VALUES (%s, %s, 0, %s, NULL, %s)
"""

QueryUsuarioExists = """
    SELECT 1 FROM Usuario_RU WHERE id_usuario = %s
"""

QueryUsuarioDelete = """
    DELETE FROM Usuario_RU WHERE id_usuario = %s
"""
