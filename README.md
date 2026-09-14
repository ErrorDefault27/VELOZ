# Controle de estoque de restaurante

Aplicação local para registrar a fotografia de estoque de ingredientes em um período e gerar uma lista de compras conforme consumo, validade e falta antecipada. O backend Django concentra persistência, validações e regras de reposição; o React consome somente a API e apresenta os resultados.

## Identificação

- Nome: Edgar Cauã Mota da Anunciação
- Matrícula: `04160900`
- Repositório: [github.com/ErrorDefault27/VELOZ](https://github.com/ErrorDefault27/VELOZ)

## Funcionalidades

- Cadastro, consulta, edição e exclusão de ingredientes.
- Unidades `Kg`, `L` e `un`.
- Estoque atual calculado como quantidade inicial menos consumo.
- Validação de consumo, quantidades, precisão e falta antecipada.
- Lista de compras por data de referência.
- Motivo da reposição e texto pronto no formato `Comprar: <quantidade> <unidade> de <ingrediente>`.
- Exclusão automática de compras iguais ou inferiores a zero.
- Interface responsiva com estados de carregamento, erro e lista vazia.
- Django Admin como apoio opcional.
- Comando idempotente para carregar cinco exemplos.

## Regras de negócio

1. Validade anterior à referência significa vencido; na própria data o ingrediente ainda é válido.
2. Vencimento tem prioridade: o estoque aproveitável passa a zero e a compra é a meta completa.
3. Se o ingrediente válido acabou antes do fim do mês, a compra é o consumo multiplicado por `1,20`.
4. Nos demais casos, a compra é `max(meta - estoque atual, 0)`.
5. O cálculo não altera meta, estoque ou qualquer registro.
6. Compras em `un` são arredondadas para cima ao inteiro.
7. Compras em `Kg` e `L` são arredondadas para cima a duas casas decimais.

Exemplos com ingrediente válido:

| Situação | Resultado |
| --- | --- |
| Meta `20 Kg`, inicial `20 Kg`, consumo `8 Kg` | Estoque atual `12 Kg`; comprar `8 Kg`. |
| Meta `10 Kg`, inicial `10 Kg`, consumo `10 Kg`, sem falta antecipada | Comprar `10 Kg`. |
| Inicial `10 Kg`, consumo `10 Kg`, com falta antecipada | Comprar `12 Kg`. |
| Inicial `3 un`, consumo `3 un`, com falta antecipada | `3 × 1,20 = 3,6`; comprar `4 un`. |
| Estoque atual igual ou superior à meta | Nada a comprar. |

Se a meta for `20 Kg` e o ingrediente estiver vencido, a compra será `20 Kg`, independentemente da sobra ou da marcação de falta antecipada.

Todas as regras usam `Decimal`, nunca `float`. Quantidades aceitam até 12 dígitos no total e três casas decimais, no intervalo de `0` a `999999999.999`. Ingredientes medidos em `un` exigem quantidades inteiras.

## Limitação do modelo

Cada registro é uma única fotografia do ingrediente no período avaliado. Não existem entradas intermediárias, lotes, movimentações completas ou histórico mensal. Como não há entradas adicionais, o estoque atual é sempre `quantidade inicial - consumo` e não existe como campo editável.

## Stack e versões

- Python 3.14.x — validado com Python 3.14.6.
- Django 6.1.1.
- Django REST Framework 3.18.1.
- SQLite incluído no Python.
- Node.js 24.x LTS — exigido pelo `package.json` e validado com 24.21.0.
- npm 11.x — validado com 11.19.0.
- React 19, TypeScript 6 e Vite 8, instalados conforme `package-lock.json`.
- CSS próprio, sem biblioteca de componentes.

Não é necessário Docker, banco externo ou serviço de terceiros.

## Estrutura resumida

```text
backend/
  config/                  configurações e rotas principais do Django
  health/                  endpoint de saúde
  inventory/               modelo, validações, serviço, API, Admin e testes
  manage.py
  requirements.txt
frontend/
  src/components/          formulário, tabela e lista de compras
  src/api.ts               chamadas HTTP centralizadas
  src/types.ts             contrato TypeScript da API
  package.json
  package-lock.json
```

## Instalação do zero no Windows PowerShell

### 1. Instale as ferramentas necessárias

Instale estas ferramentas antes de baixar o projeto:

1. **Git para Windows:** baixe em [git-scm.com/download/win](https://git-scm.com/download/win) e conclua a instalação com as opções padrão. O Git é necessário para clonar e posteriormente publicar o repositório. Se você recebeu o projeto como arquivo ZIP, ele não é necessário apenas para executar a aplicação.
2. **Python 3.14, 64 bits:** baixe em [python.org/downloads/windows](https://www.python.org/downloads/windows/). No início do instalador, marque **Add python.exe to PATH** e mantenha a instalação do `pip` habilitada.
3. **Node.js 24 LTS, 64 bits:** baixe o instalador `.msi` da linha 24 em [nodejs.org/download](https://nodejs.org/en/download). A instalação padrão já inclui o npm. Este projeto exige Node `24.x`; não use Node 25 ou outra versão fora desse intervalo.

Depois das instalações, feche e abra um novo PowerShell para que o `PATH` seja atualizado. Confirme uma ferramenta por vez:

```powershell
git --version
python --version
node --version
npm.cmd --version
```

O resultado do Python deve começar com `Python 3.14` e o do Node com `v24`. Se `python` ou `node` não for reconhecido, reabra o terminal; se o problema continuar, execute novamente o instalador e habilite a inclusão no `PATH`.

> **Backend e frontend usam ambientes independentes.** O `.venv` contém apenas Python e as dependências do Django; Node.js e npm são instalados no Windows e usados pelo React. O prefixo `(.venv)` indica ativação naquele terminal, mas ela não é obrigatória quando o comando chama `.\.venv\Scripts\python.exe` diretamente.

Salvo quando houver a instrução `Set-Location .\frontend`, execute os comandos a partir da raiz que contém as pastas `backend` e `frontend`.

### 2. Obtenha o projeto e entre na pasta correta

Para clonar o repositório público:

```powershell
Set-Location "C:\pasta\onde\salvar"
git clone "https://github.com/ErrorDefault27/VELOZ.git"
Set-Location ".\VELOZ"
```

Também é possível baixar o ZIP pelo GitHub, extrair seu conteúdo e abrir o PowerShell na pasta extraída. A pasta correta é aquela que contém `README.md`, `backend` e `frontend`.

Confira antes de continuar:

```powershell
Get-ChildItem
```

### 3. Crie o ambiente virtual do backend

Na raiz do projeto, crie um ambiente Python isolado chamado `.venv`:

```powershell
python -m venv .venv
```

Instale as dependências usando diretamente o Python do ambiente:

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\backend\requirements.txt
```

O prompt não precisa mostrar `(.venv)`, pois o caminho explícito seleciona o Python correto. Se preferir ativar o ambiente, execute `.\.venv\Scripts\Activate.ps1` e passe a usar `python` no lugar de `.\.venv\Scripts\python.exe`. A ativação vale somente para o terminal atual; se for bloqueada pela política do PowerShell, continue com o caminho explícito sem alterar a política do Windows.

### 4. Prepare o banco de dados

Crie o banco SQLite local e aplique as migrações versionadas:

```powershell
.\.venv\Scripts\python.exe .\backend\manage.py migrate
```

Para preencher a demonstração com cinco ingredientes, execute:

```powershell
.\.venv\Scripts\python.exe .\backend\manage.py carregar_demo
```

O carregamento é opcional e idempotente: pode ser repetido sem apagar nem sobrescrever registros existentes com os mesmos nomes. As datas dos exemplos são calculadas em relação ao dia da execução.

### 5. Instale o frontend

Entre na pasta do React e instale exatamente as versões registradas no `package-lock.json`:

```powershell
Set-Location .\frontend
npm.cmd ci
Set-Location ..
```

Use `npm.cmd` no PowerShell para evitar problemas quando a execução de `npm.ps1` estiver desabilitada. Para uma instalação reproduzível, preserve o lockfile e prefira `npm.cmd ci` a `npm install`.

### 6. Confirme que a instalação terminou corretamente

Ainda na raiz do projeto, execute:

```powershell
.\.venv\Scripts\python.exe .\backend\manage.py check
Set-Location .\frontend
npm.cmd run build
Set-Location ..
```

O Django deve informar que não encontrou problemas e o Vite deve concluir o build sem erros. O diretório `frontend/dist` gerado é local e ignorado pelo Git.

## Execução local

São necessários dois terminais PowerShell simultâneos. O primeiro mantém o backend Django ativo e o segundo mantém o frontend Vite ativo. Fechar um desses terminais interrompe o respectivo servidor.

| Terminal | Diretório de trabalho | Ambiente necessário | Porta |
| --- | --- | --- | --- |
| Backend | raiz do projeto | Python do `.venv` | `8000` |
| Frontend | pasta `frontend` | Node.js 24 e npm; `.venv` não é necessário | `5173` |

Nos comandos seguintes, substitua `C:\caminho\para\NOME_DO_REPOSITORIO` pelo local onde o projeto foi salvo. Em seu ambiente atual, por exemplo, a raiz é `E:\proj\VELOZ`.

### Terminal 1 — backend Django

```powershell
Set-Location "C:\caminho\para\NOME_DO_REPOSITORIO"
.\.venv\Scripts\python.exe .\backend\manage.py runserver 127.0.0.1:8000
```

Não é necessário ativar o `.venv`, pois seu executável já foi indicado. Caso ele esteja ativado, `python .\backend\manage.py runserver 127.0.0.1:8000` é equivalente. Mantenha o terminal aberto; a mensagem `Starting development server at http://127.0.0.1:8000/` confirma que o backend está em execução.

### Terminal 2 — frontend React/Vite

```powershell
Set-Location "C:\caminho\para\NOME_DO_REPOSITORIO"
Set-Location .\frontend
npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

O segundo terminal não precisa exibir `(.venv)`. Se `node` ou `npm.cmd` não for reconhecido, o Node.js 24 não está instalado ou ainda não foi adicionado ao `PATH`; retorne à etapa 1 antes de prosseguir.

### Endereços locais

- Interface React: `http://127.0.0.1:5173/`
- API: `http://127.0.0.1:8000/api/`
- Health check: `http://127.0.0.1:8000/api/health/`
- Django Admin: `http://127.0.0.1:8000/admin/`

O React usa URLs relativas `/api`; durante o desenvolvimento, o Vite encaminha essas requisições para `127.0.0.1:8000`.

Não use `0.0.0.0` nem exponha as portas na rede. A aplicação é uma demonstração local, sem autenticação na API e sem CORS habilitado.

## Superusuário opcional

Para acessar o Django Admin, crie um usuário administrativo depois das migrações:

```powershell
.\.venv\Scripts\python.exe .\backend\manage.py createsuperuser
```

Esse usuário protege apenas o Admin. Os endpoints da demonstração continuam sem autenticação e restritos ao uso local.

## Testes e verificações

Na raiz do projeto:

```powershell
.\.venv\Scripts\python.exe .\backend\manage.py check
.\.venv\Scripts\python.exe .\backend\manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe .\backend\manage.py test inventory health
```

No frontend:

```powershell
Set-Location .\frontend
npm.cmd run lint
npm.cmd run build
Set-Location ..
```

O build gera arquivos estáticos em `frontend/dist/`. **Executar `npm.cmd run build` não inicia, inclui nem hospeda o backend Django.** Para a aplicação completa funcionar, o backend precisa ser executado separadamente ou, em uma futura implantação, publicado e roteado por infraestrutura própria.

## Limitações e hospedagem

- Uma fotografia por ingrediente e período, sem lotes ou entradas intermediárias.
- SQLite local.
- API sem autenticação, destinada somente à demonstração local.
- Sem Docker ou serviços externos.
- Hospedagem não implementada; não existe URL pública da aplicação.
