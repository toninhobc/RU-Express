-- =======================================================
-- DDL (DATA DEFINITION LANGUAGE) - ESTRUTURA DO BANCO
-- =======================================================

-- Tabelas independentes (PK)

CREATE TABLE Campus (
    id_campus INT AUTO_INCREMENT,
    nome_campus VARCHAR(100) NOT NULL,

    PRIMARY KEY (id_campus)
);

CREATE TABLE Grupo_Acesso (
    id_categoria INT AUTO_INCREMENT,
    nome_categoria VARCHAR(100) NOT NULL,
    valor_refeicao FLOAT NOT NULL,
    valor_desjejum FLOAT NOT NULL,

    PRIMARY KEY (id_categoria)
);

CREATE TABLE Sorteio_Diario (
    id_sorteio INT AUTO_INCREMENT,
    data_sorteio DATE NOT NULL,
    quantidade_vagas INT NOT NULL,

    PRIMARY KEY (id_sorteio)
);


-- Tabelas dependentes (PK e FK)

CREATE TABLE Restaurante_Universitario (
    id_ru INT AUTO_INCREMENT,
    nome_ru VARCHAR(100) NOT NULL,
    id_campus INT NOT NULL,

    PRIMARY KEY (id_ru),
    FOREIGN KEY (id_campus) REFERENCES Campus(id_campus)
);

CREATE TABLE Refeitorio (
    id_refeitorio INT AUTO_INCREMENT,
    nome_refeitorio VARCHAR(100) NOT NULL,
    tipo_servico VARCHAR(100) NOT NULL,
    andar INT,
    id_ru INT NOT NULL,

    PRIMARY KEY (id_refeitorio),
    FOREIGN KEY (id_ru) REFERENCES Restaurante_Universitario(id_ru)
);

CREATE TABLE Catraca (
    id_catraca INT AUTO_INCREMENT,
    status_operacao VARCHAR(100) NOT NULL,
    id_refeitorio INT NOT NULL,

    PRIMARY KEY (id_catraca),
    FOREIGN KEY (id_refeitorio) REFERENCES Refeitorio(id_refeitorio)
);

CREATE TABLE Usuario_RU (
    id_usuario INT AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    saldo_atual FLOAT NOT NULL,
    prioridade_legal BOOLEAN NOT NULL,
    foto_perfil BLOB,
    id_categoria INT NOT NULL,

    PRIMARY KEY (id_usuario),
    FOREIGN KEY (id_categoria) REFERENCES Grupo_Acesso(id_categoria)
);

CREATE TABLE Estudante (
    matricula INT NOT NULL,
    dias_sem_fastpass INT NOT NULL,
    id_usuario INT NOT NULL,

    PRIMARY KEY (id_usuario),
    FOREIGN KEY (id_usuario) REFERENCES Usuario_RU(id_usuario)
);

CREATE TABLE Documentacao_Assistencia (
    id_documento INT AUTO_INCREMENT,
    data_envio DATE NOT NULL,
    status_aprovacao VARCHAR(100) NOT NULL,
    comprovante_pdf BLOB NOT NULL,
    id_usuario INT NOT NULL,

    PRIMARY KEY (id_documento),
    FOREIGN KEY (id_usuario) REFERENCES Estudante(id_usuario)
);

CREATE TABLE Servidor_Docente (
    siape INT NOT NULL,
    departamento VARCHAR(100) NOT NULL,
    id_usuario INT NOT NULL,

    PRIMARY KEY (id_usuario),
    FOREIGN KEY (id_usuario) REFERENCES Usuario_RU(id_usuario)
);

CREATE TABLE Visitante (
    motivo_visita VARCHAR(100),
    id_usuario INT NOT NULL,

    PRIMARY KEY (id_usuario),
    FOREIGN KEY (id_usuario) REFERENCES Usuario_RU(id_usuario)
);

CREATE TABLE Recarga_Saldo (
    id_recarga INT AUTO_INCREMENT,
    valor_adicionado FLOAT NOT NULL,
    data_hora_recarga DATETIME NOT NULL,
    metodo_pagamento VARCHAR(100) NOT NULL,
    id_usuario INT NOT NULL,

    PRIMARY KEY (id_recarga),
    FOREIGN KEY (id_usuario) REFERENCES Usuario_RU(id_usuario)
);

CREATE TABLE Acesso_RU (
    id_acesso INT AUTO_INCREMENT,
    data_hora_entrada DATETIME NOT NULL,
    valor_cobrado FLOAT,
    peso_prato_kg FLOAT,
    id_usuario INT NOT NULL,
    id_catraca INT NOT NULL,

    PRIMARY KEY (id_acesso),
    FOREIGN KEY (id_usuario) REFERENCES Usuario_RU(id_usuario),
    FOREIGN KEY (id_catraca) REFERENCES Catraca(id_catraca)
);

