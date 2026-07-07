-- =======================================================
-- DDL (DATA DEFINITION LANGUAGE) - ESTRUTURA DO BANCO
-- =======================================================

-- Tabelas independentes (PK)

CREATE TABLE IF NOT EXISTS Campus (
    id_campus INT AUTO_INCREMENT,
    nome_campus VARCHAR(100) NOT NULL,

    PRIMARY KEY (id_campus)
);

CREATE TABLE IF NOT EXISTS Grupo_Acesso (
    id_categoria INT AUTO_INCREMENT,
    nome_categoria VARCHAR(100) NOT NULL,
    valor_refeicao Decimal(5, 2) NOT NULL,
    valor_desjejum Decimal(5, 2) NOT NULL,

    PRIMARY KEY (id_categoria)
);

CREATE TABLE IF NOT EXISTS Sorteio_Diario (
    id_sorteio INT AUTO_INCREMENT,
    horario_inicio DATETIME NOT NULL,
    horario_fim DATETIME NOT NULL,
    quantidade_vagas INT NOT NULL,

    PRIMARY KEY (id_sorteio)
);


-- Tabelas dependentes (PK e FK)

CREATE TABLE IF NOT EXISTS Restaurante_Universitario (
    id_ru INT AUTO_INCREMENT,
    nome_ru VARCHAR(100) NOT NULL,
    id_campus INT NOT NULL,

    PRIMARY KEY (id_ru),
    FOREIGN KEY (id_campus) REFERENCES Campus(id_campus) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Refeitorio (
    id_refeitorio INT AUTO_INCREMENT,
    nome_refeitorio VARCHAR(100) NOT NULL,
    tipo_servico VARCHAR(100) NOT NULL,
    andar INT,
    id_ru INT NOT NULL,

    PRIMARY KEY (id_refeitorio),
    FOREIGN KEY (id_ru) REFERENCES Restaurante_Universitario(id_ru) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Catraca (
    id_catraca INT AUTO_INCREMENT,
    status_operacao VARCHAR(100) NOT NULL,
    id_refeitorio INT NOT NULL,

    PRIMARY KEY (id_catraca),
    FOREIGN KEY (id_refeitorio) REFERENCES Refeitorio(id_refeitorio) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Usuario_RU (
    id_usuario INT AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    saldo_atual Decimal(5, 2) NOT NULL CHECK (saldo_atual >= 0),
    prioridade_legal BOOLEAN NOT NULL,
    foto_perfil BLOB,
    id_categoria INT NOT NULL,

    PRIMARY KEY (id_usuario),
    FOREIGN KEY (id_categoria) REFERENCES Grupo_Acesso(id_categoria)
);

CREATE TABLE IF NOT EXISTS Estudante (
    matricula INT NOT NULL UNIQUE,
    dias_sem_fastpass INT NOT NULL,
    id_usuario INT NOT NULL,

    PRIMARY KEY (id_usuario),
    FOREIGN KEY (id_usuario) REFERENCES Usuario_RU(id_usuario) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Documentacao_Assistencia (
    id_documento INT AUTO_INCREMENT,
    data_envio DATE NOT NULL,
    status_aprovacao VARCHAR(100) NOT NULL,
    comprovante_pdf BLOB NOT NULL,
    id_usuario INT NOT NULL,

    PRIMARY KEY (id_documento),
    FOREIGN KEY (id_usuario) REFERENCES Estudante(id_usuario) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Servidor_Docente (
    siape INT NOT NULL UNIQUE,
    departamento VARCHAR(100) NOT NULL,
    id_usuario INT NOT NULL,

    PRIMARY KEY (id_usuario),
    FOREIGN KEY (id_usuario) REFERENCES Usuario_RU(id_usuario) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Visitante (
    motivo_visita VARCHAR(100),
    id_usuario INT NOT NULL,

    PRIMARY KEY (id_usuario),
    FOREIGN KEY (id_usuario) REFERENCES Usuario_RU(id_usuario) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Recarga_Saldo (
    id_recarga INT AUTO_INCREMENT,
    valor_adicionado Decimal(5, 2) NOT NULL,
    data_hora_recarga DATETIME NOT NULL,
    metodo_pagamento VARCHAR(100) NOT NULL,
    id_usuario INT NOT NULL,

    PRIMARY KEY (id_recarga),
    FOREIGN KEY (id_usuario) REFERENCES Usuario_RU(id_usuario)
);

CREATE TABLE IF NOT EXISTS Acesso_RU (
    id_acesso INT AUTO_INCREMENT,
    data_hora_entrada DATETIME NOT NULL,
    tipo_refeicao VARCHAR(20) NOT NULL,  -- derivado do horário pelo trigger trg_cobrar_acesso
    valor_cobrado Decimal(5, 2),
    peso_prato_kg Decimal(5, 2),
    id_usuario INT NOT NULL,
    id_catraca INT NOT NULL,

    PRIMARY KEY (id_acesso),
    FOREIGN KEY (id_usuario) REFERENCES Usuario_RU(id_usuario),
    FOREIGN KEY (id_catraca) REFERENCES Catraca(id_catraca)
);

CREATE TABLE IF NOT EXISTS Bilhete_FastPass (
    id_bilhete INT AUTO_INCREMENT,
    horario_inicio DATETIME NOT NULL,
    horario_fim DATETIME NOT NULL,
    status_uso VARCHAR(100) NOT NULL,
    id_sorteio INT NOT NULL,
    id_usuario INT NOT NULL,
    id_refeitorio INT NOT NULL,

    PRIMARY KEY (id_bilhete),
    FOREIGN KEY (id_sorteio) REFERENCES Sorteio_Diario(id_sorteio),
    FOREIGN KEY (id_usuario) REFERENCES Usuario_RU(id_usuario),
    FOREIGN KEY (id_refeitorio) REFERENCES Refeitorio(id_refeitorio)
);

-- =======================================================
-- TRIGGER: Atualiza saldo automaticamente após recarga
-- =======================================================

DELIMITER //

CREATE TRIGGER IF NOT EXISTS trg_atualizar_saldo_apos_recarga
AFTER INSERT ON Recarga_Saldo
FOR EACH ROW
BEGIN
    UPDATE Usuario_RU
    SET saldo_atual = saldo_atual + NEW.valor_adicionado
    WHERE id_usuario = NEW.id_usuario;
END //

DELIMITER ;

-- =======================================================
-- TRIGGER: Cobrança na catraca
-- Decide o tipo de refeição pelo horário
-- e o valor cobrado se não for RU executivo.
-- Esse valor já é debitado
-- =======================================================

DELIMITER //

CREATE TRIGGER IF NOT EXISTS trg_cobrar_acesso
BEFORE INSERT ON Acesso_RU
FOR EACH ROW
BEGIN
    DECLARE v_servico VARCHAR(100);

    SET NEW.tipo_refeicao = IF(HOUR(NEW.data_hora_entrada) < 10, 'Desjejum', 'Refeicao');

    SELECT r.tipo_servico
    INTO v_servico
    FROM Catraca c
    JOIN Refeitorio r ON c.id_refeitorio = r.id_refeitorio
    WHERE c.id_catraca = NEW.id_catraca;

    IF v_servico = 'Executivo' THEN
        IF NEW.valor_cobrado IS NULL THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'valor_cobrado é obrigatório em refeitório Executivo';
        END IF;
    ELSE
        SET NEW.valor_cobrado = (
            SELECT CASE
                       WHEN NEW.tipo_refeicao = 'Desjejum' THEN g.valor_desjejum
                       ELSE g.valor_refeicao
                   END
            FROM Usuario_RU u
            JOIN Grupo_Acesso g ON u.id_categoria = g.id_categoria
            WHERE u.id_usuario = NEW.id_usuario
        );
    END IF;

    UPDATE Usuario_RU
    SET saldo_atual = saldo_atual - NEW.valor_cobrado
    WHERE id_usuario = NEW.id_usuario;
END //

DELIMITER ;

-- =======================================================
-- PROCEDURE: Sorteio ponderado de FastPass por faixa
-- =======================================================

DELIMITER //

CREATE PROCEDURE IF NOT EXISTS Gerar_Sorteio_FastPass (
    IN p_horario_inicio DATETIME,
    IN p_horario_fim DATETIME,
    IN p_vagas INT,
    IN p_id_refeitorio INT
)
BEGIN   
    DECLARE v_id_sorteio INT;

    -- 1. Registrar o sorteio com a faixa de horário e seu limite próprio
    INSERT INTO Sorteio_Diario (horario_inicio, horario_fim, quantidade_vagas)
    VALUES (p_horario_inicio, p_horario_fim, p_vagas);

    SET v_id_sorteio = LAST_INSERT_ID();

    -- 2. Tabela temporária para os ganhadores
    CREATE TEMPORARY TABLE IF NOT EXISTS Temp_Ganhadores (
        id_usuario INT
    );

    TRUNCATE TABLE Temp_Ganhadores;

    -- 3. Sorteio ponderado: quanto mais dias sem FastPass, maior a chance
    INSERT INTO Temp_Ganhadores (id_usuario)
    SELECT id_usuario
    FROM Estudante
    ORDER BY POW(RAND(), 1.0 / (dias_sem_fastpass + 1)) DESC
    LIMIT p_vagas;

    -- 4. Emitir bilhetes com janela de horário
    INSERT INTO Bilhete_FastPass (horario_inicio, horario_fim, status_uso, id_sorteio, id_usuario, id_refeitorio)
    SELECT p_horario_inicio, p_horario_fim, 'Pendente', v_id_sorteio, id_usuario, p_id_refeitorio
    FROM Temp_Ganhadores;

    -- 5. Atualizar pesos
    UPDATE Estudante
    SET dias_sem_fastpass = dias_sem_fastpass + 1
    WHERE id_usuario NOT IN (SELECT id_usuario FROM Temp_Ganhadores);

    UPDATE Estudante
    SET dias_sem_fastpass = 0
    WHERE id_usuario IN (SELECT id_usuario FROM Temp_Ganhadores);

    -- 6. Limpar tabela temporária
    DROP TEMPORARY TABLE Temp_Ganhadores;

END //

DELIMITER ;

-- =======================================================
-- DQL (DATA QUERY LANGUAGE) - VIEW DE RELATÓRIO
-- =======================================================

-- View: fluxo de pessoas e faturamento por refeitório
CREATE OR REPLACE VIEW vw_relatorio_fluxo_ru AS
SELECT 
    r.nome_refeitorio, 
    r.tipo_servico, 
    COUNT(a.id_acesso) AS total_pessoas_atendidas, 
    SUM(a.valor_cobrado) AS faturamento_diario
FROM Refeitorio r
JOIN Catraca c ON r.id_refeitorio = c.id_refeitorio
JOIN Acesso_RU a ON c.id_catraca = a.id_catraca
WHERE DATE(a.data_hora_entrada) = CURDATE()
GROUP BY r.id_refeitorio, r.nome_refeitorio, r.tipo_servico;
