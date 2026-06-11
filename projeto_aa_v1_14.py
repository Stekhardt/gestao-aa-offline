import streamlit as st
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema de Gestão AA", page_icon="🤝", layout="wide")

# E-mail Master oculto
MASTER_EMAIL = "gestao_aa@admin.com"

# --- FUNÇÕES DE SEGURANÇA ---
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

MASTER_HASH = make_hashes(MASTER_EMAIL)

# --- CONEXÃO COM O BANCO DE DADOS ---
@st.cache_resource
def init_db():
    conn = sqlite3.connect("aa_sistema_v5.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT UNIQUE, password TEXT, 
                  perfil TEXT, parent_id INTEGER, pergunta_seg TEXT, resposta_seg TEXT, ativo INTEGER DEFAULT 1)''')
    c.execute('''CREATE TABLE IF NOT EXISTS ong 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, nome TEXT, cidade TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS palestrantes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, conta_id INTEGER, nome TEXT, especialidade TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS pacientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, codigo_anonimo TEXT, data_ingresso TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reunioes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, data TEXT, horario_inicio TEXT, horario_fim TEXT, palestrante_id INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS presencas 
                 (reuniao_id INTEGER, paciente_id INTEGER, status TEXT, PRIMARY KEY (reuniao_id, paciente_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS relatos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, reuniao_id INTEGER, paciente_id INTEGER, 
                  anotacao TEXT, data_registro TEXT)''')
    conn.commit()
    conn.close()

init_db()

def run_query(query, params=(), fetch="all"):
    conn = sqlite3.connect("aa_sistema_v5.db")
    c = conn.cursor()
    c.execute(query, params)
    if fetch == "all":
        data = c.fetchall()
    elif fetch == "one":
        data = c.fetchone()
    else:
        data = None
    conn.commit()
    conn.close()
    return data

# --- LÓGICA DE SESSÃO ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_id'] = None
    st.session_state['username'] = ""
    st.session_state['perfil'] = ""
    st.session_state['parent_id'] = 0

# ==================== ESTADO 1: USUÁRIO DESLOGADO ====================
if not st.session_state['logged_in']:
    st.sidebar.title("🤝 Gestão AA")
    st.sidebar.caption("Projeto de Extensão Universitária")
    st.sidebar.divider()
    modo_acesso = st.sidebar.radio("Navegação:", ["Entrar", "Criar Conta de ONG", "Esqueci minha Senha"])
    
    st.title("🤝 Plataforma de Gestão AA")
    st.markdown("---")
    
    if modo_acesso == "Entrar":
        st.subheader("🔐 Acesso Seguro")
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type='password')
        if st.button("Fazer Login"):
            user_check = run_query("SELECT id, perfil, parent_id, ativo FROM usuarios WHERE user = ?", (username,), fetch="one")
            if user_check:
                pass_check = run_query("SELECT id FROM usuarios WHERE user = ? AND password = ?", (username, make_hashes(password)), fetch="one")
                if pass_check:
                    if user_check[3] == 0: 
                        st.error("Conta inativada. Procure a gestão da unidade.")
                    else:
                        st.session_state.update({'logged_in': True, 'user_id': user_check[0], 'username': username, 'perfil': user_check[1], 'parent_id': user_check[2]})
                        st.rerun()
                else:
                    st.error("Senha incorreta.")
            else:
                st.warning("Usuário não encontrado.")

    elif modo_acesso == "Criar Conta de ONG":
        st.subheader("🏢 Registro de Nova Unidade (Gestor)")
        new_user = st.text_input("Usuário de Acesso")
        new_pwd = st.text_input("Senha", type="password")
        pergunta = st.text_input("Pergunta de Segurança (Ex: Qual o nome do seu primeiro animal?)")
        resposta = st.text_input("Resposta de Segurança", type="password")
        if st.button("Registrar Unidade"):
            if new_user and new_pwd and pergunta and resposta:
                perfil = 'Master' if make_hashes(new_user.strip()) == MASTER_HASH else 'Gestor'
                if '@' in new_user and perfil != 'Master': 
                    st.error("Erro de formato: Não use '@'. Ex: ong-centro."); st.stop()
                try:
                    run_query("INSERT INTO usuarios (user, password, perfil, parent_id, pergunta_seg, resposta_seg, ativo) VALUES (?, ?, ?, ?, ?, ?, 1)", 
                              (new_user, make_hashes(new_pwd), perfil, 0, pergunta, make_hashes(resposta)), fetch="none")
                    if perfil == 'Master':
                        st.success("Conta Master ativada com sucesso! Vá em 'Entrar'.")
                    else:
                        st.success("Conta de ONG criada com sucesso! Vá em 'Entrar' para configurar sua unidade.")
                except: 
                    st.error("Este usuário já existe no sistema.")
            else:
                st.warning("Preencha todos os campos.")

    elif modo_acesso == "Esqueci minha Senha":
        st.subheader("🔑 Recuperação de Acesso")
        rec_user = st.text_input("Qual o seu usuário?")
        if rec_user:
            user_data = run_query("SELECT id, pergunta_seg, resposta_seg FROM usuarios WHERE user = ?", (rec_user,), fetch="one")
            if user_data:
                st.info(f"Pergunta de Segurança: {user_data[1]}")
                rec_resp = st.text_input("Resposta:", type="password")
                nova_senha = st.text_input("Nova Senha:", type="password")
                if st.button("Redefinir Senha"):
                    if make_hashes(rec_resp) == user_data[2]:
                        run_query("UPDATE usuarios SET password = ? WHERE id = ?", (make_hashes(nova_senha), user_data[0]), fetch="none")
                        st.success("Senha atualizada com sucesso!")
                    else:
                        st.error("Resposta incorreta.")
            else:
                st.warning("Usuário não encontrado.")

# ==================== ESTADO 2: USUÁRIO LOGADO ====================
else:
    u_id = st.session_state['user_id'] if st.session_state['perfil'] == 'Gestor' else st.session_state['parent_id']
    if st.session_state['perfil'] == 'Master': u_id = 0
        
    st.sidebar.title("🤝 Gestão AA")
    st.sidebar.caption(f"👤 Logado como: **{st.session_state['username']}** ({st.session_state['perfil']})")
    
    if st.session_state['perfil'] != 'Master':
        ong = run_query("SELECT nome, cidade FROM ong WHERE user_id = ? LIMIT 1", (u_id,), fetch="one")
        st.sidebar.caption(f"📍 Unidade: **{ong[0] if ong else 'Pendente de configuração'}**")
            
    if st.sidebar.button("Sair / Logout"):
        st.session_state.update({'logged_in': False, 'user_id': None, 'username': "", 'perfil': ""})
        st.rerun()
        
    st.sidebar.divider()
    opcoes = ["🛠️ Painel Master"] if st.session_state['perfil'] == 'Master' else \
             ["🏠 Painel da ONG & Palestrantes", "👥 Cadastro de Membros", "📅 Agenda & Presença", "📝 Relatos do Palestrante", "📈 Evolução do Membro"]
    
    if st.session_state['perfil'] == 'Palestrante': 
        opcoes.pop(0)
    
    menu = st.sidebar.radio("Selecione uma Tela:", opcoes)

    # --- PAINEL MASTER ---
    if menu == "🛠️ Painel Master":
        st.title("🛠️ Painel Administrativo Global")
        st.error("Acesso de Nível Máximo. Os dados exibidos referem-se apenas a Gestores. Pacientes são inacessíveis por design de segurança.")
        gestores = run_query("SELECT id, user FROM usuarios WHERE perfil = 'Gestor'")
        if gestores:
            for g in gestores:
                c1, c2 = st.columns([4, 1])
                o = run_query("SELECT nome, cidade FROM ong WHERE user_id = ?", (g[0],), fetch="one")
                c1.info(f"Usuário: {g[1]} | ONG: {o[0] + ' (' + o[1] + ')' if o else 'N/A'}")
                if c2.button("Reset Senha", key=f"r_{g[0]}"):
                    run_query("UPDATE usuarios SET password = ? WHERE id = ?", (make_hashes("123456"), g[0]), fetch="none")
                    st.success("Senha temporária gerada: 123456")
        else:
            st.write("Nenhum Gestor cadastrado no sistema.")

    # --- PAINEL ONG & PALESTRANTES ---
    elif menu == "🏠 Painel da ONG & Palestrantes":
        st.title("🏠 Gestão da Unidade")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Configurar Unidade/ONG")
            ongs_cadastradas = run_query("SELECT id, nome, cidade FROM ong WHERE user_id = ?", (u_id,))
            
            if not ongs_cadastradas:
                nome_ong = st.text_input("Nome do Grupo/ONG")
                cidade_ong = st.text_input("Cidade/Estado")
                if st.button("Salvar Unidade"):
                    if nome_ong and cidade_ong:
                        run_query("INSERT INTO ong (user_id, nome, cidade) VALUES (?, ?, ?)", (u_id, nome_ong, cidade_ong), fetch="none")
                        st.success("Unidade cadastrada com sucesso!")
                        st.rerun() 
                    else:
                        st.error("Preencha todos os campos.")
            else:
                st.success("✅ Unidade configurada com sucesso.")
                st.info(f"**{ongs_cadastradas[0][1]}** - {ongs_cadastradas[0][2]}")
                st.caption("A arquitetura permite apenas uma unidade por Gestor para garantir o isolamento total dos dados.")
                
                st.markdown("---")
                st.subheader("📥 Relatórios da Unidade")
                if st.button("Gerar Relatório Geral de Membros"):
                    df_membros = pd.DataFrame(run_query("SELECT id, codigo_anonimo, data_ingresso FROM pacientes WHERE user_id = ?", (u_id,)), columns=['ID', 'Código', 'Ingresso'])
                    st.download_button("Clique para Baixar (CSV)", df_membros.to_csv(index=False).encode('utf-8'), "relatorio_unidade.csv", "text/csv")

        with col2:
            st.subheader("Cadastrar Membro da Equipe (Palestrante)")
            nome_pal = st.text_input("Nome do Palestrante")
            esp_pal = st.text_input("Papel/Função (Ex: Coordenador, Psicólogo)")
            
            st.markdown("**🔑 Criar Acesso do Palestrante**")
            user_pal = st.text_input("Usuário de Login")
            pass_pal = st.text_input("Senha Inicial", type="password")
            perg_pal = st.text_input("Pergunta de Segurança (Para o palestrante recuperar a senha)")
            resp_pal = st.text_input("Resposta da Segurança", type="password")
            
            if st.button("Cadastrar Equipe"):
                if nome_pal and esp_pal and user_pal and pass_pal and perg_pal and resp_pal:
                    try:
                        run_query("INSERT INTO usuarios (user, password, perfil, parent_id, pergunta_seg, resposta_seg, ativo) VALUES (?, ?, ?, ?, ?, ?, 1)", 
                                  (user_pal, make_hashes(pass_pal), 'Palestrante', u_id, perg_pal, make_hashes(resp_pal)), fetch="none")
                        
                        nova_conta = run_query("SELECT id FROM usuarios WHERE user = ?", (user_pal,), fetch="one")
                        
                        run_query("INSERT INTO palestrantes (user_id, conta_id, nome, especialidade) VALUES (?, ?, ?, ?)", 
                                  (u_id, nova_conta[0], nome_pal, esp_pal), fetch="none")
                        
                        st.success("Palestrante e Login cadastrados com sucesso!")
                    except Exception as e:
                        st.error("Erro: Este usuário de login já está em uso.")
                else:
                    st.error("Preencha todos os campos do formulário.")
            
            st.markdown("---")
            st.markdown("**Gestão da Equipe Cadastrada:**")
            
            pals_cadastrados = run_query("""SELECT p.id, p.nome, p.especialidade, u.id, u.user, u.ativo 
                                            FROM palestrantes p JOIN usuarios u ON p.conta_id = u.id 
                                            WHERE p.user_id = ?""", (u_id,))
            if pals_cadastrados:
                for p in pals_cadastrados:
                    c_info, c_reset, c_status, c_del = st.columns([4, 2, 2, 2])
                    icone = "🟢" if p[5] == 1 else "🔴"
                    c_info.markdown(f"{icone} **{p[1]}** ({p[2]}) | Login: `{p[4]}`")
                    
                    if c_reset.button("Reset Senha", key=f"res_{p[0]}"):
                        run_query("UPDATE usuarios SET password = ? WHERE id = ?", (make_hashes("123456"), p[3]), fetch="none")
                        st.success("Nova senha: 123456")
                        
                    if p[5] == 1:
                        if c_status.button("Inativar", key=f"ina_{p[0]}"):
                            run_query("UPDATE usuarios SET ativo = 0 WHERE id = ?", (p[3],), fetch="none")
                            st.rerun()
                    else:
                        if c_status.button("Ativar", key=f"ati_{p[0]}"):
                            run_query("UPDATE usuarios SET ativo = 1 WHERE id = ?", (p[3],), fetch="none")
                            st.rerun()
                            
                    if c_del.button("Excluir", key=f"del_{p[0]}"):
                        # CORREÇÃO: Mantém o registro do palestrante, mas anexa a tag (Excluído) no nome dele.
                        run_query("UPDATE palestrantes SET nome = nome || ' (Excluído)' WHERE id = ?", (p[0],), fetch="none")
                        # Deleta permanentemente apenas o acesso ao sistema
                        run_query("DELETE FROM usuarios WHERE id = ?", (p[3],), fetch="none")
                        st.rerun()
            else:
                st.write("Sem equipe.")

    # --- CADASTRO DE MEMBROS ---
    elif menu == "👥 Cadastro de Membros":
        st.title("👥 Gestão de Membros (Foco em Anonimato)")
        st.info("Para proteger a identidade no AA, utilize códigos (ex: AA-001, Membro-X) em vez de nomes reais.")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Novo Cadastro")
            cod_anonimo = st.text_input("Código Identificador Único")
            if st.button("Registrar Membro"):
                if cod_anonimo:
                    existe = run_query("SELECT id FROM pacientes WHERE user_id = ? AND codigo_anonimo = ?", (u_id, cod_anonimo), fetch="one")
                    if existe:
                        st.error(f"Erro: O membro '{cod_anonimo}' já existe nesta unidade.")
                    else:
                        hoje = datetime.now().strftime("%d/%m/%Y")
                        run_query("INSERT INTO pacientes (user_id, codigo_anonimo, data_ingresso) VALUES (?, ?, ?)", (u_id, cod_anonimo, hoje), fetch="none")
                        st.success(f"Membro '{cod_anonimo}' registrado com sucesso!")
                else:
                    st.error("Insira um código válido.")
                    
        with col2:
            st.subheader("Membros Cadastrados no Sistema")
            membros = run_query("SELECT id, codigo_anonimo, data_ingresso FROM pacientes WHERE user_id = ?", (u_id,))
            if membros:
                for m in membros:
                    st.text(f"ID: {m[0]} | Código: {m[1]} | Data de Ingresso: {m[2]}")
            else:
                st.write("Nenhum membro cadastrado ainda.")

    # --- AGENDA E PRESENÇA ---
    elif menu == "📅 Agenda & Presença":
        st.title("📅 Reuniões e Lista de Presença")
        
        tab1, tab2 = st.tabs(["Criar Reunião", "Marcar Presença"])
        
        with tab1:
            st.subheader("Agendar Nova Sessão")
            data_reuniao = st.date_input("Data da Reunião").strftime("%d/%m/%Y")
            
            col_hora1, col_hora2 = st.columns(2)
            with col_hora1:
                hora_inicio = st.time_input("Horário de Início").strftime("%H:%M")
            with col_hora2:
                hora_fim = st.time_input("Horário de Término").strftime("%H:%M")
            
            if st.session_state['perfil'] == 'Palestrante':
                meu_res = run_query("SELECT id, nome FROM palestrantes WHERE conta_id = ?", (st.session_state['user_id'],), fetch="one")
                if meu_res:
                    p_id = meu_res[0]
                    st.info(f"👤 Palestrante Responsável: **{meu_res[1]}** (Automático)")
                    st.caption("Como palestrante, você apenas pode agendar reuniões em seu próprio nome.")
                    
                    if st.button("Agendar Reunião"):
                        run_query("INSERT INTO reunioes (user_id, data, horario_inicio, horario_fim, palestrante_id) VALUES (?, ?, ?, ?, ?)", 
                                  (u_id, data_reuniao, hora_inicio, hora_fim, p_id), fetch="none")
                        st.success("Reunião agendada com sucesso!")
                else:
                    st.error("Erro ao localizar seu perfil de palestrante no sistema.")
                    
            else: # Gestor
                palestrantes = run_query("""SELECT p.id, p.nome FROM palestrantes p 
                                            JOIN usuarios u ON p.conta_id = u.id 
                                            WHERE p.user_id = ? AND u.ativo = 1""", (u_id,))
                lista_palestrantes = {p[1]: p[0] for p in palestrantes} if palestrantes else {}
                
                pal_selecionado = st.selectbox("Selecione o Palestrante/Coordenador", list(lista_palestrantes.keys())) if lista_palestrantes else None
                
                if st.button("Agendar Reunião"):
                    if pal_selecionado:
                        p_id = lista_palestrantes[pal_selecionado]
                        run_query("INSERT INTO reunioes (user_id, data, horario_inicio, horario_fim, palestrante_id) VALUES (?, ?, ?, ?, ?)", 
                                  (u_id, data_reuniao, hora_inicio, hora_fim, p_id), fetch="none")
                        st.success("Reunião agendada com sucesso!")
                    else:
                        st.error("Cadastre um palestrante ativo primeiro.")
                    
        with tab2:
            st.subheader("Controle de Frequência")
            
            filtro_presenca = st.radio("Filtrar Reuniões:", ["📅 Próximas Reuniões (e Hoje)", "🕰️ Reuniões Passadas"], horizontal=True, key="filtro_presenca")
            
            reunioes = run_query("""SELECT r.id, r.data, r.horario_inicio, r.horario_fim, IFNULL(p.nome, 'Palestrante Excluído'), r.palestrante_id 
                                    FROM reunioes r LEFT JOIN palestrantes p ON r.palestrante_id = p.id 
                                    WHERE r.user_id = ? ORDER BY r.id DESC""", (u_id,))
            
            if reunioes:
                hoje_datetime = datetime.now()
                reunioes_filtradas = {}
                
                for r in reunioes:
                    try:
                        dt_reuniao = datetime.strptime(f"{r[1]} {r[2]}", "%d/%m/%Y %H:%M")
                    except:
                        dt_reuniao = hoje_datetime
                        
                    texto_exibicao = f"ID {r[0]} - {r[1]} ({r[2]} às {r[3]}) - {r[4]}"
                    
                    if filtro_presenca == "📅 Próximas Reuniões (e Hoje)" and dt_reuniao.date() >= hoje_datetime.date():
                        reunioes_filtradas[texto_exibicao] = (r[0], r[5])
                    elif filtro_presenca == "🕰️ Reuniões Passadas" and dt_reuniao.date() < hoje_datetime.date():
                        reunioes_filtradas[texto_exibicao] = (r[0], r[5])

                if reunioes_filtradas:
                    reu_selecionada = st.selectbox("Escolha a Reunião:", list(reunioes_filtradas.keys()))
                    r_id, r_pal_id = reunioes_filtradas[reu_selecionada]
                    
                    meu_pal_id = None
                    if st.session_state['perfil'] == 'Palestrante':
                        meu_res = run_query("SELECT id FROM palestrantes WHERE conta_id = ?", (st.session_state['user_id'],), fetch="one")
                        if meu_res:
                            meu_pal_id = meu_res[0]

                    pode_editar_presenca = False
                    if st.session_state['perfil'] == 'Palestrante' and meu_pal_id == r_pal_id:
                        pode_editar_presenca = True
                        
                    if not pode_editar_presenca:
                        st.warning("👀 **Modo Leitura / Auditoria.** Apenas o palestrante responsável por esta reunião pode alterar a lista de presença.")
                    
                    pacientes = run_query("SELECT id, codigo_anonimo FROM pacientes WHERE user_id = ?", (u_id,))
                    
                    if pacientes:
                        st.write("Marque a presença de cada membro:")
                        for pac in pacientes:
                            p_id_pac = pac[0]
                            p_cod = pac[1]
                            
                            status_atual = run_query("SELECT status FROM presencas WHERE reuniao_id = ? AND paciente_id = ?", (r_id, p_id_pac), fetch="one")
                            index_default = 0
                            if status_atual:
                                if status_atual[0] == "Presente":
                                    index_default = 1
                                elif status_atual[0] == "Ausente":
                                    index_default = 2
                                elif status_atual[0] == "Não Avaliado":
                                    index_default = 0
                                
                            status = st.radio(f"Membro: {p_cod}", ["Não Avaliado", "Presente", "Ausente"], index=index_default, key=f"p_{r_id}_{p_id_pac}", disabled=not pode_editar_presenca)
                            
                            if pode_editar_presenca:
                                run_query("""INSERT INTO presencas (reuniao_id, paciente_id, status) 
                                             VALUES (?, ?, ?) ON CONFLICT(reuniao_id, paciente_id) DO UPDATE SET status=excluded.status""", 
                                          (r_id, p_id_pac, status), fetch="none")
                        
                        if pode_editar_presenca:
                            st.success("Presenças atualizadas automaticamente no banco!")
                    else:
                        st.write("Nenhum membro cadastrado para listar.")
                else:
                    st.info("Nenhuma reunião encontrada para este filtro.")
            else:
                st.write("Nenhuma reunião agendada ainda.")

    # ==================== TELA 4: RELATOS DO PALESTRANTE ====================
    elif menu == "📝 Relatos do Palestrante":
        st.title("📝 Prontuário de Relatos Confidenciais")
        
        filtro_relatos = st.radio("Filtrar Reuniões:", ["📅 Próximas Reuniões (e Hoje)", "🕰️ Reuniões Passadas"], horizontal=True, key="filtro_relatos")
        
        reunioes = run_query("""SELECT r.id, r.data, r.horario_inicio, r.horario_fim, IFNULL(p.nome, 'Palestrante Excluído'), r.palestrante_id 
                                FROM reunioes r LEFT JOIN palestrantes p ON r.palestrante_id = p.id 
                                WHERE r.user_id = ? ORDER BY r.id DESC""", (u_id,))
        pacientes = run_query("SELECT id, codigo_anonimo FROM pacientes WHERE user_id = ?", (u_id,))
        
        if reunioes and pacientes:
            hoje_datetime = datetime.now()
            reunioes_filtradas = {}
            
            for r in reunioes:
                try:
                    dt_reuniao = datetime.strptime(f"{r[1]} {r[2]}", "%d/%m/%Y %H:%M")
                except:
                    dt_reuniao = hoje_datetime
                    
                texto_exibicao = f"ID {r[0]} - {r[1]} ({r[2]} às {r[3]}) - {r[4]}"
                
                if filtro_relatos == "📅 Próximas Reuniões (e Hoje)" and dt_reuniao.date() >= hoje_datetime.date():
                    reunioes_filtradas[texto_exibicao] = (r[0], r[5])
                elif filtro_relatos == "🕰️ Reuniões Passadas" and dt_reuniao.date() < hoje_datetime.date():
                    reunioes_filtradas[texto_exibicao] = (r[0], r[5])

            if reunioes_filtradas:
                reu_nome = st.selectbox("Selecione a Reunião:", list(reunioes_filtradas.keys()))
                reu_id, reu_pal_id = reunioes_filtradas[reu_nome]
                
                lista_pacientes = {p[1]: p[0] for p in pacientes}
                pac_id = lista_pacientes[st.selectbox("Selecione o Membro (Código Anônimo):", list(lista_pacientes.keys()))]
                
                st.markdown("---")
                
                meu_pal_id = None
                if st.session_state['perfil'] == 'Palestrante':
                    meu_res = run_query("SELECT id FROM palestrantes WHERE conta_id = ?", (st.session_state['user_id'],), fetch="one")
                    if meu_res:
                        meu_pal_id = meu_res[0]

                pode_escrever = False
                if st.session_state['perfil'] == 'Palestrante' and meu_pal_id == reu_pal_id:
                    pode_escrever = True
                    
                if pode_escrever:
                    st.caption("Você é o palestrante desta reunião. Adicione seu relato abaixo.")
                    anotacao = st.text_area("Anotações sobre o relato / estado emocional do membro:")
                    
                    if st.button("Salvar Anotação"):
                        if anotacao:
                            hoje = datetime.now().strftime("%d/%m/%Y %H:%M")
                            run_query("INSERT INTO relatos (user_id, reuniao_id, paciente_id, anotacao, data_registro) VALUES (?, ?, ?, ?, ?)", 
                                      (u_id, reu_id, pac_id, anotacao, hoje), fetch="none")
                            st.success("Relato salvo com sucesso no prontuário seguro!")
                        else:
                            st.error("Por favor, digite alguma anotação.")
                else:
                    st.warning("👀 **Modo Leitura / Auditoria.** Apenas o palestrante que conduziu esta reunião pode escrever novos relatos nela.")

                # --- HISTÓRICO VISUAL ---
                st.markdown("---")
                st.subheader(f"Histórico de Relatos do Membro nesta Reunião")
                
                historico = run_query("""SELECT r.data_registro, r.anotacao, reu.data, IFNULL(p.nome, 'Palestrante Excluído') 
                                         FROM relatos r 
                                         JOIN reunioes reu ON r.reuniao_id = reu.id 
                                         LEFT JOIN palestrantes p ON reu.palestrante_id = p.id
                                         WHERE r.paciente_id = ? AND r.user_id = ? AND reu.id = ? ORDER BY r.id DESC""", (pac_id, u_id, reu_id))
                if historico:
                    for h in historico:
                        st.info(f"**Data do Registro:** {h[0]} | **Sessão:** {h[2]} | **Responsável:** {h[3]}\n\n{h[1]}")
                else:
                    st.write("Sem registros históricos para este membro nesta reunião.")
            else:
                st.info("Nenhuma reunião encontrada para este filtro.")
        else:
            st.error("Certifique-se de ter reuniões e membros cadastrados no sistema.")

    # ==================== TELA 5: EVOLUÇÃO DO MEMBRO ====================
    elif menu == "📈 Evolução do Membro":
        st.title("📈 Evolução do Membro")
        st.caption("Visão consolidada do histórico, frequência e todos os relatos de um membro específico.")
        
        pacientes = run_query("SELECT id, codigo_anonimo, data_ingresso FROM pacientes WHERE user_id = ?", (u_id,))
        
        if pacientes:
            lista_pacientes = {f"{p[1]} (Ingresso: {p[2]})": p[0] for p in pacientes}
            pac_selecionado = st.selectbox("Selecione o Membro para análise:", list(lista_pacientes.keys()))
            pac_id = lista_pacientes[pac_selecionado]
            
            st.markdown("---")
            
            # --- MÉTRICAS DE FREQUÊNCIA ---
            st.subheader("📊 Resumo de Frequência")
            
            total_reunioes_res = run_query("SELECT COUNT(*) FROM reunioes WHERE user_id = ?", (u_id,), fetch="one")
            total_reunioes_ong = total_reunioes_res[0] if total_reunioes_res else 0
            
            presencas = run_query("SELECT status, COUNT(*) FROM presencas WHERE paciente_id = ? GROUP BY status", (pac_id,))
            
            total_presente = 0
            total_ausente = 0
            
            if presencas:
                for p in presencas:
                    if p[0] == "Presente": total_presente = p[1]
                    elif p[0] == "Ausente": total_ausente = p[1]
            
            total_nao_avaliado = total_reunioes_ong - total_presente - total_ausente
            taxa = f"{(total_presente / total_reunioes_ong * 100):.1f}%" if total_reunioes_ong > 0 else "N/A"
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Presente", total_presente)
            col2.metric("Ausente", total_ausente)
            col3.metric("Não Avaliado", total_nao_avaliado)
            col4.metric("Taxa de Presença", taxa)
            
            st.markdown("---")
            
            # --- GRÁFICO CORRIGIDO ---
            df_grafico = pd.DataFrame({
                "Status": ["1 - Presente", "2 - Ausente", "3 - Não Avaliado"], 
                "Quantidade": [total_presente, total_ausente, total_nao_avaliado]
            })
            st.bar_chart(df_grafico.set_index("Status"))
            
            st.markdown("---")
            
            # --- LINHA DO TEMPO GERAL E EXPORTAÇÃO ---
            st.subheader("📖 Linha do Tempo Completa de Relatos")
            
            historico_completo = run_query("""SELECT r.data_registro, r.anotacao, reu.data, IFNULL(p.nome, 'Palestrante Excluído') 
                                              FROM relatos r 
                                              JOIN reunioes reu ON r.reuniao_id = reu.id 
                                              LEFT JOIN palestrantes p ON reu.palestrante_id = p.id
                                              WHERE r.paciente_id = ? AND r.user_id = ? ORDER BY r.id DESC""", (pac_id, u_id))
            
            if historico_completo:
                df_exp = pd.DataFrame(historico_completo, columns=['Data Registro', 'Relato', 'Data Sessão', 'Palestrante Responsável'])
                st.download_button("Baixar Prontuário Completo (CSV)", df_exp.to_csv(index=False).encode('utf-8'), f"prontuario_{pac_selecionado.split(' ')[0]}.csv", "text/csv")
                st.write("")
                for h in historico_completo:
                    st.success(f"📅 **Sessão:** {h[2]} | ✍️ **Responsável:** {h[3]} | 🕒 **Registrado em:** {h[0]}\n\n{h[1]}")
            else:
                st.write("Sem registros históricos de relatos para este membro em toda a unidade.")
        else:
            st.warning("Nenhum membro cadastrado nesta unidade.")
