# Revisão humana metodológica dos sete casos de fronteira

**Estado:** revisão concluída. Cinco rótulos foram alterados e dois mantidos
no Gold humano congelado; os registros finais estão em
`data/final/specpath_gold_human_90.csv` e no respectivo manifesto.

## Objetivo

Esta revisão decidiu validade da unidade de análise e regras de precedência. Ela
não usa concordância automatizada como critério e não busca aumentar
artificialmente a acurácia de nenhum modelo.

## Regras metodológicas adotadas

1. **Coerência temporal obrigatória.** A ocorrência do caminho deve existir no
   artefato da tarefa no commit de referência. Se existir apenas em um snapshot
   posterior usado na extração, o pareamento referência–commit é inválido.
2. **Artefato gerado continua sendo arquivo.** Um caminho concreto dentro de um
   comando não se torna `non_file_reference` quando configuração de build,
   manifesto e regras de versionamento demonstram que ele é um artefato
   gerado. Sua ausência versionada pode ser esperada.
3. **Escopo precede ciclo de vida.** Quando evidência afirmativa coloca o
   caminho em outro repositório, `external_repository_reference` precede
   criar/modificar/remover. A intenção de criação descreve o que ocorre dentro
   do repositório externo, não muda o escopo da referência.
4. **Declaração de externo exige evidência positiva.** Ausência local,
   arquitetura presumida ou diferença de tecnologia não bastam. É necessário
   pelo menos um vínculo verificável: submódulo, link explícito para o
   repositório de implementação, declaração documental inequívoca ou
   correspondência do arquivo/conteúdo em repositório identificado.
5. **Exemplo pode continuar sendo referência externa.** Se o texto cita um
   arquivo concreto e ele é verificavelmente um exemplo de outro repositório,
   a classe é externa. `non_file_reference` fica reservada para nomes
   hipotéticos, placeholders e convenções sem arquivo externo identificado.

## Decisões adotadas

### F006 — `dist/cli.js`

- Fato: ausente no commit; `package.json` declara `./dist/cli.js` como binário,
  o build usa `tsup`, `dist/` é ignorado e a tarefa mostra sua execução.
- Questão: caminho em comando versus artefato gerado.
- Decisão: **manter `expected_absence_create`**.
- Justificativa: é um arquivo concreto e gerado, cuja ausência do controle de
  versão é explicada pelo processo de build. A palavra “create” deve abranger
  geração por build, mesmo que a tarefa em questão apenas documente a execução.

### F013 — `VersionsTab.test.tsx`

- Fato: a ocorrência existe no contexto de extração, mas não no arquivo
  completo `tasks.md` do commit `3bf471d9…`.
- Questão: unidade temporalmente incompatível.
- Decisão: **alterar para `inaccessible_or_invalid`**.
- Justificativa: o caminho não é citado pela tarefa naquele commit. Não é
  metodologicamente válido concluir que está problematicamente ausente com
  base em texto de outro snapshot.

### F024 — `src/components/transfers/columnDefinitions.ts`

- Fato: a instrução de centralização aparece no contexto de extração, mas não
  no `tasks.md` completo do commit `251d26c8…`.
- Questão: unidade temporalmente incompatível.
- Decisão: **alterar para `inaccessible_or_invalid`**.
- Justificativa: a criação seria clara no snapshot posterior, mas não é uma
  inferência válida para o commit associado ao registro.

### F025 — `src/lib/prisma.ts`

- Fato: a tarefa no commit manda modificar o arquivo; ele não existe na árvore.
  O README descreve `backend/src/lib/prisma.ts` como parte da estrutura local do
  mesmo projeto. Não há repositório externo identificado.
- Questão: evidência mínima para escopo externo.
- Decisão: **alterar para `confirmed_missing_problematic`**.
- Justificativa: os revisores inferiram um backend separado, mas a evidência do
  commit descreve um diretório local ausente. Sem vínculo positivo para outro
  repositório, a classe externa não é reproduzível.

### F037 — `internal/store/queries/tokens.sql`

- Fato: a instrução para escrever o arquivo aparece no contexto de extração,
  mas não no `tasks.md` completo do commit `c6233231…`.
- Questão: unidade temporalmente incompatível.
- Decisão: **alterar para `inaccessible_or_invalid`**.
- Justificativa: a referência–commit está desalinhada; não se deve transportar
  a intenção de criação de um snapshot posterior para o commit âncora.

### F040 — `Stages.java`

- Fato: a tarefa cita o padrão de `Stages.java`; o arquivo não é local, e a
  adjudicação localizou a implementação correspondente no repositório externo
  de exemplos do Embabel.
- Questão: exemplo documental versus arquivo externo concreto.
- Decisão: **manter `external_repository_reference`**.
- Justificativa: não é um nome hipotético. A referência aponta para um arquivo
  concreto e verificável de outro repositório; o uso como exemplo não elimina
  seu escopo externo.

### F064 — `e2e/playwright/fixtures/auth.fixture.ts`

- Fato: o repositório âncora se declara repositório de documentação e vincula
  explicitamente `ccradle/finding-a-bed-tonight` como monorepo de implementação.
  A tarefa manda adicionar a fixture de implementação.
- Questão: escopo externo versus intenção de criação.
- Decisão: **alterar para `external_repository_reference`**.
- Justificativa: pela ordem da árvore, escopo é decidido antes do ciclo de vida.
  O arquivo pode ser criado, mas será criado no repositório externo.

## Resultado no Gold congelado

| Caso | Rótulo antes da revisão | Rótulo no Gold congelado |
|---|---|---|
| F006 | `expected_absence_create` | `expected_absence_create` |
| F013 | `confirmed_missing_problematic` | `inaccessible_or_invalid` |
| F024 | `expected_absence_create` | `inaccessible_or_invalid` |
| F025 | `external_repository_reference` | `confirmed_missing_problematic` |
| F037 | `expected_absence_create` | `inaccessible_or_invalid` |
| F040 | `external_repository_reference` | `external_repository_reference` |
| F064 | `expected_absence_create` | `external_repository_reference` |

As cinco alterações foram registradas como correções humanas metodológicas
após verificar a proveniência, não como substituições automáticas por rótulos
da LLM. O manifesto preserva os identificadores corrigidos e o Gold congelado
contém as decisões usadas na comparação reportada.
