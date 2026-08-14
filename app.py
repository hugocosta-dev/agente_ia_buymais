import streamlit as st
from chat import DOCUMENTO, responder


st.set_page_config(page_title="Agente BuyMais", page_icon="🤖", layout="centered")

st.title("🤖 Agente de Reembolsos BuyMais")

st.write("Faça perguntas sobre a Política de Reembolsos e Devoluções da BuyMais.")

if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

def exibir_fontes(fontes: list[str]) -> None:
    if not fontes:
        return

    with st.expander(f"Fontes consultadas — {DOCUMENTO}"):
        for fonte in fontes:
            st.caption(fonte)


for mensagem in st.session_state.mensagens:
    with st.chat_message(mensagem["role"]):
        st.markdown(mensagem["content"])

        if mensagem["role"] == "assistant":
            exibir_fontes(mensagem.get("fontes", []))


pergunta = st.chat_input("Exemplo: Qual é o prazo para solicitar reembolso?")


if pergunta:
    pergunta = pergunta.strip()

    if not pergunta:
        st.warning("A pergunta não pode estar vazia.")
        st.stop()

    historico = st.session_state.mensagens.copy()
    st.session_state.mensagens.append(
        {
            "role": "user",
            "content": pergunta,
        }
    )

    with st.chat_message("user"):
        st.markdown(pergunta)

    with st.chat_message("assistant"):
        with st.spinner("Consultando a política de reembolso..."):
            try:
                resposta, fontes = responder(pergunta=pergunta, historico=historico)
                st.markdown(resposta)
                exibir_fontes(fontes)

                st.session_state.mensagens.append(
                    {
                        "role": "assistant",
                        "content": resposta,
                        "fontes": fontes,
                    }
                )
            except Exception as erro:
                resposta = ("Erro. Verifique a configuração da aplicação.")
                st.error(resposta)
                st.exception(erro)
   