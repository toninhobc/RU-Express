# RU-Express - User Stories para Testes

## Histórias de Usuário por Feature

---

## Feature 1: Gestão de Usuários (CRUD)

### US-01: Visualizar Perfil de Usuário
**Como** usuário do sistema  
**Quero** visualizar meu perfil completo  
**Para** verificar minhas informações cadastradas  

**Critérios de Aceitação:**
- [ ] API `/api/profile` retorna dados do usuário por `usuario_id`
- [ ] Retorna nome, email, categoria, matrícula (se estudante), SIAPE (se servidor), departamento, motivo_visita (se visitante)
- [ ] Retorna `prioridade_legal` corretamente
- [ ] Retorna foto_perfil se existir (BLOB não serializa no JSON, mas não quebra)
- [ ] Retorna HTTP 404 se usuário não existir

**Dados de Teste:**
- Estudante: usuario_id=1
- Servidor: usuario_id com siape
- Visitante: usuario_id com motivo_visita

---

### US-02: Criar Novo Usuário
**Como** administrador  
**Quero** cadastrar novos usuários no sistema  
**Para** adicionar pessoas ao RU  

**Critérios de Aceitação:**
- [ ] API POST `/api/usuarios` cria usuário com sucesso
- [ ] Campos obrigatórios: nome, email, prioridade_legal, id_categoria
- [ ] Retorna HTTP 201 com `id_usuario` do novo usuário
- [ ] Retorna HTTP 409 se email já existir (UNIQUE constraint)
- [ ] Retorna HTTP 400 se id_categoria não existir (FK constraint)
- [ ] Email é salvo corretamente no banco

**Casos de Teste:**
- ✅ Criar estudante válido
- ✅ Criar servidor válido
- ✅ Criar visitante válido
- ❌ Email duplicado
- ❌ Categoria inexistente

---

### US-03: Atualizar Usuário
**Como** administrador  
**Quero** atualizar dados de usuários  
**Para** manter informações corrigidas  

**Critérios de Aceitação:**
- [ ] API PUT `/api/usuarios/{id}` atualiza campos enviados
- [ ] Apenas campos não-nulos são atualizados (PATCH behavior)
- [ ] Retorna HTTP 200 com `{"status": "atualizado"}`
- [ ] Retorna HTTP 400 se nenhum campo for enviado
- [ ] Retorna HTTP 404 se usuário não existir
- [ ] Permite atualizar: nome, email, prioridade_legal, id_categoria

**Casos de Teste:**
- ✅ Atualizar apenas nome
- ✅ Atualizar apenas email
- ✅ Atualizar múltiplos campos
- ❌ Atualizar usuário inexistente
- ❌ Enviar body vazio

---

### US-04: Remover Usuário
**Como** administrador  
**Quero** excluir usuários do sistema  
**Para** remover cadastros inválidos  

**Critérios de Aceitação:**
- [ ] API DELETE `/api/usuarios/{id}` remove usuário
- [ ] Retorna HTTP 204 (No Content) em sucesso
- [ ] Retorna HTTP 404 se usuário não existir
- [ ] Retorna HTTP 409 se usuário tem histórico (FK constraint error 1451)
- [ ] CASCADE delete funciona para tabelas dependentes (Estudante, Servidor_Docente, Visitante)

**Casos de Teste:**
- ✅ Excluir usuário sem histórico
- ❌ Excluir usuário com recargas
- ❌ Excluir usuário com acessos
- ❌ Excluir usuário com bilhetes FastPass

---

## Feature 2: Gestão de Saldo

### US-05: Visualizar Saldo
**Como** usuário  
**Quero** consultar meu saldo atual  
**Para** saber quanto posso gastar  

**Critérios de Aceitação:**
- [ ] API GET `/api/balance?usuario_id=X` retorna saldo
- [ ] Retorna `saldo_atual` como decimal
- [ ] Retorna HTTP 404 se usuário não existir
- [ ] Saldo reflete todas as transações (recargas, gastos na catraca)

