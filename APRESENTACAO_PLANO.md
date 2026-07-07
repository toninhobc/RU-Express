# 🎤 Plano de Apresentação — RU-Express (15 min)

---

## ⏱ SEGMENTO 1: Contexto + Banco de Dados (4 min)

### 0:00 → 0:30 — O que é o RU-Express?
- Sistema de gestão de acesso ao Restaurante Universitário da UnB
- Gerencia saldos, catracas, sorteio ponderado de FastPass
- GitHub: `github.com/toninhobc/RU-Express`

### 0:30 → 2:00 — Modelo do Banco (mostrar mR.pdf / mER.pdf)
- **15 tabelas**, com destaque para o **diagrama MR** (abrir `mR.pdf` ou `mER.pdf`)
- Tabelas principais:
  - `Campus` → `Restaurante_Universitario` → `Refeitorio` → `Catraca`
  - `Grupo_Acesso` → `Usuario_RU` → `Estudante` / `Servidor_Docente` / `Visitante`
  - `Recarga_Saldo`, `Acesso_RU`, `Bilhete_FastPass`, `Inscricao_FastPass`
- **Relações**: FK com `ON DELETE CASCADE`, `UNIQUE KEY`, `CHECK (saldo_atual >= 0)`

### 2:00 → 3:30 — Mostrar dados no MySQL (≥ 5 registros em cada tabela principal)

```sql
USE Ru_Express;

-- Campi (5 registros)
SELECT * FROM Campus;                       -- Darcy, Gama, Ceilândia, Planaltina, FAL

-- Usuarios (65 registros)
SELECT id_usuario, nome, email, saldo_atual, prioridade_legal FROM Usuario_RU LIMIT 10;

-- Grupos de Acesso (4 registros)
SELECT * FROM Grupo_Acesso;

-- Acessos (150 registros)
SELECT * FROM Acesso_RU LIMIT 10;

-- Recargas (60 registros)
SELECT * FROM Recarga_Saldo LIMIT 10;
```

> **Dica**: Rode `SELECT COUNT(*) FROM <tabela>` para mostrar rapidamente a quantidade.

### 3:30 → 4:00 — O BLOB (imagem)
- `Usuario_RU.foto_perfil` é **`BLOB`** — armazena foto PNG/JPEG/WEBP
- `Documentacao_Assistencia.comprovante_pdf` é **`BLOB`** — armazena PDF
- Seed insere `FOTO_DUMMY = bytes.fromhex("89504E47")` (cabeçalho PNG) em todos os estudantes

---

## ⏱ SEGMENTO 2: CRUD + Persistência (4 min)

### 4:00 → 5:30 — A camada de persistência (`backend/db.py`)

```python
def make_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
    )

def get_db():
    conn = make_connection()
    conn.database = DB_NAME
    try:
        yield conn  # Generator usado como dependência do FastAPI
    finally:
        conn.close()
```

- **`init_db()`**: Lê `ru_express.sql` (DDL + triggers + procedures + view), executa, faz seed
- **`get_db()`**: Generator usado como `Depends` em todas as rotas → conexão aberta/fechada automaticamente

### 5:15 → 5:45 — 🚫 Proteção de Integridade Referencial (FK)

**Demonstração ao vivo** — mostra que NÃO é possível deletar um registro com histórico:

```bash
# Tenta deletar usuário COM histórico (acessos/recargas) → ERRO 409
curl -X DELETE http://localhost:8000/api/usuarios/1
# Resposta: {"detail":"Não é possível excluir: usuário possui histórico (recargas/acessos/bilhetes)."}
# HTTP 409 Conflict
```

**Explicação** (abrir `backend/main.py` linha 198–211):
```python
except mysql.connector.Error as e:
    db.rollback()
    cursor.close()
    if e.errno == 1451:  # FK violation — tabelas filhas têm registros
        raise HTTPException(
            status_code=409,
            detail="Não é possível excluir: usuário possui histórico.",
        )
```

**Nível SQL**: O erro `1451` é lançado pelo MySQL porque as tabelas `Recarga_Saldo`, `Acesso_RU` e `Bilhete_FastPass` têm FK para `Usuario_RU` **sem** `ON DELETE CASCADE` (diferente de `Estudante`/`Servidor`/`Visitante` que **têm** CASCADE).

**Contraste**: Usuários **sem** histórico podem ser deletados:
```bash
# Deletar usuário SEM histórico → OK (204 No Content)
curl -X DELETE http://localhost:8000/api/usuarios/48
# HTTP 204
```

### 5:45 → 7:00 — CRUD de Usuários (3 tabelas + relações)

