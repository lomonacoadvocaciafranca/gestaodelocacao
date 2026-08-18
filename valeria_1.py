import streamlit as st
import requests
import pandas as pd
from datetime import date, timedelta
import io
from typing import Optional, List, Dict, Any

# Importando o módulo separado de mensagens
from modulo_mensagens import renderizar_modulo_mensagens

# --- TENTATIVA DE IMPORTAÇÃO DO REPORTLAB PARA PDF ---
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestão de Locações", page_icon="🏢", layout="wide")

API_URL = "http://127.0.0.1:8000"

# Ocultar elementos da interface do Streamlit na hora de imprimir
st.markdown("""
<style>
@media print {
    [data-testid="stSidebar"], .stButton, header, footer { display: none !important; }
    .main .block-container { padding: 0 !important; }
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# FUNÇÕES AUXILIARES (VALIDAÇÃO DE CPF E VIA CEP)
# ------------------------------------------------------------------------------
def validar_cpf(cpf: str) -> bool:
    """Valida o número de CPF informando se os dígitos verificadores estão corretos."""
    if not cpf:
        return False
    # Remove caracteres não numéricos
    cpf_nums = ''.join(filter(str.isdigit, cpf))
    
    # Verifica se tem 11 dígitos ou se é uma sequência repetida conhecida
    if len(cpf_nums) != 11 or cpf_nums == cpf_nums[0] * 11:
        return False
        
    # Cálculo do 1º dígito verificador
    soma = sum(int(cpf_nums[i]) * (10 - i) for i in range(9))
    digito1 = (soma * 10) % 11
    if digito1 == 10:
        digito1 = 0
    if digito1 != int(cpf_nums[9]):
        return False
        
    # Cálculo do 2º dígito verificador
    soma = sum(int(cpf_nums[i]) * (11 - i) for i in range(10))
    digito2 = (soma * 10) % 11
    if digito2 == 10:
        digito2 = 0
    if digito2 != int(cpf_nums[10]):
        return False
        
    return True

def gerar_pdf_relatorio(df_dados: pd.DataFrame) -> io.BytesIO:
    """Gera um buffer de PDF com os dados do relatório financeiro."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1E3A8A'),
        spaceAfter=12
    )
    
    story.append(Paragraph("<b>Relatório Gerencial de Contratos de Locação</b>", title_style))
    story.append(Paragraph(f"Emitido em: {date.today().strftime('%d/%m/%Y')}", styles['Normal']))
    story.append(Spacer(1, 15))

    cols = list(df_dados.columns)
    data = [cols] + df_dados.astype(str).values.tolist()
    
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F3F4F6')]),
    ]))
    
    story.append(table)
    doc.build(story)
    buffer.seek(0)
    return buffer

@st.cache_data(ttl=300) 
def buscar_dados_contratos(api_url: str) -> Optional[List[Dict[str, Any]]]:
    """Busca os dados dos contratos na API com tratamento de erros."""
    try:
        res = requests.get(f"{api_url}/relatorio", timeout=10)
        res.raise_for_status() 
        return res.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de conexão com a API: {e}")
        return None
    except ValueError:
        st.error("Erro ao decodificar a resposta da API (formato JSON inválido).")
        return None

def preparar_dataframe(dados: List[Dict[str, Any]]) -> pd.DataFrame:
    """Padroniza colunas e tipagem do DataFrame recebido da API."""
    df = pd.DataFrame(dados)
    
    if df.empty:
        return df

    mapeamento_colunas = {
        "id": "ID",
        "id_imovel": "ID Imóvel",
        "id_locador": "ID Locador",
        "id_locatario": "ID Locatário",
        "id_fiador": "ID Fiador",
        "numero_sequencia": "Nº Sequência",
        "descricao_imovel": "Descrição do Imóvel",
        "locador": "Locador",
        "locatario": "Locatário",
        "data_inicio": "Data Início",
        "prazo_meses": "Prazo (Meses)",
        "data_final": "Data Final",
        "valor_locacao": "Valor (R$)",
        "multa": "Multa (R$)",
        "valor_iptu": "IPTU (R$)",
        "status_iptu": "Status IPTU",
        "dias_restantes": "Dias Restantes",
        "indice_reajuste": "Índice de Reajuste",
        "dados_bancarios_locador": "Dados Bancários (Locador)"
    }
    
    colunas_presentes = {k: v for k, v in mapeamento_colunas.items() if k in df.columns}
    df = df.rename(columns=colunas_presentes)
    
    if "Valor (R$)" in df.columns:
        df["Valor (R$)"] = pd.to_numeric(df["Valor (R$)"], errors='coerce').fillna(0.0)
    if "Dias Restantes" in df.columns:
        df["Dias Restantes"] = pd.to_numeric(df["Dias Restantes"], errors='coerce').fillna(0)

    return df

