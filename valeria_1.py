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

# CSS para suporte a impressão via navegador
st.markdown("""
<style>
@media print {
    [data-testid="stSidebar"], .stButton, header, footer {
        display: none !important;
    }
    .main .block-container {
        padding: 0 !important;
    }
}
</style>
""", unsafe_allow_html=True)

# Função auxiliar para gerar relatório PDF
def gerar_pdf_relatorio(df_dados):
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

    # Tabela com dados
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
    "👤 Cadastro de Pessoas", 
    "🏠 Cadastro de Imóveis", 
    "📄 Cadastro de Contratos", 
    "📊 Relatório Gerencial", 
    "📧 Alertas de Vencimento"
])

# ------------------------------------------------------------------------------
# ABA 1: CADASTRO DE PESSOAS
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

        # Upload de Documento Pessoal (RG, CPF, Comprovante)
        doc_pessoa = st.file_uploader("📂 Upload de Documentos Pessoais (PDF, JPG, PNG)", type=["pdf", "png", "jpg", "jpeg", "docx"], key="upload_pessoa")

        btn_salvar_pessoa = st.form_submit_button("💾 Salvar Cadastro de Pessoa")

        if btn_salvar_pessoa:
            if not (nome and cpf and rg and endereco and cep and cidade):
                st.warning("Preencha todos os campos obrigatórios (*).")
            else:
                payload = {
                    "tipo": tipo, "nome": nome, "cpf": cpf, "rg": rg,
                    "endereco": endereco, "cep": cep, "cidade": cidade, "estado": estado
                }
                try:
                    res = requests.post(f"{API_URL}/pessoas", json=payload)
                    if res.status_code in [200, 201]:
                        st.success(f"{tipo} '{nome}' cadastrado(a) com sucesso!")
                        if doc_pessoa:
                            st.info(f"Arquivo '{doc_pessoa.name}' anexado com sucesso!")
                    else:
                        st.error(f"Erro ao cadastrar: {res.text}")
                except Exception as e:
                    st.error(f"Certifique-se de que o Uvicorn/Backend está rodando: {e}")

    # Lista pessoas cadastradas na mesma tela
    st.divider()
    st.subheader("Pessoas Cadastradas no Sistema")
    try:
        res_p = requests.get(f"{API_URL}/pessoas")
        if res_p.status_code == 200 and res_p.json():
            st.dataframe(pd.DataFrame(res_p.json()), use_container_width=True)
    except:
        pass

# ------------------------------------------------------------------------------
# ABA 2: CADASTRO DE IMÓVEIS
# ------------------------------------------------------------------------------
with tab2:
    st.header("Cadastrar Imóvel")
    
    with st.form("form_imoveis", clear_on_submit=True):
        col_imv1, col_imv2 = st.columns(2)
        with col_imv1:
            endereco_imovel = st.text_input("Endereço do Imóvel*")
            descricao_imovel = st.text_area("Descrição do Imóvel* (Ex: Casa 3 quartos, suíte, garagem)")
        with col_imv2:
            valor_iptu_imovel = st.number_input("Valor Anual/Mensal do IPTU (R$)", min_value=0.0, value=0.0, step=50.0)
            status_iptu_imovel = st.selectbox("Status do IPTU", ["Pago", "Não Pago", "Isento", "Pendente"])

        # Upload de Documentos do Imóvel
        doc_imovel = st.file_uploader("📂 Upload de Documentos do Imóvel (Matrícula, Carnê IPTU, Habite-se)", type=["pdf", "png", "jpg", "jpeg", "docx"], key="upload_imovel")

        btn_salvar_imovel = st.form_submit_button("💾 Salvar Cadastro de Imóvel")

        if btn_salvar_imovel:
            if not (endereco_imovel and descricao_imovel):
                st.warning("Preencha o endereço e a descrição do imóvel.")
            else:
                payload = {
                    "endereco": endereco_imovel, 
                    "descricao": descricao_imovel,
                    "valor_iptu": float(valor_iptu_imovel),
                    "status_iptu": status_iptu_imovel
                }
                try:
                    res = requests.post(f"{API_URL}/imoveis", json=payload)
                    if res.status_code in [200, 201]:
                        st.success("Imóvel cadastrado com sucesso!")
                        if doc_imovel:
                            st.info(f"Documento '{doc_imovel.name}' anexado ao imóvel com sucesso!")
                    else:
                        st.error(f"Erro ao salvar imóvel: {res.text}")
                except Exception as e:
                    st.error(f"Erro de conexão com backend: {e}")

    # Lista imóveis cadastrados na mesma tela
    st.divider()
    st.subheader("Imóveis Cadastrados")
    try:
        res_i = requests.get(f"{API_URL}/imoveis")
        if res_i.status_code == 200 and res_i.json():
            st.dataframe(pd.DataFrame(res_i.json()), use_container_width=True)
    except:
        pass

