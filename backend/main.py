from datetime import datetime

import mysql.connector
from fastapi import FastAPI, Depends, Query, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field

from db import init_db, get_db

from queries import (
    QueryUser,
    QueryBalance,
    QueryAcessos,
    QueryBilheteBase,
    QueryRefeitorios,
    QueryRechargeInsert,
    QuerySaldoAfterRecharge,
    QueryRelatorioFluxo,
    QueryAdminUsuariosBase,
    QueryUsuarioInsert,
    QueryUsuarioExists,
    QueryUsuarioDelete,
)

VAGASFASTPASS = 20


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Usuários (CRUD) ─────────────────────────────────────────────────────────


@app.get("/api/profile")
def profile(usuario_id: int = Query(), db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    cursor.execute(QueryUser, (usuario_id,))
    usuario = cursor.fetchone()
    cursor.close()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Limpa os nulos vindos do LEFT JOIN para deixar o JSON bonito
    usuario_limpo = {k: v for k, v in usuario.items() if v is not None}
    return {"usuario": usuario_limpo}


class UsuarioCreate(BaseModel):
    nome: str
    email: str
    prioridade_legal: bool = False
    id_categoria: int


class UsuarioUpdate(BaseModel):
    nome: str | None = None
    email: str | None = None
    prioridade_legal: bool | None = None
    id_categoria: int | None = None


@app.post("/api/usuarios", status_code=status.HTTP_201_CREATED)
def criar_usuario(body: UsuarioCreate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            QueryUsuarioInsert,
            (body.nome, body.email, body.prioridade_legal, body.id_categoria),
        )
        db.commit()
    except mysql.connector.Error as e:
        db.rollback()
        cursor.close()
        if e.errno == 1062:  # e-mail duplicado (UNIQUE)
            raise HTTPException(status_code=409, detail="E-mail já cadastrado.")
        if e.errno == 1452:  # id_categoria inexistente (FK)
            raise HTTPException(status_code=400, detail="Categoria inexistente.")
        raise

    novo_id = cursor.lastrowid
    cursor.close()
    return {"id_usuario": novo_id}


@app.put("/api/usuarios/{usuario_id}")
def atualizar_usuario(usuario_id: int, body: UsuarioUpdate, db=Depends(get_db)):
    # Atualiza só os campos informados (not None)
    campos = body.model_dump(exclude_none=True)
    if not campos:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

    cursor = db.cursor()
    cursor.execute(QueryUsuarioExists, (usuario_id,))
    if not cursor.fetchone():
        cursor.close()
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Os nomes das colunas vêm do modelo (fixos), os valores vão parametrizados
    set_clause = ", ".join(f"{col} = %s" for col in campos)
    params = list(campos.values()) + [usuario_id]
    cursor.execute(f"UPDATE Usuario_RU SET {set_clause} WHERE id_usuario = %s", params)
    db.commit()
    cursor.close()
    return {"status": "atualizado"}


@app.delete("/api/usuarios/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_usuario(usuario_id: int, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute(QueryUsuarioExists, (usuario_id,))
    if not cursor.fetchone():
        cursor.close()
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    try:
        cursor.execute(QueryUsuarioDelete, (usuario_id,))
        db.commit()
    except mysql.connector.Error as e:
        db.rollback()
        cursor.close()
        # 1451 = FK: usuário tem histórico (recarga/acesso/bilhete) que não cascateia
        if e.errno == 1451:
            raise HTTPException(
                status_code=409,
                detail="Não é possível excluir: usuário possui histórico (recargas/acessos/bilhetes).",
            )
        raise
    cursor.close()


# ─── Saldo ────────────────────────────────────────────────────────────────


@app.get("/api/balance")
def balance(usuario_id: int = Query(), db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    cursor.execute(QueryBalance, (usuario_id,))
    saldo = cursor.fetchone()
    cursor.close()

    if not saldo:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return {"saldo": saldo}


# ─── Refeitórios (para dropdowns no frontend) ──────────────────────────────


@app.get("/api/refeitorios")
def listar_refeitorios(db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    cursor.execute(QueryRefeitorios)
    rows = cursor.fetchall()
    cursor.close()
    return {"refeitorios": rows}


class RechargeRequest(BaseModel):
    usuario_id: int
    valor: float = Field(gt=0)
    metodo_pagamento: str


@app.post("/api/balance/recharge", status_code=status.HTTP_201_CREATED)
def recharge_balance(body: RechargeRequest, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    agora = datetime.now()
    cursor.execute(
        QueryRechargeInsert, (body.valor, agora, body.metodo_pagamento, body.usuario_id)
    )
    db.commit()

    cursor.execute(QuerySaldoAfterRecharge, (body.usuario_id,))
    row = cursor.fetchone()
    cursor.close()
    if not row:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return {"saldo_atual": float(row["saldo_atual"])}


# ─── Acessos ────────────────────────────────────────────────────────────────


@app.get("/api/accesses")
def accesses(
    usuario_id: int = Query(),
    limit: int = Query(20),
    offset: int = Query(0),
    db=Depends(get_db),
):
    cursor = db.cursor(dictionary=True)
    cursor.execute(QueryAcessos, (usuario_id, limit, offset))
    rows = cursor.fetchall()
    cursor.close()
    return {"accesses": rows}


@app.post("/api/accesses")
def novo_acesso(usuario_id: int = Query(), catraca: int = Query()):
    pass


# ─── Admin ────────────────────────────────────────────────────────────────


@app.get("/api/admin/relatorio-fluxo")
def relatorio_fluxo(db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    cursor.execute(QueryRelatorioFluxo)
    rows = cursor.fetchall()
    cursor.close()
    return {"relatorio": rows}


@app.get("/api/admin/usuarios")
def admin_usuarios(
    categoria: str = Query(None), busca: str = Query(None), db=Depends(get_db)
):
    cursor = db.cursor(dictionary=True)

    # Base sem foto_perfil (BLOB) para não quebrar a serialização JSON
    sql = QueryAdminUsuariosBase
    params: list = []

    if categoria:
        sql += " AND id_categoria = %s"
        params.append(categoria)

    if busca:
        sql += " AND (nome LIKE %s OR email LIKE %s)"
        like = f"%{busca}%"
        params.extend([like, like])

    sql += " ORDER BY nome"
    cursor.execute(sql, tuple(params) if params else None)
    rows = cursor.fetchall()
    cursor.close()
    return {"usuarios": rows}


# ─── FastPass ────────────────────────────────────────────────────────────────


@app.get("/api/fastpass/meus-bilhetes")
def meus_bilhetes(
    usuario_id: int = Query(), status_uso: str = Query(None), db=Depends(get_db)
):
    cursor = db.cursor(dictionary=True)

    # Inicia com a string importada
    sql = QueryBilheteBase
    params: list = [usuario_id]

    if status_uso:
        sql += " AND b.status_uso = %s"
        params.append(status_uso)

    sql += " ORDER BY b.horario_inicio DESC"

    cursor.execute(sql, tuple(params))
    rows = cursor.fetchall()
    cursor.close()
    return {"bilhetes": rows}


class FastPassRequest(BaseModel):
    usuario_id: int
    refeitorio_id: int
    horario_inicio: str
    horario_fim: str
    vagas: int = VAGASFASTPASS


@app.post("/api/fastpass/solicitar", status_code=status.HTTP_201_CREATED)
def solicitar_fastpass(body: FastPassRequest, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)

    # validacao estudante
    cursor.execute(
        "SELECT id_usuario FROM Estudante WHERE id_usuario = %s", (body.usuario_id,)
    )
    if not cursor.fetchone():
        cursor.close()
        raise HTTPException(
            status_code=403, detail="Apenas estudantes podem participar."
        )

    # validacao sorteio na msm faixa
    cursor.execute(
        """
        SELECT id_sorteio FROM Sorteio_Diario 
        WHERE horario_inicio = %s AND horario_fim = %s
    """,
        (body.horario_inicio, body.horario_fim),
    )

    if cursor.fetchone():
        cursor.close()
        raise HTTPException(
            status_code=409, detail="Sorteio já existente para esta faixa."
        )

    # executa a Procedure com commit/rollback
    try:
        cursor.callproc(
            "Gerar_Sorteio_FastPass",
            (body.horario_inicio, body.horario_fim, body.vagas, body.refeitorio_id),
        )
        db.commit()
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

    cursor.close()
    return {"status": "sorteio realizado com sucesso"}
