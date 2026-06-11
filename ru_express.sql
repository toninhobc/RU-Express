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
    foto_perfil VARCHAR(255),
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
    comprovante_pdf VARCHAR(255) NOT NULL,
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

-- Mudança temporária no delimitador (boa prática).
-- Assim, o banco não confunde os pontos e vírgulas internos com o fim do comando.

DELIMITER //

CREATE TRIGGER trg_atualizar_saldo_apos_recarga
AFTER INSERT ON Recarga_Saldo
FOR EACH ROW
BEGIN
    -- 'NEW' vai acessar os dados da linha que acabou de ser inserida.
    UPDATE Usuario_RU
    SET saldo_atual = saldo_atual + NEW.valor_adicionado
    WHERE id_usuario = NEW.id_usuario;
END //

DELIMITER ;