CREATE TABLE Bilhete_FastPass (
    id_bilhete INT AUTO_INCREMENT,
    data_validade DATE NOT NULL,
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

CREATE TRIGGER trg_atualizar_saldo_apos_recarga
AFTER INSERT ON Recarga_Saldo
FOR EACH ROW
BEGIN
    UPDATE Usuario_RU
    SET saldo_atual = saldo_atual + NEW.valor_adicionado
    WHERE id_usuario = NEW.id_usuario;
END //

DELIMITER ;

-- =======================================================
-- PROCEDURE: Sorteio ponderado de FastPass
-- =======================================================

DELIMITER //

CREATE PROCEDURE Gerar_Sorteio_FastPass (
    IN p_data DATE,
    IN p_vagas INT,
    IN p_id_refeitorio INT
)
BEGIN   
    DECLARE v_id_sorteio INT;

    -- 1. Registrar o sorteio
    INSERT INTO Sorteio_Diario (data_sorteio, quantidade_vagas)
    VALUES (p_data, p_vagas);

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

    -- 4. Emitir bilhetes
    INSERT INTO Bilhete_FastPass (data_validade, status_uso, id_sorteio, id_usuario, id_refeitorio)
    SELECT p_data, 'Pendente', v_id_sorteio, id_usuario, p_id_refeitorio
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
-- DML (DATA MANIPULATION LANGUAGE) - POVOAMENTO
-- =======================================================

-- 1. Inserindo Campi
INSERT INTO Campus (nome_campus) VALUES 
('Darcy Ribeiro'),
('FGA - Gama'),
('FCE - Ceilândia'),
('FUP - Planaltina'),
('FAL - Fazenda Água Limpa');

-- 2. Inserindo Grupos de Acesso
INSERT INTO Grupo_Acesso (nome_categoria, valor_refeicao, valor_desjejum) VALUES 
('Estudante Padrão', 2.50, 1.00),
('Estudante Isento (100%)', 0.00, 0.00),
('Servidor/Docente', 15.00, 7.00),
('Visitante Sem Vínculo', 20.00, 10.00),
('Pós-Graduação', 2.50, 1.00);

-- 3. Inserindo Sorteios Diários
INSERT INTO Sorteio_Diario (data_sorteio, quantidade_vagas) VALUES 
('2026-06-25', 50),
('2026-06-26', 60),
('2026-06-27', 50),
('2026-06-28', 100),
('2026-06-29', 50);

-- 4. Inserindo Restaurantes Universitários
INSERT INTO Restaurante_Universitario (nome_ru, id_campus) VALUES 
('RU Central Darcy', 1),
('RU Setor Norte', 1),
('RU Gama', 2),
('RU Ceilândia', 3),
('RU Planaltina', 4);

-- 5. Inserindo Refeitórios (andar NULL para salões únicos)
INSERT INTO Refeitorio (nome_refeitorio, tipo_servico, andar, id_ru) VALUES 
('Salão Térreo Principal', 'Padrão', 0, 1),
('Salão Superior', 'Padrão', 1, 1),
('Restaurante Executivo', 'Executivo', 2, 1),
('Salão Único FGA', 'Padrão', NULL, 3),
('Salão Único FCE', 'Padrão', NULL, 4);

-- 6. Inserindo Catracas
INSERT INTO Catraca (status_operacao, id_refeitorio) VALUES 
('Ativa', 1),
('Ativa', 2),
('Ativa', 3),
('Em Manutenção', 4),
('Ativa', 5);

-- 7. Inserindo Usuários RU (15 registros: 5 de cada tipo)
-- 0x89504E47 = PNG dummy para foto_perfil
INSERT INTO Usuario_RU (nome, email, saldo_atual, prioridade_legal, foto_perfil, id_categoria) VALUES 
-- IDs 1-5: Estudantes
('Antonio Coelho', 'antonio@aluno.unb.br', 50.00, FALSE, 0x89504E47, 1),
('Yasmin', 'yasmin@aluno.unb.br', 12.50, FALSE, 0x89504E47, 1),
('Vitor', 'vitor@aluno.unb.br', 0.00, TRUE, 0x89504E47, 2),
('Rafael', 'rafael@aluno.unb.br', 25.00, FALSE, 0x89504E47, 1),
('Felipe', 'felipe@aluno.unb.br', 5.00, FALSE, 0x89504E47, 1),
-- IDs 6-10: Servidores
('Prof. Silva', 'silva@unb.br', 150.00, FALSE, 0x89504E47, 3),
('Prof. Costa', 'costa@unb.br', 45.00, FALSE, 0x89504E47, 3),
('Tec. Santos', 'santos@unb.br', 90.00, FALSE, 0x89504E47, 3),
('Prof. Oliveira', 'oliveira@unb.br', 30.00, FALSE, 0x89504E47, 3),
('Tec. Souza', 'souza@unb.br', 15.00, FALSE, 0x89504E47, 3),
-- IDs 11-15: Visitantes
('Carlos Mendes', 'carlos@email.com', 40.00, FALSE, NULL, 4),
('Marcos Rocha', 'marcos@email.com', 20.00, FALSE, NULL, 4),
('Julia Lima', 'julia@email.com', 0.00, FALSE, NULL, 4),
('Fernanda Alves', 'fernanda@email.com', 60.00, FALSE, NULL, 4),
('Roberto Nunes', 'roberto@email.com', 20.00, TRUE, NULL, 4);

-- 8. Inserindo Estudantes (FK para IDs 1-5)
INSERT INTO Estudante (matricula, dias_sem_fastpass, id_usuario) VALUES 
(221000001, 5, 1),
(231000002, 2, 2),
(211000003, 10, 3),
(241000004, 0, 4),
(221000005, 3, 5);

-- 9. Inserindo Servidores (FK para IDs 6-10)
INSERT INTO Servidor_Docente (siape, departamento, id_usuario) VALUES 
(1122334, 'Ciência da Computação', 6),
(2233445, 'Matemática', 7),
(3344556, 'Engenharia', 8),
(4455667, 'Física', 9),
(5566778, 'Medicina', 10);

-- 10. Inserindo Visitantes (FK para IDs 11-15)
INSERT INTO Visitante (motivo_visita, id_usuario) VALUES 
('Palestra Sinapses Abertas', 11),
('Competição II Maratona do Cerrado', 12),
('Reunião Administrativa', 13),
('Visita Guiada', 14),
('Manutenção Técnica', 15);

-- 11. Inserindo Documentação (0x25504446 = "%PDF" dummy)
INSERT INTO Documentacao_Assistencia (data_envio, status_aprovacao, comprovante_pdf, id_usuario) VALUES 
('2026-01-10', 'Aprovado', 0x25504446, 3),
('2026-03-15', 'Em Análise', 0x25504446, 2),
('2026-02-20', 'Aprovado', 0x25504446, 1),
('2026-04-05', 'Rejeitado', 0x25504446, 4),
('2026-05-12', 'Em Análise', 0x25504446, 5);

-- 12. Inserindo Recargas de Saldo
INSERT INTO Recarga_Saldo (valor_adicionado, data_hora_recarga, metodo_pagamento, id_usuario) VALUES 
(50.00, '2026-06-20 10:00:00', 'PIX', 1),
(15.00, '2026-06-21 14:30:00', 'Cartão de Crédito', 6),
(20.00, '2026-06-22 09:15:00', 'PIX', 11),
(12.50, '2026-06-23 11:45:00', 'Boleto', 2),
(30.00, '2026-06-24 16:20:00', 'PIX', 8);

-- 13. Inserindo Acessos no RU
INSERT INTO Acesso_RU (data_hora_entrada, valor_cobrado, peso_prato_kg, id_usuario, id_catraca) VALUES 
('2026-06-25 11:30:00', 2.50, NULL, 1, 1),
('2026-06-25 12:00:00', 0.00, NULL, 3, 2),
('2026-06-25 12:15:00', 15.00, 0.850, 6, 3),
('2026-06-25 12:30:00', 20.00, NULL, 11, 5),
('2026-06-25 12:45:00', 2.50, NULL, 2, 1);

-- 14. Inserindo Bilhetes FastPass
INSERT INTO Bilhete_FastPass (data_validade, status_uso, id_sorteio, id_usuario, id_refeitorio) VALUES 
('2026-06-25', 'Utilizado', 1, 1, 1),
('2026-06-26', 'Pendente', 2, 3, 2),
('2026-06-26', 'Pendente', 2, 2, 1),
('2026-06-27', 'Expirado', 3, 5, 4),
('2026-06-28', 'Pendente', 4, 4, 1);

-- =======================================================
-- DQL (DATA QUERY LANGUAGE) - VIEW DE RELATÓRIO
-- =======================================================

-- View: fluxo de pessoas e faturamento por refeitório
CREATE VIEW vw_relatorio_fluxo_ru AS
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