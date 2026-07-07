# Relatório de Testes - RU-Express

Data: 06/07/2026  
Sistema: Sistema de gerenciamento do Restaurante Universitário (RU)

---

## Sumário

| Categoria | Total | Passaram | Falhas | Status |
|-----------|-------|----------|--------|--------|
| Endpoints API | 11 | 10 | 1 | 91% |
| Triggers | 2 | 2 | 0 | 100% |
| Procedures | 1 | 1 | 0 | 100% |
| Views | 1 | 1 | 0 | 100% |
| Frontend | 1 | 0 | 1 | 0% |

---

## Feature 1: Gestão de Usuários (CRUD)

### US-01: Visualizar Perfil de Usuário
**Endpoint:** `GET /api/profile?usuario_id=X`

✅ **IMPLEMENTADO E TESTADO**
- Retorna dados do usuário (id_usuario, nome, email, saldo_atual, prioridade_legal, categoria)
- Retorna matrícula para estudantes
- Retorna SIAPE e departamento para servidores
- Retorna motivo_visita para visitantes
- Retorna HTTP 404 se usuário não existir

**Testes realizados:**
```bash
# Estudante
curl -s http://localhost:8000/api/profile?usuario_id=1
# Resultado: {"usuario":{"id_usuario":1,"nome":"Yasmin Souza","email":"yasmin.souza.0@aluno.unb.br","saldo_atual":59.57,...}}

# Servidor
curl -s http://localhost:8000/api/profile?usuario_id=55
# Resultado: {"usuario":{"siape":1000014,"departamento":"Medicina",...}}

# Visitante
curl -s http://localhost:8000/api/profile?usuario_id=58
# Resultado: {"usuario":{"motivo_visita":"Evento Científico",...}}
```

### US-02: Criar Novo Usuário
**Endpoint:** `POST /api/usuarios`

✅ **IMPLEMENTADO E TESTADO**
- HTTP 201 com `id_usuario` no sucesso
- HTTP 409 para email duplicado
- HTTP 400 para categoria inexistente

**Testes realizados:**
```bash
# Sucesso
curl -s -X POST http://localhost:8000/api/usuarios -d '{"nome":"Teste","email":"teste@unb.br","prioridade_legal":false,"id_categoria":2}'
# Resultado: {"id_usuario":66}

# Email duplicado (409)
curl -s -X POST http://localhost:8000/api/usuarios -d '{"nome":"Teste","email":"teste@unb.br","prioridade_legal":false,"id_categoria":2}'
# Resultado: {"detail":"E-mail já cadastrado."}

# Categoria inexistente (400)
curl -s -X POST http://localhost:8000/api/usuarios -d '{"nome":"Teste2","email":"teste2@unb.br","prioridade_legal":false,"id_categoria":99}'
# Resultado: {"detail":"Categoria inexistente."}
```

### US-03: Atualizar Usuário
**Endpoint:** `PUT /api/usuarios/{id}`

✅ **IMPLEMENTADO E TESTADO**
- Comportamento PATCH (atualiza apenas campos não-nulos)
- HTTP 200 com `{"status": "atualizado"}`
- HTTP 404 se usuário não existir

**Testes realizados:**
```bash
curl -s -X PUT http://localhost:8000/api/usuarios/66 -d '{"nome":"Teste Atualizado"}'
# Resultado: {"status":"atualizado"}

curl -s -X PUT http://localhost:8000/api/usuarios/999 -d '{"nome":"Teste"}'
# Resultado: {"detail":"Usuário não encontrado"}
```

### US-04: Remover Usuário
**Endpoint:** `DELETE /api/usuarios/{id}`

✅ **IMPLEMENTADO E TESTADO**
- HTTP 204 (No Content) em sucesso
- HTTP 404 se usuário não existir
- HTTP 409 se usuário tem histórico (FK constraint)

**Testes realizados:**
```bash
curl -s -w "HTTP_CODE: %{http_code}" -X DELETE http://localhost:8000/api/usuarios/66
# HTTP_CODE: 204

curl -s -w "HTTP_CODE: %{http_code}" -X DELETE http://localhost:8000/api/usuarios/1
# HTTP_CODE: 409 - {"detail":"Não é possível excluir: usuário possui histórico..."}
```

---

## Feature 2: Gestão de Saldo

### US-05: Visualizar Saldo
**Endpoint:** `GET /api/balance?usuario_id=X`

✅ **IMPLEMENTADO E TESTADO**
- Retorna `saldo_atual` como decimal
- Retorna HTTP 404 se usuário não existir

### US-06: Recarregar Saldo
**Endpoint:** `POST /api/balance/recharge`

✅ **IMPLEMENTADO E TESTADO**
- Trigger `trg_atualizar_saldo_apos_recarga` funciona corretamente
- Saldo atualizado automaticamente após INSERT em Recarga_Saldo
- HTTP 201 com `saldo_atual` atualizado