st.title("🏢 Sistema Gerencial de Locação de Imóveis")

# Navegação por Abas Principais
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "👤 Pessoas", "🏠 Imóveis", "📄 Contratos", "📊 Relatório", "📧 Alertas", "💬 Mensagens"
])

# ------------------------------------------------------------------------------
# ABA 1: PESSOAS (COM VALIDADOR DE CPF E VIA CEP)
# ------------------------------------------------------------------------------
with tab1:
    st.header("Cadastrar Pessoa (Locador, Locatário ou Fiador)")
    st.markdown("Preencha os dados abaixo. O **CPF** é validado automaticamente e o **CEP** preenche o endereço consultando a API do ViaCEP.")

    if "p_cep" not in st.session_state: st.session_state.p_cep = ""
    if "p_endereco" not in st.session_state: st.session_state.p_endereco = ""
    if "p_cidade" not in st.session_state: st.session_state.p_cidade = ""
    if "p_estado" not in st.session_state: st.session_state.p_estado = "SP"

    col1, col2 = st.columns(2)
    with col1:
        tipo = st.selectbox("Tipo de Perfil*", ["Locador", "Locatário", "Fiador"])
        nome = st.text_input("Nome Completo*")
        cpf = st.text_input("CPF* (Apenas números ou formatado)")
        
        # Feedback visual do CPF em tempo real
        if cpf:
            if validar_cpf(cpf):
                st.success("✅ CPF Válido")
            else:
                st.error("❌ CPF Inválido")

        rg = st.text_input("RG*")

    with col2:
        cep_col1, cep_col2 = st.columns([0.65, 0.35])
        with cep_col1:
            cep = st.text_input("CEP*", value=st.session_state.p_cep)
        with cep_col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔍 Buscar CEP", width="stretch"):
                cep_limpo = ''.join(filter(str.isdigit, cep))
                if len(cep_limpo) == 8:
                    try:
                        r_cep = requests.get(f"https://viacep.com.br/ws/{cep_limpo}/json/", timeout=5)
                        if r_cep.status_code == 200:
                            d_cep = r_cep.json()
                            if not d_cep.get("erro"):
                                st.session_state.p_cep = cep
                                st.session_state.p_endereco = f"{d_cep.get('logradouro', '')}, {d_cep.get('bairro', '')}"
                                st.session_state.p_cidade = d_cep.get('localidade', '')
                                st.session_state.p_estado = d_cep.get('uf', 'SP')
                                st.success("Endereço preenchido via ViaCEP!")
                                st.rerun()
                            else:
                                st.warning("CEP não encontrado.")
                        else:
                            st.error("Erro ao consultar o ViaCEP.")
                    except Exception as e:
                        st.error(f"Erro de conexão com ViaCEP: {e}")
                else:
                    st.warning("Digite um CEP válido com 8 dígitos.")

        endereco = st.text_input("Endereço Completo*", value=st.session_state.p_endereco)
        cidade = st.text_input("Cidade*", value=st.session_state.p_cidade)
        
        estados_lista = ["SP", "MG", "RJ", "PR", "SC", "RS", "GO", "DF", "ES", "BA", "CE", "PE", "OUTRO"]
        current_uf = st.session_state.p_estado if st.session_state.p_estado in estados_lista else "SP"
        estado = st.selectbox("Estado (UF)*", estados_lista, index=estados_lista.index(current_uf))

    doc_pessoa = st.file_uploader("📂 Upload de Documentos Pessoais", type=["pdf", "png", "jpg", "jpeg"])
    
    if st.button("💾 Salvar Cadastro de Pessoa", type="primary"):
        if not validar_cpf(cpf):
            st.error("❌ Não é possível salvar: o CPF informado é inválido.")
        elif not (nome and cpf and rg and endereco and cep and cidade):
            st.warning("Preencha todos os campos obrigatórios (*).")
        else:
            payload = {"tipo": tipo, "nome": nome, "cpf": cpf, "rg": rg, "endereco": endereco, "cep": cep, "cidade": cidade, "estado": estado}
            try:
                res = requests.post(f"{API_URL}/pessoas", json=payload)
                if res.status_code in [200, 201]:
                    st.success(f"{tipo} '{nome}' cadastrado(a) com sucesso!")
                    if doc_pessoa:
                        files = {"file": (doc_pessoa.name, doc_pessoa.getvalue(), doc_pessoa.type)}
                        req_upload = requests.post(f"{API_URL}/upload-documento", files=files)
                        if req_upload.status_code == 200:
                            st.info(f"Arquivo anexado no servidor com sucesso!")
                else:
                    st.error(f"Erro ao cadastrar: {res.text}")
            except Exception as e:
                st.error(f"Erro de conexão com o backend. O Uvicorn está rodando? Erro: {e}")

    st.divider()
    try:
        res_p = requests.get(f"{API_URL}/pessoas")
        if res_p.status_code == 200 and res_p.json():
            pessoas_data = res_p.json()
            st.dataframe(pd.DataFrame(pessoas_data), width="stretch")
            
            st.subheader("🗑️ Descartar Cadastro de Pessoa")
            col_del_p1, col_del_p2 = st.columns([0.8, 0.2])
            with col_del_p1:
                p_del_id = st.selectbox(
                    "Selecione a Pessoa para excluir:",
                    options=[p["id"] for p in pessoas_data],
                    format_func=lambda x: next(f"{p['nome']} (CPF: {p.get('cpf', 'N/A')})" for p in pessoas_data if p["id"] == x),
                    key="del_pessoa_select"
                )
            with col_del_p2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️ Descartar Pessoa", key="btn_del_pessoa"):
                    try:
                        res_del = requests.delete(f"{API_URL}/pessoas/{p_del_id}")
                        if res_del.status_code in [200, 204]:
                            st.success("Cadastro descartado com sucesso!")
                            st.rerun()
                        else:
                            st.error(f"Erro ao descartar: {res_del.text}")
                    except Exception as e:
                        st.error(f"Erro de conexão: {e}")
    except:
        pass