**Casos de Teste:**
- ✅ Saldo positivo normal
- ✅ Saldo zero
- ❌ Usuário inexistente

---

### US-06: Recarregar Saldo
**Como** usuário  
**Quero** adicionar créditos à minha conta  
**Para** poder fazer refeições  

**Critérios de Aceitação:**
- [ ] API POST `/api/balance/recharge` processa recarga
- [ ] Campos obrigatórios: usuario_id, valor (> 0), metodo_pagamento
- [ ] Valor é inserido na tabela Recarga_Saldo
- [ ] TRIGGER `trg_atualizar_saldo_apos_recarga` atualiza saldo automaticamente
- [ ] Retorna HTTP 201 com `saldo_atual` atualizado
- [ ] Retorna HTTP 404 se usuário não existir

**Métodos de Pagamento:**
- PIX
- Cartão de Crédito
- Boleto

**Casos de Teste:**
- ✅ Recarga de R$ 10,00 via PIX
- ✅ Recarga de R$ 100,00 via Cartão
- ✅ Recarga de R$ 50,00 via Boleto
- ❌ Valor = 0
- ❌ Valor negativo
- ❌ Usuário inexistente

**Verificação Pós-Recarga:**
- [ ] Saldo anterior + valor_recarga = saldo_atual
- [ ] Trigger foi executado corretamente

---

## Feature 3: Controle de Acessos

### US-07: Listar Histórico de Acessos
**Como** usuário  
**Quero** ver meu histórico de entradas no RU  
**Para** consultar quando e onde usei o restaurante  

**Critérios de Aceitação:**
- [ ] API GET `/api/accesses?usuario_id=X&limit=20&offset=0` retorna acessos
- [ ] Retorna lista com data_hora_entrada, catraca, valor_cobrado, peso_prato_kg
- [ ] Suporta paginação com limit/offset
- [ ] Retorna HTTP 404 se usuário não existir (via balance query)

**Casos de Teste:**
- ✅ Listar últimos 20 acessos
- ✅ Listar com limit=5
- ✅ Listar com offset=10
- ✅ Histórico vazio

---

### US-08: Registrar Novo Acesso (Catraca)
**Como** sistema de catraca  
**Quero** registrar entrada do usuário automaticamente  
**Para** controlar fluxo e cobrar refeição  

**Critérios de Aceitação:**
- [ ] API POST `/api/accesses?usuario_id=X&catraca=Y` (endpoint mockado)
- [ ] TRIGGER `trg_cobrar_acesso` define automaticamente:
  - tipo_refeicao: 'Desjejum' se hora < 10, senão 'Refeicao'
- [ ] TRIGGER cobra valor correto baseado em:
  - **Padrão**: valor do Grupo_Acesso (valor_desjejum ou valor_refeicao)
  - **Executivo**: valor_cobrado é obrigatório no INSERT
- [ ] TRIGGER atualiza saldo_atual do usuário (saldo - valor_cobrado)
- [ ] Retorna HTTP 500 se refeitório for Executivo e valor_cobrado for NULL

**Casos de Teste (via INSERT direto no banco):**
- ✅ Acesso às 08:30 → tipo_refeicao = 'Desjejum'
- ✅ Acesso às 12:00 → tipo_refeicao = 'Refeicao'
- ✅ Acesso em refeitório Padrão → valor automático do Grupo_Acesso
- ✅ Acesso em refeitório Executivo com valor_cobrado definido
- ❌ Acesso em refeitório Executivo SEM valor_cobrado → erro

**Verificação Pós-Acesso:**
- [ ] Saldo diminuiu corretamente
- [ ] Registro criado em Acesso_RU

---

## Feature 4: Refeitórios e Campus

