from datetime import datetime
import os

import base64
import mysql.connector

from fastapi import FastAPI, Depends, Query, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi import UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field

from db import init_db, get_db
from queries import (
    QueryUser,
    QueryBalance,
    QueryAcessos,
    QueryExtrato,
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

# ─── Serve Frontend ─────────────────────────────────────────────────────────

frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/static", StaticFiles(directory=frontend_path), name="static")


@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    with open(os.path.join(frontend_path, "mock_preview.html"), encoding="utf-8") as f:
        return f.read()


# ─── Usuários (CRUD) ─────────────────────────────────────────────────────────


@app.get("/api/profile")
def profile(usuario_id: int = Query(), db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    cursor.execute(QueryUser, (usuario_id,))
    usuario = cursor.fetchone()
    cursor.close()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    foto_bytes = usuario.pop("foto_perfil", None)

    # Limpa os nulos vindos do LEFT JOIN para deixar o JSON bonito
    usuario_limpo = {k: v for k, v in usuario.items() if v is not None}
    if "prioridade_legal" in usuario_limpo:
        usuario_limpo["prioridade_legal"] = bool(usuario_limpo["prioridade_legal"])

    usuario_limpo["tem_foto_perfil"] = foto_bytes is not None
    if foto_bytes:
        usuario_limpo["foto_perfil_base64"] = base64.b64encode(foto_bytes).decode(
            "ascii"
        )

    return {"usuario": usuario_limpo}


MAX_FOTO_BYTES = 2 * 1024 * 1024  # 2 MB
TIPOS_PERMITIDOS = {"image/jpeg", "image/png", "image/webp"}


@app.post("/api/usuarios/{usuario_id}/foto")
async def upload_foto(
    usuario_id: int, foto: UploadFile = File(...), db=Depends(get_db)
):
    if foto.content_type not in TIPOS_PERMITIDOS:
        raise HTTPException(
            status_code=400,
            detail="Formato inválido. Envie JPEG, PNG ou WEBP.",
        )

    conteudo = await foto.read()

    if len(conteudo) > MAX_FOTO_BYTES:
        raise HTTPException(status_code=400, detail="Arquivo maior que 2MB.")

    cursor = db.cursor()
    cursor.execute(QueryUsuarioExists, (usuario_id,))
    if not cursor.fetchone():
        cursor.close()
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    cursor.execute(
        "UPDATE Usuario_RU SET foto_perfil = %s WHERE id_usuario = %s",
        (conteudo, usuario_id),
    )
    db.commit()
    cursor.close()
    return {"status": "foto atualizada"}


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
    cursor.execute(QueryBalance, (usuario_id,))
    usuario_existe = cursor.fetchone()
    if not usuario_existe:
        cursor.close()
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    cursor.execute(QueryAcessos, (usuario_id, limit, offset))
    rows = cursor.fetchall()
    cursor.close()
    return {"accesses": rows}


@app.get("/api/extrato")
def extrato(
    usuario_id: int = Query(),
    limit: int = Query(20),
    offset: int = Query(0),
    db=Depends(get_db),
):
    cursor = db.cursor(dictionary=True)

    cursor.execute(QueryBalance, (usuario_id,))
    if not cursor.fetchone():
        cursor.close()
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    cursor.execute(QueryExtrato, (usuario_id, usuario_id, limit, offset))
    rows = cursor.fetchall()
    cursor.close()
    return {"extrato": rows}


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


@app.post("/api/fastpass/solicitar")
def solicitar_fastpass(body: FastPassRequest, db=Depends(get_db)):
    # Só estudantes participam do sorteio
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT id_usuario FROM Estudante WHERE id_usuario = %s", (body.usuario_id,)
    )
    if not cursor.fetchone():
        cursor.close()
        raise HTTPException(
            status_code=403, detail="Apenas estudantes podem participar."
        )

    cursor.execute(
        "SELECT id_sorteio FROM Sorteio_Diario WHERE horario_inicio = %s AND horario_fim = %s",
        (body.horario_inicio, body.horario_fim),
    )
    ja_sorteado = cursor.fetchone()
    cursor.close()

    if not ja_sorteado:
        cursor = db.cursor()
        try:
            cursor.callproc(
                "Gerar_Sorteio_FastPass",
                (
                    body.horario_inicio,
                    body.horario_fim,
                    VAGASFASTPASS,
                    body.refeitorio_id,
                ),
            )
            db.commit()
        except Exception as e:
            db.rollback()
            cursor.close()
            raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
        cursor.close()

    cursor = db.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT b.id_bilhete, b.horario_inicio, b.horario_fim, b.status_uso, b.id_sorteio
        FROM Bilhete_FastPass b
        JOIN Sorteio_Diario s ON b.id_sorteio = s.id_sorteio
        WHERE s.horario_inicio = %s AND s.horario_fim = %s AND b.id_usuario = %s
        """,
        (body.horario_inicio, body.horario_fim, body.usuario_id),
    )
    bilhete = cursor.fetchone()
    cursor.close()

    if bilhete:
        return {"contemplado": True, "bilhete": bilhete}
    return {
        "contemplado": False,
        "mensagem": "Não foi dessa vez. Suas chances aumentam no próximo sorteio.",
    }


class UsarFastPassRequest(BaseModel):
    usuario_id: int
    id_bilhete: int


@app.post("/api/fastpass/usar")
def usar_fastpass(body: UsarFastPassRequest, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT id_usuario, status_uso FROM Bilhete_FastPass WHERE id_bilhete = %s",
        (body.id_bilhete,),
    )
    bilhete = cursor.fetchone()

    if not bilhete:
        cursor.close()
        raise HTTPException(status_code=404, detail="Bilhete não encontrado")

    # Só o dono pode usar o próprio bilhete
    if bilhete["id_usuario"] != body.usuario_id:
        cursor.close()
        raise HTTPException(status_code=403, detail="Este bilhete não é seu.")

    # Só bilhete pendente pode ser usado (não Utilizado nem Expirado)
    if bilhete["status_uso"] != "Pendente":
        cursor.close()
        raise HTTPException(
            status_code=409,
            detail=f"Bilhete não está disponível (status: {bilhete['status_uso']}).",
        )

    cursor.execute(
        "UPDATE Bilhete_FastPass SET status_uso = 'Utilizado' WHERE id_bilhete = %s",
        (body.id_bilhete,),
    )
    db.commit()
    cursor.close()
    return {"status": "utilizado"}
