Proposta de Projeto: Sistema Integrado de Gestão e Acesso ao Restaurante Universitário (RU) da UnB
Objetivo Principal
Desenvolver um sistema de banco de dados para otimizar o fluxo de usuários do Restaurante Universitário da UnB, facilitando a vida acadêmica por meio da gestão de saldos, análise de horários de pico e a implementação de um sistema de "Fast Pass" focado em equidade.

Justificativa e Impacto
O RU é um pilar da permanência estudantil, mas o enfrentamento de filas longas é um problema crônico. O projeto visa mitigar esse desgaste diário através de um gerenciamento inteligente. Em respeito à natureza pública e democrática da universidade, o sistema rejeita dinâmicas de "fura-fila" baseadas em poder aquisitivo (pay-to-win). Em vez disso, propõe um modelo probabilístico justo para a distribuição de passes rápidos.

Funcionalidades e Regras de Negócio Centrais

Gestão de Refeições e Saldos: Controle completo do histórico de acessos na catraca, recarga de créditos e categorias de assistência estudantil.

Roleta de Probabilidade Ponderada (Fast Pass): O diferencial do sistema. A distribuição do acesso rápido é feita de forma algorítmica, onde o tempo que um estudante passa sem ganhar atua como um peso matemático no sorteio. Quanto maior o tempo de espera, maiores as chances matemáticas de ser contemplado.

Inteligência de Fluxo: Consolidação de dados para fornecer aos alunos estatísticas sobre os melhores horários para frequentar o RU em cada dia da semana.

Aderência à Disciplina (Bancos de Dados)
O escopo do projeto atende perfeitamente à especificação técnica exigida. A diversidade de informações garante a criação de mais de 10 entidades consistentes. A lógica complexa do sorteio probabilístico exigirá a criação de Procedures dedicadas, enquanto a cobrança em tempo real no momento da catraca será a oportunidade ideal para a implementação de Triggers, garantindo a integridade dos dados e o uso avançado do SGBD.

---

## Rodando o projeto

### Front End

Para servir as páginas do Front End rode o seguinte comando:

```
python -m http.server --directory frontend
```

### Back End

Para rodar o servidor Back End, é necessário ter um servidor MySQL rodando e python instalado.
As configurações (`DB_USER` e `DB_PASSWORD`) para conectar com o servidor MySQL devem estar em `backend/.env`.

Com isso, os seguintes comandos devem ser rodados:

```
cd backend

python -m venv .venv  (Se não funcionar, teste: python3 -m venv .venv)

# Linux
source .venv/bin/activate

# Windows cmd
.venv\Scripts\activate.bat

# Windows powershell
.venv\Scripts\Activate.ps1
```

```
pip install fastapi uvicorn python-dotenv mysql-connector-python
```

```
uvicorn main:app --reload
```


