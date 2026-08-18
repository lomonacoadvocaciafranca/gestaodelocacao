import streamlit as st
import requests
import pandas as pd
from datetime import date, datetime

def calcular_encargos(
    valor_devido: float, 
    data_vencimento: date, 
    data_pagamento: date, 
    taxa_ipc_anual: float = 4.5
) -> dict:
    """
    Calcula a Correção Monetária (IPC) e Juros de Mora (1% a.m. ou fração).
    """
    if data_pagamento <= data_vencimento:
        # Sem atraso
        return {
            "dias_atraso": 0,
            "meses_fracao": 0,
            "correcao": 0.0,
            "juros": 0.0,
            "total": round(valor_devido, 2)
        }

    # Calculo de atraso
    dias_atraso = (data_pagamento - data_vencimento).days
    
    # Juros: 1% ao mês ou fração de mês em atraso
    # Exemplo: 1 a 30 dias = 1 mês; 31 a 60 dias = 2 meses, etc.
    meses_fracao = (dias_atraso - 1) // 30 + 1
    taxa_juros = 0.01 * meses_fracao
    valor_juros = valor_devido * taxa_juros

    # Correção Monetária via IPC (Pro-rata dia com base na taxa informada/estimada)
    # Converte taxa anual IPC estimada em taxa diária equivalente
    taxa_ipc_diaria = ((1 + (taxa_ipc_anual / 100.0)) ** (1 / 365.0)) - 1
    valor_correcao = valor_devido * (taxa_ipc_diaria * dias_atraso)

    valor_total = valor_devido + valor_correcao + valor_juros

    return {
        "dias_atraso": dias_atraso,
        "meses_fracao": meses_fracao,
        "correcao": round(valor_correcao, 2),
        "juros": round(valor_juros, 2),
        "total": round(valor_total, 2)
    }


def renderizar_modulo_financeiro(api_url: str):
    """Renderiza a interface de administração financeira e liquidação de débitos."""
    st.header("💰 Administração Financeira e Cálculo de Débitos")
    st.markdown(
        "Selecione um contrato para apurar cobranças em aberto, calcular a **Correção Monetária (IPC)** "
        "e **Juros de Mora (1% ao mês ou fração)** sobre o período de atraso."
    )

    try:
        res = requests.get(f"{api_url}/relatorio", timeout=10)
        if res.status_code == 200 and res.json():
            dados_contratos = res.json()

            opcoes_contratos = {
                f"Contrato #{c.get('numero_sequencia', c.get('id', 'N/A'))} | "
                f"Locatário: {c.get('locatario', 'N/A')} | "
                f"Imóvel: {c.get('descricao_imovel', 'N/A')}": c
                for c in dados_contratos
            }

            contrato_sel = st.selectbox(
                "Selecione o Contrato para Lançamento Financeiro:",
                list(opcoes_contratos.keys())
            )

            if contrato_sel:
                dados_c = opcoes_contratos[contrato_sel]

                st.divider()
                st.subheader("⚙️ Parâmetros do Débito")

                col_f1, col_f2, col_f3 = st.columns(3)

                with col_f1:
                    val_devido_padrao = float(dados_c.get("valor_locacao", 0.0))
                    valor_devido = st.number_input(
                        "Valor Devido (R$)*",
                        min_value=0.0,
                        value=val_devido_padrao,
                        step=50.0,
                        format="%.2f"
                    )

                with col_f2:
                    dt_vencimento = st.date_input(
                        "Data de Vencimento*",
                        value=date.today()
                    )

                with col_f3:
                    dt_pagamento = st.date_input(
                        "Data de Pagamento / Calculada*",
                        value=date.today()
                    )

                st.markdown("### 📊 Índice de Correção")
                ipc_anual = st.number_input(
                    "Taxa de Correção IPC Anual Estimada (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=4.5,
                    step=0.1,
                    help="Taxa IPC aplicada pro-rata aos dias em atraso."
                )

                # Cálculo automático
                resultado = calcular_encargos(
                    valor_devido=valor_devido,
                    data_vencimento=dt_vencimento,
                    data_pagamento=dt_pagamento,
                    taxa_ipc_anual=ipc_anual
                )

                st.divider()
                st.subheader("📋 Relatório de Apuração Financeira")

                # Resumo em Metricas
                col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
                col_m1.metric("Valor Devido", f"R$ {valor_devido:,.2f}")
                col_m2.metric("Correção (IPC)", f"R$ {resultado['correcao']:,.2f}")
                col_m3.metric(f"Juros (1% x {resultado['meses_fracao']} m/f)", f"R$ {resultado['juros']:,.2f}")
                col_m4.metric("Atraso (Dias)", f"{resultado['dias_atraso']} dias")
                col_m5.metric("Total Atualizado", f"R$ {resultado['total']:,.2f}")

                # Tabela Consolidada exigida
                df_relatorio = pd.DataFrame([{
                    "Locatário": dados_c.get("locatario", "N/A"),
                    "Imóvel": dados_c.get("descricao_imovel", "N/A"),
                    "Valor Devido (R$)": valor_devido,
                    "Vencimento": dt_vencimento.strftime("%d/%m/%Y"),
                    "Pagamento": dt_pagamento.strftime("%d/%m/%Y"),
                    "Valor Pago / Atualizado (R$)": resultado["total"],
                    "Correção IPC (R$)": resultado["correcao"],
                    "Juros (R$)": resultado["juros"],
                    "Total (R$)": resultado["total"]
                }])

                st.markdown("#### Detalhamento Consolidado")
                st.dataframe(
                    df_relatorio,
                    width="stretch",
                    hide_index=True,
                    column_config={
                        "Valor Devido (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                        "Valor Pago / Atualizado (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                        "Correção IPC (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                        "Juros (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                        "Total (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                    }
                )

                # Exportação
                st.download_button(
                    label="📊 Exportar Demostrativo de Débito (CSV)",
                    data=df_relatorio.to_csv(index=False).encode('utf-8'),
                    file_name=f"demonstrativo_debito_{dados_c.get('id', '0')}_{date.today().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    type="primary"
                )

        else:
            st.info("Nenhum contrato retornado para apuração financeira.")
    except Exception as e:
        st.error(f"Erro ao conectar com a API Backend: {e}")