**Rota GET /api/profile** (READ — tabela `Usuario_RU` + JOIN com `Grupo_Acesso`, `Estudante`, `Servidor_Docente`, `Visitante`)
```python
@app.get("/api/profile")
def profile(usuario_id: int = Query(), db=Depends(get_db)):
    cursor.execute(QueryUser, (usuario_id,))  # INNER JOIN + LEFT JOIN
    # Retorna nome, email, saldo, categoria, matrícula/SIAPE/motivo, foto_base64
```

**Rota POST /api/usuarios** (CREATE — tabela `Usuario_RU`)
```python
@app.post("/api/usuarios", status_code=201)
def criar_usuario(body: UsuarioCreate, db=Depends(get_db)):
    cursor.execute(QueryUsuarioInsert, (body.nome, body.email, body.prioridade_legal, body.id_categoria))
```

**Rota PUT /api/usuarios/{id}** (UPDATE — tabela `Usuario_RU`)
```python
@app.put("/api/usuarios/{usuario_id}")
def atualizar_usuario(usuario_id: int, body: UsuarioUpdate, db=Depends(get_db)):
    # Atualiza só campos fornecidos
    set_clause = ", ".join(f"{col} = %s" for col in campos)
    cursor.execute(f"UPDATE Usuario_RU SET {set_clause} WHERE id_usuario = %s", params)
```

**Rota DELETE /api/usuarios/{id}** (DELETE — tabela `Usuario_RU`)
```python
@app.delete("/api/usuarios/{usuario_id}", status_code=204)
def remover_usuario(usuario_id: int, db=Depends(get_db)):
    cursor.execute(QueryUsuarioDelete, (usuario_id,))
```

> **Relações**: `Usuario_RU.id_categoria` → `Grupo_Acesso.id_categoria` (FK). Ao deletar, `Estudante`/`Servidor_Docente`/`Visitante` cascateiam (`ON DELETE CASCADE`).

**Rota POST /api/balance/recharge** (CREATE — tabela `Recarga_Saldo`)
```python
@app.post("/api/balance/recharge", status_code=201)
def recharge_balance(body: RechargeRequest, db=Depends(get_db)):
    cursor.execute(QueryRechargeInsert, (body.valor, agora, body.metodo_pagamento, body.usuario_id))
```

**Rota POST /api/accesses** (CREATE — tabela `Acesso_RU`)
```python
@app.post("/api/accesses")
def novo_acesso(usuario_id: int = Query(), catraca: int = Query(), db=Depends(get_db)):
    cursor.execute("INSERT INTO Acesso_RU (id_usuario, id_catraca, data_hora_entrada) VALUES (...)")
```

---

## ⏱ SEGMENTO 3: Trigger e Procedure (3 min)

### 7:00 → 8:00 — Trigger: `trg_cobrar_acesso`

```sql
CREATE TRIGGER trg_cobrar_acesso
BEFORE INSERT ON Acesso_RU
FOR EACH ROW
BEGIN
    -- 1. Deriva tipo_refeicao pelo horário
    SET NEW.tipo_refeicao = IF(HOUR(NEW.data_hora_entrada) < 10, 'Desjejum', 'Refeicao');

    -- 2. Se refeitório Executivo: valor_cobrado é obrigatório
    -- 3. Se Padrão: busca preço do Grupo_Acesso do usuário
    SET NEW.valor_cobrado = (
        SELECT CASE WHEN tipo_refeicao = 'Desjejum' THEN g.valor_desjejum ELSE g.valor_refeicao END
        FROM Usuario_RU u JOIN Grupo_Acesso g ON u.id_categoria = g.id_categoria
        WHERE u.id_usuario = NEW.id_usuario
    );

    -- 4. Debita saldo
    UPDATE Usuario_RU SET saldo_atual = saldo_atual - NEW.valor_cobrado
    WHERE id_usuario = NEW.id_usuario;
END;
```

**Mostrar funcionamento**: Inserir um acesso e verificar saldo sendo debitado + tipo_refeicao preenchido.

```sql
-- Ver saldo antes
SELECT saldo_atual FROM Usuario_RU WHERE id_usuario = 1;

-- Inserir acesso (trigger dispara automaticamente)
INSERT INTO Acesso_RU (id_usuario, id_catraca, data_hora_entrada)
VALUES (1, 1, NOW());

-- Ver saldo depois + tipo_refeicao
SELECT u.saldo_atual, a.tipo_refeicao, a.valor_cobrado
FROM Usuario_RU u
JOIN Acesso_RU a ON u.id_usuario = a.id_usuario
WHERE u.id_usuario = 1
ORDER BY a.id_acesso DESC LIMIT 1;
```

**Trigger 2**: `trg_atualizar_saldo_apos_recarga` — `AFTER INSERT` atualiza saldo automaticamente.

### 8:00 → 8:30 — Procedure: `Gerar_Sorteio_FastPass`