# ------------------------------------------------------------------------------
# ABA 3: CADASTRO DE CONTRATOS
# ------------------------------------------------------------------------------
with tab3:
    st.header("Cadastrar Contrato de Locação")

    # Buscar relacionamentos
    imoveis, pessoas = [], []
    try:
        imoveis = requests.get(f"{API_URL}/imoveis").json()
        pessoas = requests.get(f"{API_URL}/pessoas").json()
    except Exception as e:
        st.error("Inicie o backend Uvicorn para carregar as opções de contrato.")

    locadores = [p for p in pessoas if p.get('tipo') == 'Locador']
    locatarios = [p for p in pessoas if p.get('tipo') == 'Locatário']
    fiadores = [p for p in pessoas if p.get('tipo') == 'Fiador']

    if not imoveis or not locadores or not locatarios or not fiadores:
        st.info("⚠️ Para gerar um contrato, cadastre previamente na aba correspondente: pelo menos 1 Imóvel, 1 Locador, 1 Locatário e 1 Fiador.")
    else:
        with st.form("form_contratos", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                map_imoveis = {f"ID {i['id']} - {i['descricao']}": i['id'] for i in imoveis}
                sel_imovel = st.selectbox("Selecione o Imóvel*", list(map_imoveis.keys()))

                map_locadores = {f"{p['nome']} (CPF: {p['cpf']})": p['id'] for p in locadores}
                sel_locador = st.selectbox("Selecione o Locador*", list(map_locadores.keys()))

                map_locatarios = {f"{p['nome']} (CPF: {p['cpf']})": p['id'] for p in locatarios}
                sel_locatario = st.selectbox("Selecione o Locatário*", list(map_locatarios.keys()))

                map_fiadores = {f"{p['nome']} (CPF: {p['cpf']})": p['id'] for p in fiadores}
                sel_fiador = st.selectbox("Selecione o Fiador*", list(map_fiadores.keys()))

            with c2:
                dt_inicio = st.date_input("Data de Início*", value=date.today())
                prazo = st.number_input("Prazo da Locação (em meses)*", min_value=1, value=12)
                dt_final = st.date_input("Data Final*", value=dt_inicio + timedelta(days=prazo*30))
                valor = st.number_input("Valor da Locação (R$)*", min_value=0.0, value=1500.0)
                multa = st.number_input("Valor da Multa (R$)*", min_value=0.0, value=3000.0)
                
                # Novos Campos de IPTU no Contrato
                valor_iptu = st.number_input("Valor do IPTU (R$)", min_value=0.0, value=0.0, step=10.0)
                status_iptu = st.selectbox("Status do IPTU", ["Pago", "Não Pago"])

            # Upload de Contrato/Anexos Assinados
            doc_contrato = st.file_uploader("📂 Upload do Contrato Assinado / Comprovantes (PDF, DOCX, PNG)", type=["pdf", "png", "jpg", "jpeg", "docx"], key="upload_contrato")

            btn_salvar_contrato = st.form_submit_button("📝 Salvar Contrato de Locação")

            if btn_salvar_contrato:
                payload = {
                    "id_imovel": map_imoveis[sel_imovel],
                    "id_locador": map_locadores[sel_locador],
                    "id_locatario": map_locatarios[sel_locatario],
                    "id_fiador": map_fiadores[sel_fiador],
                    "data_inicio": dt_inicio.isoformat(),
                    "prazo_meses": int(prazo),
                    "data_final": dt_final.isoformat(),
                    "valor_locacao": float(valor),
                    "multa": float(multa),
                    "valor_iptu": float(valor_iptu),
                    "status_iptu": status_iptu
                }
                try:
                    res = requests.post(f"{API_URL}/contratos", json=payload)
                    if res.status_code in [200, 201]:
                        st.success("Contrato cadastrado com sucesso!")
                        if doc_contrato:
                            st.info(f"Contrato anexado: '{doc_contrato.name}'")
                    else:
                        st.error(f"Erro ao salvar contrato: {res.text}")
                except Exception as e:
                    st.error(f"Erro de conexão: {e}")

# ------------------------------------------------------------------------------
# ABA 4: RELATÓRIO GERENCIAL
# ------------------------------------------------------------------------------
with tab4:
    st.header("Relatório Gerencial de Contratos")
    
    col_acoes1, col_acoes2 = st.columns([1, 4])
    with col_acoes1:
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

                st.dataframe(df, use_container_width=True)

                st.divider()
                st.subheader("🖨️ Opções de Impressão e Exportação")

                col_exp1, col_exp2, col_exp3 = st.columns(3)

                # Exportar para PDF Impresso
                with col_exp1:
                    if REPORTLAB_AVAILABLE:
                        pdf_buffer = gerar_pdf_relatorio(df)
                        st.download_button(
                            label="📄 Baixar Relatório em PDF (Para Impressão)",
                            data=pdf_buffer,
                            file_name=f"relatorio_locacoes_{date.today()}.pdf",
                            mime="application/pdf"
                        )
                    else:
                        st.info("Instale 'reportlab' (`pip install reportlab`) para gerar relatórios em PDF.")

                # Exportar para Excel
                with col_exp2:
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='Contratos')
                    excel_buffer.seek(0)

                    st.download_button(
                        label="📊 Exportar para Excel (.xlsx)",
                        data=excel_buffer,
                        file_name=f"relatorio_locacoes_{date.today()}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                # Botão de Impressão Direta
                with col_exp3:
                    st.components.v1.html(
                        '<button onclick="window.print()" style="padding: 10px 20px; font-size: 14px; cursor: pointer; background-color: #1E3A8A; color: white; border: none; border-radius: 5px;">🖨️ Imprimir Pagina Atual</button>',
                        height=50
                    )

            else:
                st.info("Nenhum contrato gerado até o momento.")
    except Exception as e:
        st.error(f"Erro ao conectar ao servidor: {e}")

# ------------------------------------------------------------------------------
# ABA 5: ALERTAS DE VENCIMENTO
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