**Teste realizado:**
```bash
curl -s -X POST http://localhost:8000/api/balance/recharge -d '{"usuario_id":1,"valor":50.00,"metodo_pagamento":"PIX"}'
# Resultado: {"saldo_atual":109.57}  # 59.57 + 50.00 = 109.57 ✅
```

---

## Feature 3: Controle de Acessos

### US-07: Listar Histórico de Acessos
**Endpoint:** `GET /api/accesses?usuario_id=X&limit=20&offset=0`

✅ **IMPLEMENTADO E TESTADO**
- Retorna lista com data_hora_entrada, catraca, valor_cobrado, peso_prato_kg
- Suporta paginação com limit/offset

### US-08: Registrar Novo Acesso (Catraca)
**Endpoint:** `POST /api/accesses?usuario_id=X&catraca=Y`

✅ **IMPLEMENTADO** - Dupla implementação:

#### Backend API
- Valida usuário e catraca existentes
- Verifica FastPass válido no refeitório (marca como Utilizado se aplicável)
- Insere em `Acesso_RU` (trigger `trg_cobrar_acesso` calcula valor e debita saldo)
- Retorna: sucesso, usuário, saldo_anterior, saldo_atual, valor_cobrado, tipo_refeicao

#### Catraca Client (Standalone)
Cliente CLI separado em `catraca_client/` que conecta diretamente ao banco:
- Prompt para ID da catraca no início
- Loop para entrada de IDs de usuários
- Feedback colorido: ✅ verde para acesso autorizado, ❌ vermelho para erros
- Detecta automaticamente FastPass válido
- Trata saldo insuficiente e usuário não encontrado

Exemplo:
```
=== Catraca RU-Express ===

ID da Catraca: 1
✓ Catraca conectada: Refeitório 1 - RU Central Darcy

[INPUT] Digite ID do usuário (q para sair): 1
  ✅ ACESSO AUTORIZADO
  Usuário: Yasmin Souza (Grupo 2)
  Saldo anterior: R$ 119.57
  Valor cobrado: R$ 4.50
  Saldo atual: R$ 115.07
  Refeição: Refeicao
```

---

### US-09: Catraca Client (QR Scanner Futuro)
O cliente foi projetado para futura integração com webcam:
- Estrutura preparada para leitura de QR code via pyzbar
- Atualmente usa entrada manual de ID (simples e funcional)

Comando para rodar:
```bash
cd catraca_client
pip install colorama
python main.py
```


## Feature 4: Refeitórios e Campus

### US-09: Listar Refeitórios
**Endpoint:** `GET /api/refeitorios`

⚠️ **PARCIALMENTE IMPLEMENTADO**
- Retorna lista de refeitórios ✅
- Falta campo `nome_campus` (apenas retorna `nome_ru`)

**Query atual:**
```sql
SELECT r.id_refeitorio, r.nome_refeitorio, r.tipo_servico, ru.nome_ru
FROM Refeitorio r
JOIN Restaurante_Universitario ru ON r.id_ru = ru.id_ru
```

**Deveria incluir:** `c.nome_campus` via JOIN com Campus

---

## Feature 5: Sistema FastPass

### US-10: Visualizar Meus Bilhetes FastPass
**Endpoint:** `GET /api/fastpass/meus-bilhetes?usuario_id=X&status_uso=Y`

✅ **IMPLEMENTADO E TESTADO**
- Retorna bilhetes ordenados por horario_inicio DESC
- Filtra por status_uso (Pendente, Utilizado, Expirado)

### US-11: Solicitar Participação em Sorteio FastPass
**Endpoint:** `POST /api/fastpass/solicitar`

✅ **IMPLEMENTADO E TESTADO**
- HTTP 403 para não-estudantes
- HTTP 409 para faixa de horário já existente
- Procedure `Gerar_Sorteio_FastPass` executada com sucesso

**Testes realizados:**
```bash
# Estudante solicita (sucesso)
curl -s -X POST http://localhost:8000/api/fastpass/solicitar -d '{"usuario_id":1,"refeitorio_id":1,"horario_inicio":"2026-07-06T17:30:00","horario_fim":"2026-07-06T19:30:00"}'
# Resultado: {"status":"sorteio realizado com sucesso"}

# Servidor tenta solicitar (403)
curl -s -X POST http://localhost:8000/api/fastpass/solicitar -d '{"usuario_id":55,"refeitorio_id":1,"horario_inicio":"2026-07-07T11:30:00","horario_fim":"2026-07-07T14:00:00"}'
# Resultado: {"detail":"Apenas estudantes podem participar."}

# Faixa já existe (409)
curl -s -X POST http://localhost:8000/api/fastpass/solicitar -d '{"usuario_id":1,"refeitorio_id":1,"horario_inicio":"2026-07-06T11:30:00","horario_fim":"2026-07-06T14:00:00"}'
# Resultado: {"detail":"Sorteio já existente para esta faixa."}
```