# ------------------------------------------------------------------------------
# ABA 2: IMÓVEIS
# ------------------------------------------------------------------------------
with tab2:
    st.header("Cadastrar Imóvel")
    with st.form("form_imoveis", clear_on_submit=True):
        col_imv1, col_imv2 = st.columns(2)
        with col_imv1:
            endereco_imovel = st.text_input("Endereço do Imóvel*")
            descricao_imovel = st.text_area("Descrição do Imóvel*")
        with col_imv2:
            valor_iptu_imovel = st.number_input("Valor Anual/Mensal do IPTU (R$)", min_value=0.0, step=50.0)
            status_iptu_imovel = st.selectbox("Status do IPTU", ["Pago", "Não Pago", "Isento", "Pendente"])

        doc_imovel = st.file_uploader("📂 Upload de Documentos do Imóvel", type=["pdf", "png", "jpg", "jpeg"])
        btn_salvar_imovel = st.form_submit_button("💾 Salvar Cadastro de Imóvel")

        if btn_salvar_imovel:
            if not (endereco_imovel and descricao_imovel):
                st.warning("Preencha o endereço e a descrição do imóvel.")
            else:
                payload = {"endereco": endereco_imovel, "descricao": descricao_imovel, "valor_iptu": valor_iptu_imovel, "status_iptu": status_iptu_imovel}
                try:
                    res = requests.post(f"{API_URL}/imoveis", json=payload)
                    if res.status_code in [200, 201]:
                        st.success("Imóvel cadastrado com sucesso!")
                        if doc_imovel:
                            files = {"file": (doc_imovel.name, doc_imovel.getvalue(), doc_imovel.type)}
                            requests.post(f"{API_URL}/upload-documento", files=files)
                            st.info("Documento anexado ao imóvel com sucesso!")
                    else:
                        st.error(f"Erro ao salvar imóvel: {res.text}")
                except Exception as e:
                    st.error(f"Erro de conexão: {e}")

    st.divider()
    try:
        res_i = requests.get(f"{API_URL}/imoveis")
        if res_i.status_code == 200 and res_i.json():
            imoveis_data = res_i.json()
            st.dataframe(pd.DataFrame(imoveis_data), width="stretch")
            
            st.subheader("🗑️ Descartar Cadastro de Imóvel")
            col_del_i1, col_del_i2 = st.columns([0.8, 0.2])
            with col_del_i1:
                i_del_id = st.selectbox(
                    "Selecione o Imóvel para excluir:",
                    options=[i["id"] for i in imoveis_data],
                    format_func=lambda x: next(f"{i['descricao']} - {i.get('endereco', '')}" for i in imoveis_data if i["id"] == x),
                    key="del_imovel_select"
                )
            with col_del_i2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️ Descartar Imóvel", key="btn_del_imovel"):
                    try:
                        res_del = requests.delete(f"{API_URL}/imoveis/{i_del_id}")
                        if res_del.status_code in [200, 204]:
                            st.success("Cadastro descartado com sucesso!")
                            st.rerun()
                        else:
                            st.error(f"Erro ao descartar: {res_del.text}")
                    except Exception as e:
                        st.error(f"Erro de conexão: {e}")
    except:
        pass

