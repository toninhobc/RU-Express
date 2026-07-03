from fastapi import FastAPI, Depends, Query
from contextlib import asynccontextmanager
from db import init_db, get_db


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
    from queries import QueryUser
    # Query 1
    cursor.excute(QueryUser)
    cursor.execute("SELECT * FROM Usuario_RU WHERE id_usuario = %s", (usuario_id,))
    usuario = cursor.fetchone()
    cursor.close()

    if not usuario:
        return {"error": "Usuário não encontrado"}, 404

    return {"usuario": usuario}


# ─── Saldo ────────────────────────────────────────────────────────────────

@app.get("/api/balance")
def balance(usuario_id: int = Query(), db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    # TODO: escreva seu SELECT para retornar o saldo_atual
    cursor.execute("SELECT saldo_atual FROM Usuario_RU WHERE id_usuario = %s", (usuario_id,))
    row = cursor.fetchone()
    cursor.close()

    if not row:
        return {"error": "Usuário não encontrado"}, 404

    return {"saldo_atual": row["saldo_atual"]}


# ─── Acessos ────────────────────────────────────────────────────────────────

@app.get("/api/accesses")
def accesses(usuario_id: int = Query(), limit: int = Query(20), offset: int = Query(0), db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    # TODO: escreva seu SELECT com JOINs (Catraca, Refeitorio) e ordenação
    cursor.execute(
        "SELECT * FROM Acesso_RU WHERE id_usuario = %s ORDER BY data_hora_entrada DESC LIMIT %s OFFSET %s",
        (usuario_id, limit, offset),
    )
    rows = cursor.fetchall()
    cursor.close()
    return {"accesses": rows}


# ─── Admin ────────────────────────────────────────────────────────────────

@app.get("/api/admin/relatorio-fluxo")
def relatorio_fluxo(db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    # TODO: escreva seu SELECT usando a view vw_relatorio_fluxo_ru
    cursor.execute("SELECT * FROM vw_relatorio_fluxo_ru")
    rows = cursor.fetchall()
    cursor.close()
    return {"relatorio": rows}


@app.get("/api/admin/usuarios")
def admin_usuarios(categoria: str = Query(None), busca: str = Query(None), db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    # TODO: escreva seu SELECT com filtros opcionais por categoria e busca
    sql = "SELECT * FROM Usuario_RU WHERE 1=1"
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
    rows = cursor.fetchall()
    cursor.close()
    return {"usuarios": rows}


# ─── FastPass ────────────────────────────────────────────────────────────────

@app.get("/api/fastpass/meus-bilhetes")
def meus_bilhetes(usuario_id: int = Query(), status: str = Query(None), db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    # TODO: escreva seu SELECT com JOINs (Refeitorio, Sorteio_Diario) e filtro opcional por status
    sql = "SELECT * FROM Bilhete_FastPass WHERE id_usuario = %s"
    params: list = [usuario_id]

    if status:
        sql += " AND status_uso = %s"
        params.append(status)

    sql += " ORDER BY horario_inicio DESC"
    cursor.execute(sql, params)
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

@app.post("/api/fastpass/solicitar")
def solicitar_fastpass(body: FastPassRequest, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    # TODO: validar perfil (só Estudante pode participar)
    # TODO: validar se já existe sorteio nessa faixa
    cursor.callproc("Gerar_Sorteio_FastPass", (body.horario_inicio, body.horario_fim, body.vagas, body.refeitorio_id))
    cursor.close()
    return {"status": "sorteio realizado"}, 201
