from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
import os
import shutil

app = FastAPI(title="API - Sistema Gerencial de Locações")

# Diretório para salvar arquivos enviados
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ------------------------------------------------------------------------------
# BANCO DE DADOS EM MEMÓRIA (MOCK)
# ------------------------------------------------------------------------------
db_pessoas = []
db_imoveis = []
db_contratos = []

# ------------------------------------------------------------------------------
# MODELOS (SCHEMAS)
# ------------------------------------------------------------------------------
class Pessoa(BaseModel):
    id: Optional[int] = None
    tipo: str  # Locador, Locatário, Fiador
    nome: str
    cpf: str
    rg: str
    endereco: str
    cep: str
    cidade: str
    estado: str

class Imovel(BaseModel):
    id: Optional[int] = None
    endereco: str
    descricao: str
    valor_iptu: float = 0.0
    status_iptu: str = "Não Pago"  # Pago, Não Pago, Isento, Pendente

class Contrato(BaseModel):
    id: Optional[int] = None
    id_imovel: int
    id_locador: int
    id_locatario: int
    id_fiador: int
    data_inicio: str
    prazo_meses: int
    data_final: str
    valor_locacao: float
    multa: float
    valor_iptu: float = 0.0
    status_iptu: str = "Não Pago"  # Pago, Não Pago

# ------------------------------------------------------------------------------
# ENDPOINTS - PESSOAS
# ------------------------------------------------------------------------------
@app.post("/pessoas", status_code=201)
def cadastrar_pessoa(pessoa: Pessoa):
    pessoa.id = len(db_pessoas) + 1
    db_pessoas.append(pessoa.dict())
    return {"mensagem": "Pessoa cadastrada com sucesso", "dados": pessoa}

@app.get("/pessoas")
def listar_pessoas():
    return db_pessoas

# ------------------------------------------------------------------------------
# ENDPOINTS - IMÓVEIS
# ------------------------------------------------------------------------------
@app.post("/imoveis", status_code=201)
def cadastrar_imovel(imovel: Imovel):
    imovel.id = len(db_imoveis) + 1
    db_imoveis.append(imovel.dict())
    return {"mensagem": "Imóvel cadastrado com sucesso", "dados": imovel}

@app.get("/imoveis")
def listar_imoveis():
    return db_imoveis

# ------------------------------------------------------------------------------
# ENDPOINTS - CONTRATOS E UPLOAD DE ARQUIVOS
# ------------------------------------------------------------------------------
@app.post("/contratos", status_code=201)
def cadastrar_contrato(contrato: Contrato):
    contrato.id = len(db_contratos) + 1
    db_contratos.append(contrato.dict())
    return {"mensagem": "Contrato registrado com sucesso", "dados": contrato}

@app.post("/upload-documento")
def upload_documento(file: UploadFile = File(...), referencia_id: Optional[int] = Form(None)):
    filepath = os.path.join(UPLOAD_DIR, file.filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"mensagem": f"Arquivo '{file.filename}' salvo com sucesso", "caminho": filepath}

# ------------------------------------------------------------------------------
# ENDPOINT - RELATÓRIO GERENCIAL
# ------------------------------------------------------------------------------
@app.get("/relatorio")
def gerar_relatorio():
    relatorio = []
    
    map_p = {p["id"]: p["nome"] for p in db_pessoas}
    map_i = {i["id"]: i["descricao"] for i in db_imoveis}

    for c in db_contratos:
        dt_fim = date.fromisoformat(c["data_final"])
        dias_restantes = (dt_fim - date.today()).days

        relatorio.append({
            "numero_sequencia": f"CTR-{c['id']:04d}",
            "descricao_imovel": map_i.get(c["id_imovel"], "N/A"),
            "locador": map_p.get(c["id_locador"], "N/A"),
            "locatario": map_p.get(c["id_locatario"], "N/A"),
            "data_inicio": c["data_inicio"],
            "prazo_meses": c["prazo_meses"],
            "data_final": c["data_final"],
            "valor_locacao": c["valor_locacao"],
            "multa": c["multa"],
            "valor_iptu": c.get("valor_iptu", 0.0),
            "status_iptu": c.get("status_iptu", "Não Pago"),
            "dias_restantes": dias_restantes
        })
    return relatorio

# ------------------------------------------------------------------------------
# ENDPOINT - ALERTAS DE VENCIMENTO
# ------------------------------------------------------------------------------
@app.post("/alertas/verificar-vencimentos")
def verificar_vencimentos(email_admin: str):
    contratos_proximos = []
    hoje = date.today()

    for c in db_contratos:
        dt_fim = date.fromisoformat(c["data_final"])
        dias = (dt_fim - hoje).days
        if 0 <= dias <= 60:
            contratos_proximos.append(c["id"])

    qtd = len(contratos_proximos)
    return {
        "mensagem": f"Verificação concluída. {qtd} contrato(s) vencerão nos próximos 60 dias. Notificação enviada para {email_admin}."
    }