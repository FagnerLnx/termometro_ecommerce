import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import datetime

# ==========================================
# 1. CONFIGURAÇÕES DA PÁGINA
# ==========================================
st.set_page_config(page_title="Termômetro Logístico E-commerce | LogiNexo", layout="centered")

# ==========================================
# 2. BANCO DE DADOS INTERNO (HARDCODED DO RAIO-X)
# ==========================================
DEVOLUCAO_POR_SEGMENTO = {
    "Moda Feminina": 0.25,
    "Moda Masculina": 0.175,
    "Calçados": 0.21,
    "Eletrônicos": 0.075,
    "Casa/Decoração": 0.125,
    "Beleza/Cosméticos": 0.10,
    "Alimentos": 0.03,
    "Pet": 0.065,
    "Outros": 0.10
}

def obter_benchmark_frete(faturamento_anual):
    if faturamento_anual <= 10000000:       
        return 22.00
    elif faturamento_anual <= 30000000:     
        return 18.00
    elif faturamento_anual <= 50000000:     
        return 15.00
    else:                                   
        return 13.00

# ==========================================
# 3. CONEXÃO COM O GOOGLE SHEETS
# ==========================================
def salvar_lead_no_sheets(email, segmento, fat_mensal, custo_pedido):
    try:
        cred_dict = st.secrets["gcp_service_account"]
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        credentials = Credentials.from_service_account_info(cred_dict, scopes=scopes)
        cliente = gspread.authorize(credentials)
        
        PLANILHA_ID = '1rQaMyZd1Rn2M32t52eSinGwnTK3RGAszRz5hQ9pP2uo'
        planilha = cliente.open_by_key(PLANILHA_ID).worksheet("Leads_Termometro")
        
        agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        planilha.append_row([agora, email, segmento, fat_mensal, custo_pedido])
        return True
    except Exception as e:
        st.error(f"Erro de infraestrutura ao salvar: {e}")
        return False

# ==========================================
# 4. GERENCIADOR DE ESTADO
# ==========================================
if 'etapa' not in st.session_state:
    st.session_state.etapa = 1

# ==========================================
# 5. TELAS (FRONTEND)
# ==========================================
st.title("🛒 Termômetro Logístico E-commerce")
st.write("Compare sua operação com os benchmarks de 2026 e descubra quanto dinheiro está ficando na mesa.")

if st.session_state.etapa == 1:
    st.subheader("Passo 1: Seus Números")
    
    segmento = st.selectbox("Segmento Principal:", list(DEVOLUCAO_POR_SEGMENTO.keys()))
    fat_mensal = st.number_input("Faturamento Mensal Estimado (R$):", min_value=0, step=100000)
    vol_pedidos = st.number_input("Volume de Pedidos/mês:", min_value=0, step=100)
    custo_frete = st.number_input("Custo Atual de Frete por Pedido (R$):", min_value=0.0, step=1.0)
    
    if st.button("Calcular meu GAP contra o mercado"):
        if fat_mensal > 0 and vol_pedidos > 0 and custo_frete > 0:
            st.session_state.segmento = segmento
            st.session_state.fat_mensal = fat_mensal
            st.session_state.vol_pedidos = vol_pedidos
            st.session_state.custo_frete = custo_frete
            st.session_state.etapa = 2
            st.rerun()
        else:
            st.warning("Preencha todos os campos com valores maiores que zero para uma análise real.")

elif st.session_state.etapa == 2:
    st.subheader("🔒 Cruzamento Finalizado!")
    st.write("Cruzamos seus dados com o nosso Raio-X Setorial E-commerce (2026).")
    st.info("Para revelar seu GAP financeiro e proteger os dados contra bots, informe seu e-mail de trabalho.")
    
    email_lead = st.text_input("Seu E-mail Corporativo:")
    
    if st.button("Revelar Meu Diagnóstico"):
        if "@" in email_lead and "." in email_lead:
            with st.spinner("Gravando e calculando os GAPs..."):
                sucesso = salvar_lead_no_sheets(
                    email_lead, 
                    st.session_state.segmento, 
                    st.session_state.fat_mensal, 
                    st.session_state.custo_frete
                )
                if sucesso:
                    st.session_state.etapa = 3
                    st.rerun()
        else:
            st.error("Insira um e-mail válido para continuar.")

elif st.session_state.etapa == 3:
    st.success("Diagnóstico Gerado com Sucesso!")
    
    segmento = st.session_state.segmento
    fat_anual = st.session_state.fat_mensal * 12
    vol_pedidos_ano = st.session_state.vol_pedidos * 12
    custo_frete_atual = st.session_state.custo_frete
    
    frete_benchmark_p50 = obter_benchmark_frete(fat_anual)
    
    custo_frete_anual_cliente = custo_frete_atual * vol_pedidos_ano
    custo_frete_anual_ideal = frete_benchmark_p50 * vol_pedidos_ano
    economia_anual_possivel = custo_frete_anual_cliente - custo_frete_anual_ideal

    st.subheader("📊 Seu GAP na Última Milha")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Seu Frete Médio/Pedido", f"R$ {custo_frete_atual:.2f}")
    with col2:
        st.metric("Benchmark P50 (Seu Porte)", f"R$ {frete_benchmark_p50:.2f}", delta="O Ideal")

    if economia_anual_possivel > 0:
        st.error(f"🚨 **ALERTA DE DESPERDÍCIO:** Você está deixando **R$ {economia_anual_possivel:,.2f}** na mesa todo ano apenas em ineficiência de frete.")
        st.write("Nossa análise sugere que empresas do seu faturamento podem chegar no benchmark renegociando SLAs ou ajustando a malha de couriers.")
    else:
        st.success("✅ **PARABÉNS:** Seu custo de frete está dentro ou melhor que a média (P50) do mercado para o seu porte!")
    
    st.write("---")
    
    taxa_dev_media = DEVOLUCAO_POR_SEGMENTO[segmento] * 100
    st.subheader("⚠️ Atenção à Logística Reversa")
    st.write(f"Você atua no segmento de **{segmento}**. O mercado relata uma taxa de devolução média de **{taxa_dev_media:.1f}%** nesta categoria.")
    st.write("Se a sua taxa estiver acima disso, seu lucro está sendo corroído duas vezes (frete de ida e frete de volta).")
    
    st.write("---")
    
    st.markdown("""
    ### Chegou a hora de agir
    O *Termômetro Logístico* é apenas a ponta do iceberg. Nós montamos análises completas e planos de ação para recuperar esse dinheiro.
    """)
    url_diagnostico = "https://www.loginexo.com.br/diagnostico-ecommerce"
    st.markdown(f'<a href="{url_diagnostico}" target="_blank"><button style="background-color:#004b93;color:white;padding:15px;border:none;border-radius:5px;width:100%;font-size:18px;font-weight:bold;cursor:pointer;">Quero um Raio-X Profundo da Minha Operação</button></a>', unsafe_allow_html=True)
