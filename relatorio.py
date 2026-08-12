import streamlit as st
import requests
import pandas as pd
from datetime import date
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

def gerar_pdf_relatorio(df_dados):
    """Gera um buffer de PDF com os dados do relatório."""
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
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F3F4F6')]),
    ]))
    
    story.append(table)
    doc.build(story)
    buffer.seek(0)
    return buffer

def renderizar_relatorio(api_url):
    """Renderiza a interface do relatório no Streamlit."""
    st.header("📊 Relatório Gerencial e Financeiro de Contratos")
    
    col_hdr1, col_hdr2 = st.columns([1, 4])
    with col_hdr1:
        if st.button("🔄 Atualizar Dados"):
            st.rerun()

    try:
        res = requests.get(f"{api_url}/relatorio")
        if res.status_code == 200:
            dados = res.json()
            if dados:
                df_raw = pd.DataFrame(dados)

                # Padronização de colunas
                df = df_raw.rename(columns={
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

                # --- 1. FILTROS DINÂMICOS ---
                with st.expander("🔍 **Filtros do Relatório**", expanded=True):
                    f_col1, f_col2, f_col3 = st.columns(3)
                    
                    with f_col1:
                        status_iptu_opts = ["Todos"] + list(df["Status IPTU"].dropna().unique())
                        filtro_iptu = st.selectbox("Status do IPTU:", status_iptu_opts)
                    
                    with f_col2:
                        busca_pessoa = st.text_input("Filtrar por Locador/Locatário:")

                    with f_col3:
                        dias_criticos = st.checkbox("Exibir apenas contratos vencendo em até 60 dias")

                # Aplicação dos Filtros
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

                # --- 2. CARDS DE MÉTRICAS (KPIs) ---
                st.subheader("📌 Indicadores Gerais")
                kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                
                total_contratos = len(df_filtrado)
                receita_total = df_filtrado["Valor (R$)"].sum() if total_contratos > 0 else 0.0
                vencendo_60d = len(df_filtrado[df_filtrado["Dias Restantes"] <= 60]) if total_contratos > 0 else 0
                iptu_pendente = len(df_filtrado[df_filtrado["Status IPTU"] == "Não Pago"]) if total_contratos > 0 else 0

                kpi1.metric("Total de Contratos", total_contratos)
                kpi2.metric("Receita Mensal Total", f"R$ {receita_total:,.2f}")
                kpi3.metric("A Vencer (≤ 60 dias)", vencendo_60d, delta_color="inverse")
                kpi4.metric("IPTUs Não Pagos", iptu_pendente, delta_color="inverse")

                st.divider()

                # --- 3. VISUALIZAÇÃO DE DADOS ---
                st.subheader("📋 Tabela Consolidada")
                st.dataframe(df_filtrado, use_container_width=True)

                if not df_filtrado.empty:
                    st.subheader("📈 Faturamento por Imóvel")
                    chart_data = df_filtrado.set_index("Descrição do Imóvel")[["Valor (R$)"]]
                    st.bar_chart(chart_data)

                # --- 4. OPÇÕES DE EXPORTAÇÃO ---
                st.divider()
                st.subheader("🖨️ Opções de Impressão e Exportação")

                col_exp1, col_exp2, col_exp3 = st.columns(3)

                with col_exp1:
                    if REPORTLAB_AVAILABLE:
                        pdf_buffer = gerar_pdf_relatorio(df_filtrado)
                        st.download_button(
                            label="📄 Baixar PDF",
                            data=pdf_buffer,
                            file_name=f"relatorio_locacoes_{date.today()}.pdf",
                            mime="application/pdf"
                        )
                    else:
                        st.info("Instale 'reportlab' para gerar PDF.")

                with col_exp2:
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        df_filtrado.to_excel(writer, index=False, sheet_name='Contratos')
                    excel_buffer.seek(0)
                    st.download_button(
                        label="📊 Exportar para Excel",
                        data=excel_buffer,
                        file_name=f"relatorio_locacoes_{date.today()}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                with col_exp3:
                    st.components.v1.html(
                        '<button onclick="window.print()" style="padding: 10px 20px; font-size: 14px; cursor: pointer; background-color: #1E3A8A; color: white; border: none; border-radius: 5px;">🖨️ Imprimir Página</button>',
                        height=50
                    )
            else:
                st.info("Nenhum contrato gerado até o momento.")
    except Exception as e:
        st.error(f"Erro ao conectar ao servidor: {e}")