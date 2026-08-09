import streamlit as st
import requests
import pandas as pd
from datetime import date, timedelta

st.set_page_config(page_title="Gestão de Locações", page_icon="🏢", layout="wide")

API_URL = "http://127.0.0.1:8000"

st.title("🏢 Sistema Gerencial de Locação de Imóveis")

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
        endereco_imovel = st.text_input("Endereço do Imóvel*")
        descricao_imovel = st.text_area("Descrição do Imóvel* (Ex: Casa 3 quartos, suíte, garagem)")
        
        btn_salvar_imovel = st.form_submit_button("💾 Salvar Cadastro de Imóvel")

        if btn_salvar_imovel:
            if not (endereco_imovel and descricao_imovel):
                st.warning("Preencha o endereço e a descrição do imóvel.")
            else:
                payload = {"endereco": endereco_imovel, "descricao": descricao_imovel}
                try:
                    res = requests.post(f"{API_URL}/imoveis", json=payload)
                    if res.status_code in [200, 201]:
                        st.success("Imóvel cadastrado com sucesso!")
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
                    "multa": float(multa)
                }
                try:
                    res = requests.post(f"{API_URL}/contratos", json=payload)
                    if res.status_code in [200, 201]:
                        st.success("Contrato cadastrado com sucesso!")
                    else:
                        st.error(f"Erro ao salvar contrato: {res.text}")
                except Exception as e:
                    st.error(f"Erro de conexão: {e}")

# ------------------------------------------------------------------------------
# ABA 4: RELATÓRIO GERENCIAL
# ------------------------------------------------------------------------------
with tab4:
    st.header("Relatório Gerencial de Contratos")
    
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
                    "dias_restantes": "Dias Restantes"
                })
                st.dataframe(df, use_container_width=True)
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