# ------------------------------------------------------------------------------
# ABA 3: CONTRATOS
# ------------------------------------------------------------------------------
with tab3:
    st.header("📝 Preenchimento e Geração de Contrato")
    try:
        req_p = requests.get(f"{API_URL}/pessoas")
        req_i = requests.get(f"{API_URL}/imoveis")
        
        if req_p.status_code == 200 and req_i.status_code == 200:
            pessoas = req_p.json()
            imoveis = req_i.json()
            
            locadores = [p for p in pessoas if p["tipo"] == "Locador"]
            locatarios = [p for p in pessoas if p["tipo"] == "Locatário"]
            fiadores = [p for p in pessoas if p["tipo"] == "Fiador"]

            if not imoveis or not locadores or not locatarios:
                st.warning("⚠️ Cadastre ao menos 1 Imóvel, 1 Locador e 1 Locatário nas abas anteriores para gerar um contrato.")
            else:
                with st.form("form_contrato", clear_on_submit=True):
                    imovel_id = st.selectbox("Selecione o Imóvel*", [i["id"] for i in imoveis], format_func=lambda x: next(i["descricao"] for i in imoveis if i["id"] == x))
                    locador_id = st.selectbox("Locador Responsável*", [p["id"] for p in locadores], format_func=lambda x: next(p["nome"] for p in locadores if p["id"] == x))
                    locatario_id = st.selectbox("Locatário Principal*", [p["id"] for p in locatarios], format_func=lambda x: next(p["nome"] for p in locatarios if p["id"] == x))
                    
                    opcoes_fiador = [0] + [p["id"] for p in fiadores]
                    fiador_id = st.selectbox("Fiador", opcoes_fiador, format_func=lambda x: "Sem Fiador" if x == 0 else next(p["nome"] for p in fiadores if p["id"] == x))
                    
                    col_dt1, col_dt2 = st.columns(2)
                    with col_dt1:
                        dt_ini = st.date_input("Data de Início*")
                    with col_dt2:
                        prazo = st.number_input("Prazo em Meses*", min_value=1, value=12)
                    
                    dt_fim = dt_ini + timedelta(days=prazo*30)
                    st.info(f"Término Previsto do Contrato: **{dt_fim.strftime('%d/%m/%Y')}**")

                    val_loc = st.number_input("Valor Mensal (R$)*", min_value=0.0, step=100.0)
                    val_multa = st.number_input("Valor Multa Rescisória (R$)", min_value=0.0, step=100.0)
                    
                    submit_contrato = st.form_submit_button("💾 Salvar Contrato e Ativar")
                    
                    if submit_contrato:
                        payload_contrato = {
                            "id_imovel": imovel_id,
                            "id_locador": locador_id,
                            "id_locatario": locatario_id,
                            "id_fiador": fiador_id if fiador_id != 0 else None,
                            "data_inicio": dt_ini.isoformat(),
                            "prazo_meses": prazo,
                            "data_final": dt_fim.isoformat(),
                            "valor_locacao": val_loc,
                            "multa": val_multa
                        }
                        res_c = requests.post(f"{API_URL}/contratos", json=payload_contrato)
                        if res_c.status_code in [200, 201]:
                            st.success("Contrato consolidado e gerado com sucesso!")
                        else:
                            st.error(f"Erro do Servidor: {res_c.text}")
    except Exception as e:
        st.error(f"O Backend não está acessível no momento: {e}")

