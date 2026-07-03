-- =======================================================
-- DML (DATA MANIPULATION LANGUAGE) - POVOAMENTO
-- =======================================================

-- 1. Inserindo Campi
INSERT INTO Campus (id_campus, nome_campus) VALUES 
(1, 'Darcy Ribeiro'),
(2, 'FGA - Gama'),
(3, 'FCE - Ceilândia'),
(4, 'FUP - Planaltina'),
(5, 'FAL - Fazenda Água Limpa');

-- 2. Inserindo Grupos de Acesso
INSERT INTO Grupo_Acesso (id_categoria, nome_categoria, valor_refeicao, valor_desjejum) VALUES
(1, 'Grupo 1', 0.00, 0.00),
(2, 'Grupo 2', 4.50, 2.00),
(3, 'Grupo 3', 15.20, 7.05),
(4, 'Grupo 4', 2.50, 1.50);

-- 3. Inserindo Restaurantes Universitários
INSERT INTO Restaurante_Universitario (id_ru, nome_ru, id_campus) VALUES 
(1, 'RU Central Darcy', 1),
(2, 'RU Gama', 2),
(3, 'RU Ceilândia', 3),
(4, 'RU Planaltina', 4),
(5, 'RU Setor Norte', 5);

-- 4. Inserindo Refeitórios (andar NULL para salões únicos)
INSERT INTO Refeitorio (id_refeitorio, nome_refeitorio, tipo_servico, andar, id_ru) VALUES 
(1,  'Refeitório 1', 'Padrão', 0, 1),
(2,  'Refeitório 2', 'Padrão', 0, 1),
(3,  'Refeitório 3', 'Padrão', 1, 1),
(4,  'Refeitório 4', 'Padrão', 1, 1),
(5,  'Refeitório 5', 'Padrão', 2, 1),
(6,  'Refeitório 6', 'Padrão', 2, 1),
(7,  'Restaurante Executivo', 'Executivo', 3, 1),
(8,  'Salão Único FGA', 'Padrão', NULL, 2),
(9,  'Salão Único FCE', 'Padrão', NULL, 3),
(10, 'Salão Único FUP', 'Padrão', NULL, 4),
(11, 'Salão Único FAL', 'Padrão', NULL, 5);

-- 5. Inserindo Catracas
INSERT INTO Catraca (status_operacao, id_refeitorio) VALUES 
('Ativa', 1),
('Ativa', 2),
('Ativa', 3),
('Em Manutenção', 4),
('Ativa', 5),
('Ativa', 6),
('Ativa', 7),
('Ativa', 8),
('Ativa', 9),
('Ativa', 10),
('Ativa', 11);
