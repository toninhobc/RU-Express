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

-- 14. Inserindo Bilhetes FastPass (vinculados a sorteios por faixa)
INSERT INTO Bilhete_FastPass (horario_inicio, horario_fim, status_uso, id_sorteio, id_usuario, id_refeitorio) VALUES 
('2026-06-25 11:30:00', '2026-06-25 11:40:00', 'Utilizado', 1, 1, 1),
('2026-06-25 12:00:00', '2026-06-25 12:10:00', 'Utilizado', 2, 3, 2),
('2026-06-26 11:30:00', '2026-06-26 11:40:00', 'Pendente', 3, 2, 1),
('2026-06-26 12:00:00', '2026-06-26 12:10:00', 'Pendente', 4, 3, 2),
('2026-06-27 12:00:00', '2026-06-27 12:10:00', 'Expirado', 5, 5, 4);

-- 3. Inserindo Sorteios Diários (MUDAR!!)
INSERT INTO Sorteio_Diario (data_sorteio, quantidade_vagas) VALUES 
('2026-06-25', 50),
('2026-06-26', 60),
('2026-06-27', 50),
('2026-06-28', 100),
('2026-06-29', 50);