### US-09: Listar Refeitórios
**Como** usuário  
**Quero** visualizar opções de refeitórios disponíveis  
**Para** escolher onde solicitar FastPass  

**Critérios de Aceitação:**
- [ ] API GET `/api/refeitorios` retorna lista
- [ ] Retorna id_refeitorio, nome_refeitorio, tipo_servico, andar, nome_ru, nome_campus
- [ ] Inclui todos os refeitórios cadastrados (Padrão e Executivo)

**Casos de Teste:**
- ✅ Listar todos refeitórios
- ✅ Verificar tipos de serviço (Padrão/Executivo)
- ✅ Verificar hierarquia Campus → RU → Refeitório

---

## Feature 5: Sistema FastPass

### US-10: Visualizar Meus Bilhetes FastPass
**Como** usuário  
**Quero** ver todos os meus bilhetes FastPass  
**Para** acompanhar meus sorteios e status  

**Critérios de Aceitação:**
- [ ] API GET `/api/fastpass/meus-bilhetes?usuario_id=X&status_uso=Y` retorna bilhetes
- [ ] Retorna bilhetes ordenados por horario_inicio DESC
- [ ] Filtra por status_uso se fornecido (Pendente, Utilizado, Expirado)
- [ ] Sem filtro retorna todos os bilhetes do usuário
- [ ] Inclui dados do sorteio e refeitório

**Status Possíveis:**
- Pendente
- Utilizado
- Expirado

**Casos de Teste:**
- ✅ Listar todos bilhetes
- ✅ Filtrar por Pendente
- ✅ Filtrar por Utilizado
- ✅ Lista vazia (sem bilhetes)

---

### US-11: Solicitar Participação em Sorteio FastPass
**Como** estudante  
**Quero** participar do sorteio de FastPass  
**Para** ter chances de pegar fila rápida  

**Critérios de Aceitação:**
- [ ] API POST `/api/fastpass/solicitar` processa solicitação
- [ ] Apenas Estudantes podem participar (validação por tabela Estudante)
- [ ] Retorna HTTP 403 se usuário não for estudante
- [ ] Não permite dois sorteios na mesma faixa de horário (validação em Sorteio_Diario)
- [ ] Retorna HTTP 409 se sorteio já existir para a faixa
- [ ] Executa PROCEDURE `Gerar_Sorteio_FastPass` com sucesso
- [ ] Retorna HTTP 201 com sucesso

**Lógica da Procedure:**
1. Cria registro em Sorteio_Diario com horario_inicio, horario_fim, quantidade_vagas
2. Sorteia `p_vagas` estudantes usando peso: `POW(RAND(), 1.0 / (dias_sem_fastpass + 1))`
3. Cria Bilhete_FastPass para ganhadores com status 'Pendente'
4. Atualiza peso dos NÃO ganhadores: `dias_sem_fastpass + 1`
5. Reseta peso dos ganhadores: `dias_sem_fastpass = 0`

**Casos de Teste:**
- ✅ Estudante solicita FastPass válido
- ✅ Várias solicitações no mesmo dia (dias_sem_fastpass acumula)
- ✅ Verificar probabilidade maiores para quem tem mais dias sem
- ❌ Servidor tenta solicitar (403)
- ❌ Visitante tenta solicitar (403)
- ❌ Faixa de horário já existe (409)

**Verificação Pós-Sorteio:**
- [ ] Ganhadores têm bilhetes criados
- [ ] Ganhadores têm dias_sem_fastpass = 0
- [ ] Perdedores tiveram dias incrementados

---

## Feature 6: Painel Administrativo

### US-12: Visualizar Relatório de Fluxo
**Como** administrador  
**Quero** ver estatísticas de fluxo por refeitório  
**Para** tomar decisões operacionais  

