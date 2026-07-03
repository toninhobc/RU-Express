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