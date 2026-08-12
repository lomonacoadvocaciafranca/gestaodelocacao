import streamlit as st
import requests
import pandas as pd
from datetime import date, timedelta
import io

# Importação opcional para geração de PDF
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

st.set_page_config(page_title="Gestão de Locações", page_icon="🏢", layout="wide")

API_URL = "http://127.0.0.1:8000"

st.title("🏢 Sistema Gerencial de Locação de Imóveis")

st.markdown("""
<style>
@media print {
    [data-testid="stSidebar"], .stButton, header, footer { display: none !important; }
    .main .block-container { padding: 0 !important; }
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# FUNÇÃO AUXILIAR - PDF
# ------------------------------------------------------------------------------
def gerar_pdf_relatorio(df_dados):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#1E3A8A'), spaceAfter=12)
    
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
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F3F4F6')]),
    ]))
    
    story.append(table)
    doc.build(story)
    buffer.seek(0)
    return buffer

# Navegação por Abas Principais
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "👤 Pessoas", "🏠 Imóveis", "📄 Contratos", "📊 Relatório", "📧 Alertas"
])

# ------------------------------------------------------------------------------
# ABA 1: PESSOAS
# ------------------------------------------------------------------------------
with tab1:
    st.header("Cadastrar Pessoa (Locador, Locatário ou Fiador)")
    with st.form("form_pessoas", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            tipo = st.selectbox("Tipo de Perfil*", ["Locador", "Locatário", "Fiador"])
            nome = st.text_input("Nome Completo*")
            cpf = st.text_input("CPF*")
            rg = st.text_input("RG*")
        with col2:
            endereco = st.text_input("Endereço Completo*")
            cep = st.text_input("CEP*")
            cidade = st.text_input("Cidade*")
            estado = st.selectbox("Estado (UF)*", ["SP", "MG", "RJ", "PR", "SC", "RS", "GO", "DF", "ES", "BA", "CE", "PE", "OUTRO"])

        doc_pessoa = st.file_uploader("📂 Upload de Documentos Pessoais", type=["pdf", "png", "jpg", "jpeg"])
        btn_salvar_pessoa = st.form_submit_button("💾 Salvar Cadastro de Pessoa")

        if btn_salvar_pessoa:
            if not (nome and cpf and rg and endereco and cep and cidade):
                st.warning("Preencha todos os campos obrigatórios (*).")
            else:
                payload = {"tipo": tipo, "nome": nome, "cpf": cpf, "rg": rg, "endereco": endereco, "cep": cep, "cidade": cidade, "estado": estado}
                try:
                    res = requests.post(f"{API_URL}/pessoas", json=payload)
                    if res.status_code in [200, 201]:
                        st.success(f"{tipo} '{nome}' cadastrado(a) com sucesso!")
                        
                        # Correção: Funcionalidade real de envio de upload
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
            st.dataframe(pd.DataFrame(res_p.json()), use_container_width=True)
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
            st.dataframe(pd.DataFrame(res_i.json()), use_container_width=True)
    except:
        pass

# ------------------------------------------------------------------------------
# ABA 3: CONTRATOS (Lógica Integrada para evitar falha de Módulos Externos)
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
# ABA 4: RELATÓRIO
# ------------------------------------------------------------------------------
with tab4:
    st.header("📊 Relatório Gerencial e Financeiro de Contratos")
    col_hdr1, col_hdr2 = st.columns([1, 4])
    with col_hdr1:
        if st.button("🔄 Atualizar Relatório"):
            st.rerun()

    try:
        res = requests.get(f"{API_URL}/relatorio")
        if res.status_code == 200:
            dados = res.json()
            if dados:
                df = pd.DataFrame(dados).rename(columns={
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
                    "dias_restantes": "Dias Restantes"
                })

                with st.expander("🔍 Filtros de Relatório", expanded=True):
                    f_col1, f_col2, f_col3 = st.columns(3)
                    with f_col1:
                        status_iptu_opts = ["Todos"] + list(df["Status IPTU"].dropna().unique())
                        filtro_iptu = st.selectbox("Status do IPTU:", status_iptu_opts)
                    with f_col2:
                        busca_pessoa = st.text_input("Filtrar Locador/Locatário:")
                    with f_col3:
                        dias_criticos = st.checkbox("Somente vencendo em até 60 dias")

                df_filtrado = df.copy()
                if filtro_iptu != "Todos":
                    df_filtrado = df_filtrado[df_filtrado["Status IPTU"] == filtro_iptu]
                if busca_pessoa:
                    df_filtrado = df_filtrado[
                        df_filtrado["Locador"].str.contains(busca_pessoa, case=False, na=False) |
                        df_filtrado["Locatário"].str.contains(busca_pessoa, case=False, na=False)
                    ]
                if dias_criticos:
                    df_filtrado = df_filtrado[df_filtrado["Dias Restantes"] <= 60]

                st.subheader("📌 Indicadores Gerais")
                kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                
                total_contratos = len(df_filtrado)
                receita_total = df_filtrado["Valor (R$)"].sum() if total_contratos > 0 else 0.0
                vencendo_60d = len(df_filtrado[df_filtrado["Dias Restantes"] <= 60]) if total_contratos > 0 else 0
                iptu_pendente = len(df_filtrado[df_filtrado["Status IPTU"] == "Não Pago"]) if total_contratos > 0 else 0

                kpi1.metric("Total de Contratos", total_contratos)
                kpi2.metric("Receita Mensal", f"R$ {receita_total:,.2f}")
                kpi3.metric("A Vencer (≤ 60 dias)", vencendo_60d, delta_color="inverse")
                kpi4.metric("IPTUs Não Pagos", iptu_pendente, delta_color="inverse")

                st.divider()
                st.dataframe(df_filtrado, use_container_width=True)

                if not df_filtrado.empty:
                    st.subheader("📈 Faturamento por Imóvel")
                    chart_data = df_filtrado.set_index("Descrição do Imóvel")[["Valor (R$)"]]
                    st.bar_chart(chart_data)

                st.divider()
                st.subheader("🖨️ Opções de Exportação")
                col_exp1, col_exp2, col_exp3 = st.columns(3)

                with col_exp1:
                    if REPORTLAB_AVAILABLE:
                        pdf_buffer = gerar_pdf_relatorio(df_filtrado)
                        st.download_button("📄 Baixar PDF", data=pdf_buffer, file_name=f"relatorio_{date.today()}.pdf", mime="application/pdf")
                    else:
                        st.info("Instale 'reportlab' para gerar PDFs.")

                with col_exp2:
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        df_filtrado.to_excel(writer, index=False, sheet_name='Contratos')
                    st.download_button("📊 Exportar para Excel", data=excel_buffer.getvalue(), file_name=f"relatorio_{date.today()}.xlsx")

                with col_exp3:
                    st.components.v1.html('<button onclick="window.print()" style="padding:10px 20px; background-color:#1E3A8A; color:white; border:none; border-radius:5px;">🖨️ Imprimir Página</button>', height=50)
            else:
                st.info("Nenhum contrato consolidado.")
    except Exception as e:
        st.error(f"Erro ao ler relatórios: {e}")

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