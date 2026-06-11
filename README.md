# gestao-aa-offline

Projeto de extensão universitária focado em anonimato.

---

### 🚀 Como executar o sistema

**Para Windows (Pronto para uso - Portátil):**
1. Vá na aba **Releases** (no menu lateral direito desta página) e baixe o arquivo `Gestao_AA_Windows_Portable.zip`.
2. Extraia o conteúdo em qualquer pasta do seu computador.
3. Dê um duplo clique no arquivo `iniciar_sistema.bat`. O sistema configurará tudo sozinho, operando de forma isolada, sem necessidade de instalar o Python na máquina.

**Para Linux (Modo Desenvolvedor):**
1. Clone ou baixe os arquivos fonte deste repositório.
2. Dê permissão de execução com `chmod +x iniciar_sistema.sh`.
3. Rode o script. O ambiente virtual será criado e ativado automaticamente.

---

### 🔐 Hierarquia de Acessos e Conta Master

O sistema foi desenhado com um Controle de Acesso Baseado em Funções (RBAC) rigoroso, dividido em três camadas para garantir a segurança operacional e a privacidade dos dados:

**1. Nível Master (Suporte Técnico e Administração Global):**
* **Credencial de Acesso:** Criada utilizando um endereço de e-mail identificador genérico. O sistema não exige confirmação de rede, pois o texto opera apenas como uma string geradora de um hash criptográfico seguro (SHA-256).
* **Função:** O Master atua exclusivamente como o mantenedor do sistema. É responsável por autorizar a criação de novas instâncias de gestão (Unidades/ONGs) e possui a capacidade de resetar senhas de Gestores.
* **Isolamento de Dados (Privacy by Design):** A conta Master é bloqueada por código e não possui acesso às tabelas de pacientes, reuniões ou relatos. Isso garante que o desenvolvedor/mantenedor não atue como controlador de dados sensíveis.

**2. Nível Gestor (Administrador da Unidade):**
* **Credencial de Acesso:** Contas criadas estritamente com nomes institucionais (ex: `ong-centro`). Por segurança, o sistema bloqueia o uso do caractere `@` para estes usuários, evitando o armazenamento desnecessário de e-mails pessoais no banco de dados.
* **Função:** Gerencia a sua própria unidade de forma isolada. Pode cadastrar a equipe técnica (Palestrantes/Coordenadores), inativá-los, agendar reuniões e extrair relatórios anonimizados da respectiva unidade.

**3. Nível Palestrante (Operação de Ponta):**
* **Função:** Cadastra novos membros (utilizando estritamente códigos anônimos), registra presenças e insere relatos confidenciais. Possui permissão de escrita apenas nas reuniões sob sua coordenação, mas detém acesso de leitura ao histórico unificado do membro para garantir o amparo e a continuidade do acompanhamento.