```sql
CREATE PROCEDURE Gerar_Sorteio_FastPass (
    IN p_horario_inicio DATETIME, IN p_horario_fim DATETIME,
    IN p_vagas INT, IN p_id_refeitorio INT
)
BEGIN
    -- 1. Registra o sorteio
    -- 2. Sorteio ponderado: quanto mais dias sem FastPass, maior a chance
    INSERT INTO Temp_Ganhadores (id_usuario)
    SELECT id_usuario FROM Estudante
    ORDER BY POW(RAND(), 1.0 / (dias_sem_fastpass + 1)) DESC  -- ← Ponderação!
    LIMIT p_vagas;
    -- 3. Emite bilhetes
    -- 4. Atualiza pesos: ganhadores → 0, não-ganhadores → +1
END;
```

### 8:30 → 9:00 — Procedure + View

**Procedure 2**: `Executar_Sorteio_FastPass` — sorteio apenas entre inscritos, com validações (não repetir, ter inscritos, horário já passou)

**View**: `vw_relatorio_fluxo_ru`
```sql
CREATE OR REPLACE VIEW vw_relatorio_fluxo_ru AS
SELECT r.nome_refeitorio, r.tipo_servico,
       COUNT(a.id_acesso) AS total_pessoas_atendidas,
       SUM(a.valor_cobrado) AS faturamento_diario
FROM Refeitorio r
JOIN Catraca c ON r.id_refeitorio = c.id_refeitorio
JOIN Acesso_RU a ON c.id_catraca = a.id_catraca
WHERE DATE(a.data_hora_entrada) = CURDATE()
GROUP BY r.id_refeitorio;
```

---

## ⏱ SEGMENTO 4: Frontend Funcionando (3 min)

### 9:00 → 9:30 — Iniciar servidor

```bash
cd backend
python -m venv .venv 2>nul || python3 -m venv .venv
.venv\Scripts\activate
pip install -q fastapi uvicorn python-dotenv mysql-connector-python python-multipart
uvicorn main:app --reload
```

Abra `http://localhost:8000/?usuario_id=1`

### 9:30 → 10:30 — Demonstração do Frontend (navegar rapidamente)
1. **Perfil**: Nome, e-mail, categoria, saldo, foto (se tiver)
2. **Saldo**: Mostrar valor atual, clicar em "Recarregar" → escolher valor → Confirmar → saldo atualiza
3. **Extrato**: Ver entradas (recargas) e saídas (acessos) com cores verde/vermelho
4. **FastPass**: Clicar em "Solicitar FastPass" → ver dias sem FastPass e chances → inscrever
5. **Admin**: Ver relatório de fluxo por refeitório (dados da view)

### 10:30 → 11:00 — Catraca Client (CLI)
```bash
cd catraca_client
python main.py
```
- ID da Catraca: `1` (Refeitório 1 - RU Central Darcy)
- ID do usuário: `1` → mostra saldo anterior, valor cobrado, saldo atual, tipo refeição
- ID do usuário inválido: mostra erro

### 11:00 → 11:30 — Upload de foto (BLOB)
- No frontend, clicar no perfil → "Alterar foto" → selecionar imagem PNG/JPEG
- A imagem é enviada via `POST /api/usuarios/{id}/foto` como `multipart/form-data`
- Armazenada como `BLOB` no MySQL e retornada como `base64` no JSON
- Mostrar no DB:
  ```sql
  SELECT id_usuario, LENGTH(foto_perfil) AS bytes FROM Usuario_RU WHERE foto_perfil IS NOT NULL LIMIT 5;
  ```

### 11:30 → 12:00 — Encerramento + Código-fonte
- Mostrar estrutura do repositório rapidamente
- Concluir com perguntas

---

## ⏱ RESUMO DE TEMPO

| Seg | Tópico | Duração |
|-----|--------|---------|
| 1 | Contexto + DB (tabelas, dados, relações, BLOB) | 4 min |
| 2 | CRUD + Persistência (código e funcionamento) | 4 min |
| 3 | Trigger + Procedure + View | 3 min |
| 4 | Frontend + Catraca + Demonstração prática | 4 min |
| | **Total** | **15 min** |

---

## 📋 CHECKLIST DE APRESENTAÇÃO

- [ ] Banco MySQL rodando com `Ru_Express` populado
- [ ] Terminais preparados (2 abas):
  - Terminal 1: `uvicorn backend.main:app --reload`
  - Terminal 2: `cd catraca_client && python main.py`
- [ ] SQL scripts prontos para copiar/colar (mostrar tabelas, dados, trigger, procedure)
- [ ] Navegador aberto em `http://localhost:8000/?usuario_id=1`
- [ ] mR.pdf / mER.pdf prontos para abrir
- [ ] Código-fonte aberto nos pontos certos (db.py, main.py, ru_express.sql)