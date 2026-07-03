from fastapi import FastAPI, Depends, Query, HTTPException, status
from contextlib import asynccontextmanager
from db import init_db, get_db

from queries import QueryUser, QueryBalance, QueryAcessos, QueryBilheteBase, QueryRelatorioFluxo, QueryAdminUsuariosBase

VAGASFASTPASS = 20

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/")
def root():
    return {"Hello": "World!"}

@app.get("/db")
def db(db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM Campus")
    result = cursor.fetchall()
    cursor.close()
    return result

# ─── Perfil ────────────────────────────────────────────────────────────────

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

# ─── Acessos ────────────────────────────────────────────────────────────────

@app.get("/api/accesses")
def accesses(usuario_id: int = Query(), limit: int = Query(20), offset: int = Query(0), db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    cursor.execute(QueryAcessos, (usuario_id, limit, offset))
    rows = cursor.fetchall()
    cursor.close()
    return {"accesses": rows}

# ─── Admin ────────────────────────────────────────────────────────────────

@app.get("/api/admin/relatorio-fluxo")
def relatorio_fluxo(db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    cursor.execute(QueryRelatorioFluxo)
    rows = cursor.fetchall()
    cursor.close()
    return {"relatorio": rows}


@app.get("/api/admin/usuarios")
def admin_usuarios(categoria: str = Query(None), busca: str = Query(None), db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)

    # Para evitar erro com o BLOB, buscamos colunas explicitamente.
    sql = QueryAdminUsuariosBase
    params = []

    if categoria:
        sql += " AND id_categoria = %s"
        params.append(categoria)

    if busca:
        sql += " AND (nome LIKE %s OR email LIKE %s)"
        like = f"%{busca}%"
        params.extend([like, like])

    sql += " ORDER BY nome"

    cursor.execute(sql, params or None)
    cursor.execute(sql, tuple(params) if params else None)
    rows = cursor.fetchall()
    cursor.close()
    return {"usuarios": rows}


# ─── FastPass ────────────────────────────────────────────────────────────────

@app.get("/api/fastpass/meus-bilhetes")
def meus_bilhetes(usuario_id: int = Query(), status: str = Query(None), db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    
    # Inicia com a string importada
    sql = QueryBilheteBase
    params = [usuario_id]

    if status:
        sql += " AND b.status_uso = %s"
        params.append(status)

    sql += " ORDER BY b.horario_inicio DESC"
    
    cursor.execute(sql, tuple(params))
    rows = cursor.fetchall()
    cursor.close()
    return {"bilhetes": rows}

from pydantic import BaseModel
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
    cursor.execute("SELECT id_usuario FROM Estudante WHERE id_usuario = %s", (body.usuario_id,))
    if not cursor.fetchone():
        cursor.close()
        raise HTTPException(status_code=403, detail="Apenas estudantes podem participar.")

    # validacao sorteio na msm faixa
    cursor.execute("""
        SELECT id_sorteio FROM Sorteio_Diario 
        WHERE horario_inicio = %s AND horario_fim = %s
    """, (body.horario_inicio, body.horario_fim))
    
    if cursor.fetchone():
        cursor.close()
        raise HTTPException(status_code=409, detail="Sorteio já existente para esta faixa.")

    # executa a Procedure com commit/rollback
    try:
        cursor.callproc("Gerar_Sorteio_FastPass", (body.horario_inicio, body.horario_fim, body.vagas, body.refeitorio_id))
        db.commit()
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

    cursor.close()
    return {"status": "sorteio realizado com sucesso"}