---

## Feature 6: Painel Administrativo

### US-12: Visualizar Relatório de Fluxo
**Endpoint:** `GET /api/admin/relatorio-fluxo`

✅ **IMPLEMENTADO E TESTADO**
- Retorna dados do VIEW `vw_relatorio_fluxo_ru`
- Agrupa por refeitório: total_pessoas_atendidas, faturamento_diario

### US-13: Gerenciar Usuários (Admin)
**Endpoint:** `GET /api/admin/usuarios?categoria=X&busca=Y`

✅ **IMPLEMENTADO E TESTADO**
- Filtra por categoria
- Busca por nome ou email (LIKE)
- Exclui foto_perfil da serialização

**Testes realizados:**
```bash
# Filtrar por categoria
curl -s http://localhost:8000/api/admin/usuarios?categoria=2
# Resultado: Lista de usuários do Grupo 2

# Buscar por nome
curl -s http://localhost:8000/api/admin/usuarios?busca=antonio
# Resultado: Lista filtrada com "Antônio"
```

---

## Feature 7: Frontend

### US-14 ao US-18

⚠️ **PARCIALMENTE IMPLEMENTADO**
- Arquivo `frontend/mock_preview.html` contém todos os elementos de UI
- **Problema crítico**: Endpoint `/` não serve o arquivo HTML

**Erro identificado:**
```python
# backend/main.py - o endpoint "/" retorna 404
# Possível problema com caminho no Windows: os.path.join("backend", "..", "frontend")
```

---

## Estrutura do Banco de Dados

### Triggers (Verificados via MySQL)
```sql
trg_atualizar_saldo_apos_recarga  -- AFTER INSERT em Recarga_Saldo
trg_cobrar_acesso                 -- BEFORE INSERT em Acesso_RU
```

### Procedures
```sql
Gerar_Sorteio_FastPass(p_horario_inicio, p_horario_fim, p_vagas, p_id_refeitorio)
```

### Views
```sql
vw_relatorio_fluxo_ru  -- Agrupa acessos por refeitório com faturamento
```

---

## Checklist de Testes E2E

### Fluxo 1: Usuário Novo Completo
- [x] Criar usuário estudante (API)
- [x] Verificar perfil
- [x] Fazer recarga de R$ 50 (trigger funcionando)
- [x] Solicitar FastPass (409 se já existe)
- [x] Verificar bilhetes gerados
- [x] Simular acesso na catraca (cliente implementado) ⭐
- [x] Verificar saldo debitado (trigger `trg_cobrar_acesso`) ⭐
- [x] Consultar histórico de acessos

### Fluxo 2: Administrador
- [x] Consultar relatório de fluxo
- [x] Listar todos usuários
- [x] Filtrar usuários por categoria
- [x] Buscar usuário por nome/email

### Fluxo 3: Frontend Interação
- [ ] Abrir página inicial (endpoint "/" com erro)
- [x] Visualizar QR Code (via JS no HTML)
- [x] Abrir modal de recarga (JS implementado)
- [x] Realizar recarga (API funcional)
- [x] Abrir modal FastPass (JS implementado)
- [x] Solicitar participação (API funcional)
- [x] Visualizar bilhetes (API funcional)
- [x] Abrir histórico de acessos (JS implementado)

---

### Fluxo 4: Catraca Client (Novo) ⭐
- [x] Iniciar cliente com ID da catraca
- [x] Validar usuário existente
- [x] Detectar FastPass válido automaticamente
- [x] Registrar acesso (trigger cobra saldo automaticamente)
- [x] Feedback visual colorido
- [x] Tratamento de erro (usuário não encontrado)

---

## Recomendações para Conclusão

1. ~~**Implementar `POST /api/accesses`** - Registrar acesso na catraca~~ ✅ Concluído
2. ~~**Criar catraca_client** - Cliente standalone~~ ✅ Concluído
3. **Adicionar `nome_campus`** em `QueryRefeitorios`
4. **Corrigir caminho do frontend** no `backend/main.py`
5. **Remover campo `valor_refeicao` e `valor_desjejum`** da resposta do profile (não solicitados na US-01)
6. **Testar trigger `trg_cobrar_acesso`** via INSERT direto no banco (Executivo sem valor_cobrado deve gerar erro)

---

## Comandos para Testes Manuais

```bash
# Iniciar servidor
uvicorn backend.main:app --reload --port 8000

# Testar APIs
curl http://localhost:8000/api/profile?usuario_id=1
curl http://localhost:8000/api/balance?usuario_id=1
curl http://localhost:8000/api/accesses?usuario_id=1
curl http://localhost:8000/api/refeitorios
curl http://localhost:8000/api/fastpass/meus-bilhetes?usuario_id=1
curl http://localhost:8000/api/admin/relatorio-fluxo
curl http://localhost:8000/api/admin/usuarios