import streamlit as st
import requests

def renderizar_modulo_mensagens(api_url: str):
    """Renderiza o módulo independente de geração de mensagens automáticas."""
    st.header("💬 Gerador de Mensagens Automáticas")
    st.markdown("Selecione um contrato ativo e escolha o objetivo da mensagem nos botões abaixo para gerar o texto personalizado.")

    try:
        res_msg = requests.get(f"{api_url}/relatorio")
        if res_msg.status_code == 200 and res_msg.json():
            dados_msg = res_msg.json()
            
            opcoes_contratos = {
                f"{c.get('locatario', 'Locatário')} - {c.get('descricao_imovel', 'Imóvel')}": c 
                for c in dados_msg
            }
            
            contrato_selecionado = st.selectbox("Selecione o Destinatário (Locatário - Imóvel):", list(opcoes_contratos.keys()))
            
            if contrato_selecionado:
                dados_c = opcoes_contratos[contrato_selecionado]
                locatario_nome = dados_c.get('locatario', 'Locatário')
                imovel_desc = dados_c.get('descricao_imovel', 'Imóvel')
                valor_aluguel = float(dados_c.get('valor_locacao', 0.0))
                
                st.markdown("---")
                st.markdown("### Escolha o Tipo de Mensagem:")
                
                b_col1, b_col2, b_col3, b_col4, b_col5 = st.columns(5)
                
                tipo_mensagem = None
                with b_col1:
                    if st.button("🤝 Comunicação Amiga", use_container_width=True):
                        tipo_mensagem = "Comunicação Amiga"
                with b_col2:
                    if st.button("🎉 Boas Festas", use_container_width=True):
                        tipo_mensagem = "Boas Festas"
                with b_col3:
                    if st.button("🏆 Congratulações", use_container_width=True):
                        tipo_mensagem = "Congratulações"
                with b_col4:
                    if st.button("💰 Cobrança Aluguel", use_container_width=True):
                        tipo_mensagem = "Cobrança de Aluguel"
                with b_col5:
                    if st.button("📄 Cobrança IPTU", use_container_width=True):
                        tipo_mensagem = "Cobrança de IPTU"

                if "tipo_msg_ativo" not in st.session_state:
                    st.session_state.tipo_msg_ativo = "Comunicação Amiga"

                if tipo_mensagem:
                    st.session_state.tipo_msg_ativo = tipo_mensagem

                ativo = st.session_state.tipo_msg_ativo
                st.markdown(f"**Categoria Ativa:** `{ativo}`")

                mensagem_gerada = ""
                if ativo == "Comunicação Amiga":
                    mensagem_gerada = f"Olá, {locatario_nome}! Tudo bem? Passando aqui apenas para saber se está tudo certo com o imóvel em {imovel_desc} e se precisa de alguma assistência da nossa parte. Um abraço!"
                elif ativo == "Boas Festas":
                    mensagem_gerada = f"Olá, {locatario_nome}! Gostaríamos de desejar a você e sua família um excelente final de ano e de boas festas! Que o próximo ano traga muitas alegrias no seu lar em {imovel_desc}."
                elif ativo == "Congratulações":
                    mensagem_gerada = f"Parabéns, {locatario_nome}! Desejamos muitas felicidades, saúde e sucesso. É um prazer ter você como nosso locatário no imóvel {imovel_desc}. Aproveite muito o seu dia!"
                elif ativo == "Cobrança de Aluguel":
                    mensagem_gerada = f"Olá, {locatario_nome}. Esperamos que esteja bem. Verificamos em nosso sistema que o pagamento do aluguel referente ao imóvel {imovel_desc}, no valor de R$ {valor_aluguel:,.2f}, encontra-se em aberto. Caso já tenha efetuado o pagamento, por favor, desconsidere esta mensagem."
                elif ativo == "Cobrança de IPTU":
                    mensagem_gerada = f"Olá, {locatario_nome}. Tudo bem? Passando para lembrar sobre a parcela do IPTU referente ao imóvel {imovel_desc}. Caso precise do código de barras ou do boleto atualizado para pagamento, é só nos avisar!"

                st.markdown("### Texto da Mensagem")
                texto_final = st.text_area("Você pode editar o texto abaixo antes de copiar:", value=mensagem_gerada, height=150)
                
                st.info("💡 Dica: Copie o texto acima e cole diretamente no WhatsApp ou E-mail do locatário para enviar.")
            
        else:
            st.info("Não há contratos consolidados disponíveis para gerar mensagens no momento.")
    except Exception as e:
        st.error(f"Erro ao conectar com a API para buscar os contratos: {e}")