**Critérios de Aceitação:**
- [ ] API GET `/api/admin/relatorio-fluxo` retorna VIEW `vw_relatorio_fluxo_ru`
- [ ] Retorna dados do dia atual (DATE(data_hora_entrada) = CURDATE())
- [ ] Agrupa por refeitório: total_pessoas_atendidas, faturamento_diario
- [ ] Retorna HTTP 200

**Campos Retornados:**
- nome_refeitorio
- tipo_servico
- total_pessoas_atendidas
- faturamento_diario

**Casos de Teste:**
- ✅ Dia com acessos registrados
- ✅ Dia sem acessos (valores zerados)

---

### US-13: Gerenciar Usuários (Admin)
**Como** administrador  
**Quero** buscar e filtrar usuários  
**Para** gerenciar cadastros  

**Critérios de Aceitação:**
- [ ] API GET `/api/admin/usuarios?categoria=X&busca=Y` retorna lista
- [ ] Filtra por id_categoria se fornecido
- [ ] Busca por nome OU email (LIKE %termo%)
- [ ] Ordena por nome ASC
- [ ] Exclui foto_perfil (BLOB) da serialização JSON
- [ ] Retorna HTTP 200

**Casos de Teste:**
- ✅ Listar todos usuários
- ✅ Filtrar por categoria
- ✅ Buscar por nome
- ✅ Buscar por email
- ✅ Combinar filtros

---

## Feature 7: Frontend - Interface do Usuário

### US-14: Dashboard Inicial
**Como** usuário  
**Quero** ver um resumo dashboard ao acessar o sistema  
**Para** ter visão geral do meu status  

**Critérios de Aceitação:**
- [ ] Página carrega dados do usuário
- [ ] Exibe foto de perfil ou placeholder se não houver BLOB
- [ ] Exibe nome, email, categoria, matrícula/SIAPE
- [ ] Exibe saldo atual formatado em R$
- [ ] Mostra QR Code da carteirinha digital
- [ ] Mostra último acesso
- [ ] Mostra quantidade de FastPass pendentes
- [ ] Exibe seção de ações rápidas
- [ ] Exibe tabela de últimos acessos
- [ ] Exibe lista de FastPass do usuário

---

### US-15: Modal de Recarga de Saldo
**Como** usuário  
**Quero** recarregar saldo através da interface  
**Para** adicionar créditos facilmente  

**Critérios de Aceitação:**
- [ ] Botão "Recarregar Saldo" abre modal
- [ ] Exibe valores pré-definidos: R$ 10, R$ 20, R$ 50, R$ 100
- [ ] Permite selecionar método de pagamento (PIX, Cartão, Boleto)
- [ ] Ao selecionar PIX, mostra área de QR Code simulado
- [ ] Botão "Confirmar" chama API de recarga
- [ ] Modal fecha após sucesso
- [ ] Toast de confirmação aparece
- [ ] Saldo na tela atualiza automaticamente

**Casos de Teste UI:**
- ✅ Selecionar R$ 50 via PIX
- ✅ Selecionar R$ 100 via Cartão
- ❌ Confirmar sem selecionar valor

---

### US-16: Modal de Solicitação FastPass
**Como** estudante  
**Quero** solicitar FastPass pela interface  
**Para** participar do sorteio  

**Critérios de Aceitação:**
- [ ] Card "Solicitar FastPass" abre modal
- [ ] Carrega lista de refeitórios
- [ ] Data padrão é hoje
- [ ] Exibe situação atual (dias sem FastPass, chances)
- [ ] Permite selecionar refeitório e horário
- [ ] Valida campos antes de enviar
- [ ] Chama API `/api/fastpass/solicitar`
- [ ] Exibe mensagens de erro/sucesso
- [ ] Recarrega lista de bilhetes após sucesso

**Horários Disponíveis:**
- Almoço: 11:30 - 14:00
- Jantar: 17:30 - 19:30
- Desjejum: 07:00 - 09:00

**Casos de Teste UI:**
- ✅ Selecionar data, RU e horário → sucesso
- ❌ Não selecionar data → erro
- ❌ Não selecionar refeitório → erro

