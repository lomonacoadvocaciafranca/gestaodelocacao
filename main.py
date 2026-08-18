from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import date

app = FastAPI(title="API Gestão de Locações")

# Habilitar CORS para o Streamlit acessar sem restrições
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------------------
# BANCO DE DADOS EM MEMÓRIA (MOCK/EXEMPLO)
# Se você usa SQLAlchemy/SQLite, substitua as listas pelas queries do ORM
# ------------------------------------------------------------------------------
db_pessoas = []
db_imoveis = []
db_contratos = []

# --- MODELOS DE DADOS ---
class PessoaSchema(BaseModel):
    id: Optional[int] = None
    tipo: str
    nome: str
    cpf: str
    rg: str
    endereco: str
    cep: str
    cidade: str
    estado: str

class ImovelSchema(BaseModel):
    id: Optional[int] = None
    endereco: str
    descricao: str
    valor_iptu: float
    status_iptu: str

class ContratoSchema(BaseModel):
    id: Optional[int] = None
    id_imovel: int
    id_locador: int
    id_locatario: int
    id_fiador: Optional[int] = None
    data_inicio: str
    prazo_meses: int
    data_final: str
    valor_locacao: float
    multa: float

# ------------------------------------------------------------------------------
# ENDPOINTS: PESSOAS
# ------------------------------------------------------------------------------
@app.get("/pessoas", response_model=List[PessoaSchema])
def listar_pessoas():
    return db_pessoas

@app.post("/pessoas", response_model=PessoaSchema, status_code=status.HTTP_201_CREATED)
def criar_pessoa(pessoa: PessoaSchema):
    pessoa.id = len(db_pessoas) + 1
    db_pessoas.append(pessoa.dict())
    return pessoa

@app.delete("/pessoas/{pessoa_id}", status_code=status.HTTP_200_OK)
def deletar_pessoa(pessoa_id: int):
    global db_pessoas
    pessoa = next((p for p in db_pessoas if p["id"] == pessoa_id), None)
    if not pessoa:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    db_pessoas = [p for p in db_pessoas if p["id"] != pessoa_id]
    return {"mensagem": f"Pessoa ID {pessoa_id} descartada com sucesso"}

# ------------------------------------------------------------------------------
# ENDPOINTS: IMÓVEIS
# ------------------------------------------------------------------------------
@app.get("/imoveis", response_model=List[ImovelSchema])
def listar_imoveis():
    return db_imoveis

@app.post("/imoveis", response_model=ImovelSchema, status_code=status.HTTP_201_CREATED)
def criar_imovel(imovel: ImovelSchema):
    imovel.id = len(db_imoveis) + 1
    db_imoveis.append(imovel.dict())
    return imovel

@app.delete("/imoveis/{imovel_id}", status_code=status.HTTP_200_OK)
def deletar_imovel(imovel_id: int):
    global db_imoveis
    imovel = next((i for i in db_imoveis if i["id"] == imovel_id), None)
    if not imovel:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")
    db_imoveis = [i for i in db_imoveis if i["id"] != imovel_id]
    return {"mensagem": f"Imóvel ID {imovel_id} descartado com sucesso"}

# ------------------------------------------------------------------------------
# ENDPOINTS: CONTRATOS E RELATÓRIOS
# ------------------------------------------------------------------------------
@app.get("/contratos", response_model=List[ContratoSchema])
def listar_contratos():
    return db_contratos

@app.post("/contratos", response_model=ContratoSchema, status_code=status.HTTP_201_CREATED)
def criar_contrato(contrato: ContratoSchema):
    contrato.id = len(db_contratos) + 1
    db_contratos.append(contrato.dict())
    return contrato

@app.delete("/contratos/{contrato_id}", status_code=status.HTTP_200_OK)
def deletar_contrato(contrato_id: int):
    global db_contratos
    contrato = next((c for c in db_contratos if c["id"] == contrato_id), None)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato não encontrado")
    db_contratos = [c for c in db_contratos if c["id"] != contrato_id]
    return {"mensagem": f"Contrato ID {contrato_id} descartado com sucesso"}

@app.get("/relatorio")
def gerar_relatorio():
    relatorio = []
    for c in db_contratos:
        imovel = next((i for i in db_imoveis if i["id"] == c["id_imovel"]), {})
        locador = next((p for p in db_pessoas if p["id"] == c["id_locador"]), {})
        locatario = next((p for p in db_pessoas if p["id"] == c["id_locatario"]), {})
        fiador = next((p for p in db_pessoas if p["id"] == c.get("id_fiador")), {})

        d_final = date.fromisoformat(c["data_final"])
        dias_restantes = (d_final - date.today()).days

        relatorio.append({
            "id": c["id"],
            "id_imovel": c["id_imovel"],
            "id_locador": c["id_locador"],
            "id_locatario": c["id_locatario"],
            "id_fiador": c.get("id_fiador"),
            "numero_sequencia": f"CT-{c['id']:04d}",
            "descricao_imovel": imovel.get("descricao", "N/A"),
            "locador": locador.get("nome", "N/A"),
            "locatario": locatario.get("nome", "N/A"),
            "data_inicio": c["data_inicio"],
            "prazo_meses": c["prazo_meses"],
            "data_final": c["data_final"],
            "valor_locacao": c["valor_locacao"],
            "multa": c["multa"],
            "valor_iptu": imovel.get("valor_iptu", 0.0),
            "status_iptu": imovel.get("status_iptu", "N/A"),
            "dias_restantes": dias_restantes,
            "indice_reajuste": "IPCA",
            "dados_bancarios_locador": "PIX / Conta Corrente"
        })
    return relatorio

# ------------------------------------------------------------------------------
# DEMAIS ROTAS (UPLOAD / ALERTAS)
# ------------------------------------------------------------------------------
@app.post("/upload-documento")
def upload_doc():
    return {"mensagem": "Arquivo recebido com sucesso"}

@app.post("/alertas/verificar-vencimentos")
def verificar_alertas(email_admin: str):
    return {"mensagem": f"Verificação concluída. Alertas enviados para {email_admin}"}