# ------------------------------------------------------------------------------
# ABA 4: RELATÓRIOS
# ------------------------------------------------------------------------------
with tab4:
    st.header("📊 Painel de Relatórios e Gestão")
    
    tipo_relatorio = st.radio(
        "Selecione o Relatório Desejado:", 
        ["Relatório Financeiro e Gerencial", "Relatório de Renovação de Contratos"],
        horizontal=True
    )
    
    st.divider()

    if tipo_relatorio == "Relatório Financeiro e Gerencial":
        if st.button("🔄 Atualizar Dados da API", help="Busca os dados mais recentes do servidor."):
            buscar_dados_contratos.clear()
            st.rerun()

        dados = buscar_dados_contratos(API_URL)
        
        if not dados:
            st.info("Nenhum contrato retornado ou aguardando conexão.")
        else:
            df = preparar_dataframe(dados)

            if df.empty:
                st.warning("A API retornou uma lista vazia de contratos.")
            else:
                with st.container():
                    st.markdown("### 🔍 Filtros")
                    f_col1, f_col2, f_col3 = st.columns(3)
                    
                    with f_col1:
                        status_iptu_opts = ["Todos"] + list(df["Status IPTU"].dropna().unique()) if "Status IPTU" in df.columns else ["Todos"]
                        filtro_iptu = st.selectbox("Status do IPTU:", status_iptu_opts)
                    
                    with f_col2:
                        busca_pessoa = st.text_input("Filtrar por Locador/Locatário (Nome parcial):")

                    with f_col3:
                        st.markdown("<br>", unsafe_allow_html=True) 
                        dias_criticos = st.checkbox("⚠️ Apenas contratos vencendo em até 60 dias")

                df_filtrado = df.copy()
                if filtro_iptu != "Todos" and "Status IPTU" in df_filtrado.columns:
                    df_filtrado = df_filtrado[df_filtrado["Status IPTU"] == filtro_iptu]

                if busca_pessoa:
                    filtro_texto = busca_pessoa.lower()
                    if "Locador" in df_filtrado.columns and "Locatário" in df_filtrado.columns:
                        df_filtrado = df_filtrado[
                            df_filtrado["Locador"].str.lower().str.contains(filtro_texto, na=False) |
                            df_filtrado["Locatário"].str.lower().str.contains(filtro_texto, na=False)
                        ]

                if dias_criticos and "Dias Restantes" in df_filtrado.columns:
                    df_filtrado = df_filtrado[df_filtrado["Dias Restantes"] <= 60]

                st.divider()

                st.markdown("### 📌 Indicadores Gerais")
                kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                
                total_contratos = len(df_filtrado)
                receita_total = df_filtrado["Valor (R$)"].sum() if total_contratos > 0 and "Valor (R$)" in df_filtrado.columns else 0.0
                vencendo_60d = len(df_filtrado[df_filtrado["Dias Restantes"] <= 60]) if total_contratos > 0 and "Dias Restantes" in df_filtrado.columns else 0
                iptu_pendente = len(df_filtrado[df_filtrado["Status IPTU"] == "Não Pago"]) if total_contratos > 0 and "Status IPTU" in df_filtrado.columns else 0

                kpi1.metric("Total de Contratos Filtrados", total_contratos)
                kpi2.metric("Faturamento Mensal (Filtro)", f"R$ {receita_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                kpi3.metric("A Vencer (≤ 60 dias)", vencendo_60d, delta_color="inverse")
                kpi4.metric("IPTUs Pendentes", iptu_pendente, delta_color="inverse")

                st.divider()

                st.markdown("### 📋 Tabela Consolidada")
                st.dataframe(
                    df_filtrado, 
                    width="stretch",
                    hide_index=True,
                    column_config={
                        "Valor (R$)": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
                        "IPTU (R$)": st.column_config.NumberColumn("IPTU (R$)", format="R$ %.2f"),
                        "Índice de Reajuste": st.column_config.TextColumn("Índice", help="Índice aplicável para reajuste (ex: IPCA, IGPM)"),
                        "Dados Bancários (Locador)": st.column_config.TextColumn("Dados Bancários (Locador)", width="medium")
                    }
                )

                if "ID" in df_filtrado.columns:
                    st.markdown("### 🗑️ Descartar Cadastro de Contrato")
                    col_del_c1, col_del_c2 = st.columns([0.8, 0.2])
                    with col_del_c1:
                        c_del_id = st.selectbox(
                            "Selecione o Contrato para excluir:",
                            options=df_filtrado["ID"].tolist(),
                            format_func=lambda x: f"Contrato ID #{x}",
                            key="del_contrato_select"
                        )
                    with col_del_c2:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("🗑️ Descartar Contrato", key="btn_del_contrato"):
                            try:
                                res_del = requests.delete(f"{API_URL}/contratos/{c_del_id}")
                                if res_del.status_code in [200, 204]:
                                    st.success("Contrato descartado com sucesso!")
                                    buscar_dados_contratos.clear()
                                    st.rerun()
                                else:
                                    st.error(f"Erro ao descartar: {res_del.text}")
                            except Exception as e:
                                st.error(f"Erro de conexão: {e}")

                if not df_filtrado.empty and "Descrição do Imóvel" in df_filtrado.columns and "Valor (R$)" in df_filtrado.columns:
                    st.markdown("### 📈 Faturamento por Imóvel")
                    chart_data = df_filtrado.groupby("Descrição do Imóvel")["Valor (R$)"].sum()
                    st.bar_chart(chart_data)

                st.divider()
                st.markdown("### 🖨️ Exportação")

                col_exp1, col_exp2, col_exp3 = st.columns(3)

                with col_exp1:
                    if REPORTLAB_AVAILABLE and not df_filtrado.empty:
                        pdf_buffer = gerar_pdf_relatorio(df_filtrado)
                        st.download_button(
                            label="📄 Baixar Relatório (PDF)",
                            data=pdf_buffer,
                            file_name=f"relatorio_locacoes_{date.today().strftime('%Y%m%d')}.pdf",
                            mime="application/pdf",
                            width="stretch"
                        )
                    elif not REPORTLAB_AVAILABLE:
                        st.info("⚠️ Instale 'reportlab' para ativar PDF.")

                with col_exp2:
                    if not df_filtrado.empty:
                        excel_buffer = io.BytesIO()
                        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                            df_filtrado.to_excel(writer, index=False, sheet_name='Contratos')
                        excel_buffer.seek(0)
                        st.download_button(
                            label="📊 Exportar Planilha (Excel)",
                            data=excel_buffer,
                            file_name=f"relatorio_locacoes_{date.today().strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            width="stretch"
                        )

                with col_exp3:
                    st.components.v1.html(
                        '''
                        <div style="display: flex; justify-content: center;">
                            <button onclick="window.print()" style="width: 100%; padding: 10px; font-size: 14px; font-weight: bold; cursor: pointer; background-color: #f0f2f6; color: #31333F; border: 1px solid #c4c4c4; border-radius: 8px; transition: 0.3s;">
                                🖨️ Imprimir Tela
                            </button>
                        </div>
                        ''',
                        height=50
                    )

    elif tipo_relatorio == "Relatório de Renovação de Contratos":
        st.subheader("🔄 Relatório de Renovação e Atualização de Valores")
        st.markdown("Selecione um contrato para visualizar a projeção dos dados atualizados com base no reajuste e confirme a operação para gerar a renovação.")

        dados_renovacao = buscar_dados_contratos(API_URL)
        if not dados_renovacao:
            st.info("Nenhum contrato disponível para renovação.")
        else:
            df_ren = preparar_dataframe(dados_renovacao)
            
            opcoes_ren = {
                f"Contrato #{row.get('Nº Sequência', i)} | Locatário: {row.get('Locatário')} | Imóvel: {row.get('Descrição do Imóvel')}": row
                for i, row in df_ren.iterrows()
            }

            contrato_escolhido_str = st.selectbox("Selecione o Contrato para Analisar a Renovação:", list(opcoes_ren.keys()))

            if contrato_escolhido_str:
                c_data = opcoes_ren[contrato_escolhido_str]
                
                st.markdown("---")
                col_info1, col_info2 = st.columns(2)
                with col_info1:
                    st.markdown(f"**Locador:** {c_data.get('Locador')}")
                    st.markdown(f"**Locatário:** {c_data.get('Locatário')}")
                    st.markdown(f"**Imóvel:** {c_data.get('Descrição do Imóvel')}")
                    st.markdown(f"**Data Final Atual:** {c_data.get('Data Final')}")
                with col_info2:
                    valor_atual = float(c_data.get('Valor (R$)', 0.0))
                    indice_sugerido = c_data.get('Índice de Reajuste', 'IPCA')
                    st.markdown(f"**Valor Atual do Locativo:** R$ {valor_atual:,.2f}")
                    st.markdown(f"**Índice de Reajuste Previsto:** {indice_sugerido}")

                st.markdown("### 🧮 Configuração do Reajuste e Novo Período")
                r_col1, r_col2 = st.columns(2)
                with r_col1:
                    percentual_reajuste = st.number_input("Percentual de Reajuste Aplicável (%)", min_value=0.0, max_value=100.0, value=5.0, step=0.1)
                with r_col2:
                    novo_prazo_meses = st.number_input("Novo Prazo (Meses)", min_value=1, value=12)

                valor_atualizado = valor_atual * (1 + (percentual_reajuste / 100.0))
                
                try:
                    data_fim_atual_obj = date.fromisoformat(str(c_data.get('Data Final')))
                    nova_data_inicio = data_fim_atual_obj + timedelta(days=1)
                except:
                    nova_data_inicio = date.today()

                nova_data_fim = nova_data_inicio + timedelta(days=int(novo_prazo_meses)*30)

                st.info(f"💡 **Projeção Calculada:** O valor do aluguel passará de **R$ {valor_atual:,.2f}** para **R$ {valor_atualizado:,.2f}**. "
                        f"O novo contrato vigorará de **{nova_data_inicio.strftime('%d/%m/%Y')}** até **{nova_data_fim.strftime('%d/%m/%Y')}**.")

                st.markdown("---")
                
                confirma_renovacao = st.checkbox("✅ **Confirmo os dados acima e autorizo a geração e ativação do novo contrato renovado.**")

                if st.button("🚀 Gerar Novo Contrato Renovado", type="primary"):
                    if not confirma_renovacao:
                        st.error("❌ **Confirmação Obrigatória:** Marque a caixa de confirmação dos dados acima para prosseguir com a renovação do contrato.")
                    else:
                        payload_renovacao = {
                            "id_imovel": c_data.get('ID Imóvel'),
                            "id_locador": c_data.get('ID Locador'),
                            "id_locatario": c_data.get('ID Locatário'),
                            "id_fiador": c_data.get('ID Fiador') if pd.notna(c_data.get('ID Fiador')) else None,
                            "data_inicio": nova_data_inicio.isoformat(),
                            "prazo_meses": int(novo_prazo_meses),
                            "data_final": nova_data_fim.isoformat(),
                            "valor_locacao": round(valor_atualizado, 2),
                            "multa": c_data.get('Multa (R$)', 0.0)
                        }
                        
                        try:
                            res_ren = requests.post(f"{API_URL}/contratos", json=payload_renovacao)
                            if res_ren.status_code in [200, 201]:
                                st.success("🎉 Contrato renovado e ativado com sucesso no sistema!")
                            else:
                                st.error(f"Erro ao salvar o contrato renovado: {res_ren.text}")
                        except Exception as e:
                            st.error(f"Erro de comunicação com o servidor backend: {e}")

# ------------------------------------------------------------------------------
# ABA 5: ALERTAS
# ------------------------------------------------------------------------------
with tab5:
    st.header("Verificação e Envio de Alertas")
    email_admin = st.text_input("E-mail do Administrador", value="admin@imoveis.com")
    
    if st.button("🔔 Executar Verificação (Alertas de 60 dias)"):
        try:
            res = requests.post(f"{API_URL}/alertas/verificar-vencimentos?email_admin={email_admin}")
            if res.status_code == 200:
                st.success(res.json().get('mensagem'))
        except Exception as e:
            st.error(f"Erro ao solicitar alertas: {e}")

# ------------------------------------------------------------------------------
# ABA 6: MENSAGENS E COMUNICAÇÃO (Módulo Separado)
# ------------------------------------------------------------------------------
with tab6:
    renderizar_modulo_mensagens(API_URL)