---

### US-17: Modal de Histórico de Acessos
**Como** usuário  
**Quero** ver histórico completo de acessos  
**Para** consultar entradas passadas  

**Critérios de Aceitação:**
- [ ] Card "Últimos Acessos" ou link "ver todos" abre modal
- [ ] Carrega até 50 acessos via API
- [ ] Exibe tabela com: Data, Catraca, Valor, Peso
- [ ] Modal tem scroll se necessário
- [ ] Botão fechar fecha modal

---

### US-18: Exibição de QR Code Digital
**Como** usuário  
**Quero** gerar e visualizar QR Code da carteirinha  
**Para** usar na catraca  

**Critérios de Aceitação:**
- [ ] QR Code é gerado com dados do usuário (tipo, id, nome, matrícula, email, categoria, prioridade)
- [ ] Biblioteca qrcode.js renderiza corretamente
- [ ] Botão "Regenerar QR" atualiza código
- [ ] Botão "Download" salva PNG
- [ ] Dados no QR são JSON válido

**Estrutura do QR:**
```json
{
  "tipo": "USUARIO_RU",
  "id": 1,
  "nome": "João Silva",
  "matricula": "190012345",
  "email": "joao@aluno.unb.br",
  "categoria": "Grupo 2",
  "prioridade": false
}
```

---

## Feature 8: Integridade de Dados (Database)

### US-19: Trigger de Recarga de Saldo
**Como** sistema  
**Quero** atualizar saldo automaticamente após recarga  
**Para** manter consistência financeira  

**Critérios de Aceitação:**
- [ ] TRIGGER `trg_atualizar_saldo_apos_recarga` é AFTER INSERT
- [ ] Dispara após INSERT em Recarga_Saldo
- [ ] Executa: UPDATE Usuario_RU SET saldo_atual = saldo_atual + NEW.valor_adicionado
- [ ] Não permite bypass da trigger (deve ser INSERT + trigger)
- [ ] Funciona para múltiplas recargas simultâneas

---

### US-20: Trigger de Cobrança na Catraca
**Como** sistema  
**Quero** cobrar automaticamente na catraca  
**Para** garantir pagamento de refeições  

**Critérios de Aceitação:**
- [ ] TRIGGER `trg_cobrar_acesso` é BEFORE INSERT
- [ ] Define tipo_refeicao automaticamente:
  - 'Desjejum' se HOUR(data_hora_entrada) < 10
  - 'Refeicao' caso contrário
- [ ] Para refeitórios Padrão: busca valor_cobrado do Grupo_Acesso
- [ ] Para refeitórios Executivo: exige valor_cobrado != NULL
- [ ] Atualiza saldo_atual = saldo_atual - valor_cobrado
- [ ] Levanta erro se valor_cobrado for NULL em Executivo

**Casos de Teste:**
- ✅ Entrada 08:45 Padrão → Desjejum, valor do grupo
- ✅ Entrada 12:30 Padrão → Refeicao, valor do grupo
- ✅ Entrada 13:00 Executivo com valor → valor_cobrado definido
- ❌ Entrada Executivo sem valor → SIGNAL SQLSTATE erro

---

### US-21: Procedure de Sorteio FastPass
**Como** sistema  
**Quero** realizar sorteio ponderado justo  
**Para** distribuir FastPass de forma equitativa  

**Critérios de Aceitação:**
- [ ] PROCEDURE `Gerar_Sorteio_FastPass` executa atomicamente
- [ ] Cria entrada em Sorteio_Diario
- [ ] Sorteia VAGASFASTPASS (20) ganhadores
- [ ] Usa fórmula: `ORDER BY POW(RAND(), 1.0 / (dias_sem_fastpass + 1)) DESC`
- [ ] Cria bilhetes para ganhadores em Bilhete_FastPass
- [ ] Atualiza peso dos não-ganhadores (incrementa dias_sem_fastpass)
- [ ] Reseta peso dos ganhadores (zera dias_sem_fastpass)
- [ ] Usa tabela temporária Temp_Ganhadores
- [ ] Limpa tabela temporária ao final

**Validações:**
- [ ] Probabilidade maior para dias_sem_fastpass maior
- [ ] Exatamente VAGASFASTPASS bilhetes criados
- [ ] Não cria duplicatas para mesma faixa

---

## Resumo de Cobertura

### Backend APIs Testáveis
| Método | Endpoint | Funcionalidade |
|--------|----------|----------------|
| GET | /api/profile | Visualizar perfil |
| POST | /api/usuarios | Criar usuário |
| PUT | /api/usuarios/{id} | Atualizar usuário |
| DELETE | /api/usuarios/{id} | Remover usuário |
| GET | /api/balance | Consultar saldo |
| POST | /api/balance/recharge | Recarregar saldo |
| GET | /api/accesses | Listar acessos |
| POST | /api/accesses | Registrar acesso |
| GET | /api/refeitorios | Listar refeitórios |
| GET | /api/admin/relatorio-fluxo | Relatório fluxo |
| GET | /api/admin/usuarios | Gerenciar usuários |
| GET | /api/fastpass/meus-bilhetes | Meus bilhetes |
| POST | /api/fastpass/solicitar | Solicitar FastPass |

### Triggers Testáveis
- `trg_atualizar_saldo_apos_recarga` (AFTER INSERT)
- `trg_cobrar_acesso` (BEFORE INSERT)

### Procedures Testáveis
- `Gerar_Sorteio_FastPass`

### Views Testáveis
- `vw_relatorio_fluxo_ru`

---

## Dados de Teste (IDs Conhecidos)

### Grupos de Acesso
- ID 1: Grupo 1 (R$ 0,00 / R$ 0,00) - Gratuito
- ID 2: Grupo 2 (R$ 4,50 / R$ 2,00)
- ID 3: Grupo 3 (R$ 15,20 / R$ 7,05)
- ID 4: Grupo 4 (R$ 2,50 / R$ 1,50)

### Campus e RUs
- Campus 1: Darcy Ribeiro → RU Central Darcy
- Campus 2: FGA → RU Gama
- Campus 3: FCE → RU Ceilândia

### Refeitórios (para testes)
- ID 1-6: Padrão, RU Central (andares 0-2)
- ID 7: Executivo, RU Central (andar 3)
- ID 8: Padrão, RU Gama (Salão Único)

---

## Checklist de Testes E2E

### Fluxo 1: Usuário Novo Completo
1. [ ] Criar usuário estudante (API)
2. [ ] Verificar perfil
3. [ ] Fazer recarga de R$ 50
4. [ ] Solicitar FastPass
5. [ ] Verificar bilhetes gerados
6. [ ] Simular acesso na catraca
7. [ ] Verificar saldo debitado
8. [ ] Consultar histórico de acessos

### Fluxo 2: Administrador
1. [ ] Consultar relatório de fluxo
2. [ ] Listar todos usuários
3. [ ] Filtrar usuários por categoria
4. [ ] Buscar usuário por nome/email

### Fluxo 3: Frontend Interação
1. [ ] Abrir página inicial
2. [ ] Visualizar QR Code
3. [ ] Abrir modal de recarga
4. [ ] Realizar recarga
5. [ ] Abrir modal FastPass
6. [ ] Solicitar participação
7. [ ] Visualizar bilhetes
8. [ ] Abrir histórico de acessos

### Fluxo 4: Edge Cases
1. [ ] Usuário com saldo zero tenta acessar
2. [ ] FastPass em refeitório já sorteado
3. [ ] Deleção de usuário com histórico (409)
4. [ ] Acesso em Executivo sem valor (erro trigger)
5. [ ] Email duplicado (409)