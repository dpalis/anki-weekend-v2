# Anki Weekend Addon v2.0

## Contexto do Projeto

### Visão Geral
Addon para Anki que pausa a apresentação de novos cards aos finais de semana, mantendo apenas reviews de cards já aprendidos. Permite que usuários descansem nos finais de semana sem acumular reviews atrasados.

### Requisitos Funcionais
- Pausar novos cards aos finais de semana (sábado e domingo)
- Manter reviews de cards já aprendidos
- Opção "modo viagem": desligar novos cards por período indeterminado
- Detecção automática de idioma (PT-BR ou ENG, fallback para ENG)

### Motivação para v2.0
A versão 1.0 sofreu de:
- Bugs recorrentes que não foram resolvidos definitivamente
- Código complexo e desorganizado após múltiplas correções
- Estrutura confusa e difícil de manter
- Dificuldade em expandir funcionalidades

A v2.0 é uma reescrita completa focada em **simplicidade, estabilidade e manutenibilidade**.

## Princípios Arquiteturais

### 0. PRINCÍPIO: Simplicidade Apropriada ⭐

**Começar sempre com a solução mais simples que funciona.**
**Adicionar complexidade APENAS quando necessário e JUSTIFICADO.**

#### Regras:

1. **Feature simples** (ex: este addon) → **Solução simples** (2-3 arquivos)
2. **Feature complexa** (ex: multi-API) → **Solução estruturada apropriada**
3. **SEMPRE questionar:** "Essa complexidade resolve problema REAL ou IMAGINÁRIO?"

#### Red Flags (sinais de over-engineering):

- ❌ Feature simples com estimativa > 5 dias
- ❌ Código "preparado para o futuro" sem necessidade clara
- ❌ Mais de 3 abstrações (classes/módulos) sem justificativa
- ❌ "Mas e se precisarmos..." sem caso de uso concreto
- ❌ Separação de arquivos quando total < 200 linhas

#### Evolução Natural:

```
v1.0: Simples, aprende sobre o problema REAL
  ↓
  [Usar em produção, coletar feedback]
  ↓
v2.0+: Adiciona estrutura onde v1.0 DOEU
  ↓
  Complexidade emerge de DORES REAIS, não de "boas práticas"
```

#### Decisão para Este Projeto (Anki Weekend Addon):

- **Complexidade do domínio:** BAIXA (pause cards + restore)
- **Solução apropriada:** SIMPLES (1 arquivo ~150 linhas)
- **Justificativa:** Lógica é trivial, over-engineering seria prejudicial
- **Estrutura aprovada:** `__init__.py` + `config.json` (2 arquivos)

---

### 1. Simplicidade Acima de Tudo
- Código deve ser óbvio à primeira leitura
- Evitar abstrações desnecessárias
- Preferir clareza sobre cleverness
- Se algo parece complicado, provavelmente está errado

### 2. Modularidade Apropriada
- Separação clara de responsabilidades **quando necessário**
- Cada módulo tem um propósito específico e bem definido
- Baixo acoplamento entre componentes
- **Regra:** Só separar em múltiplos arquivos se passar de ~200 linhas
- **Para este projeto:** 1 arquivo é suficiente

### 3. Estabilidade e Confiabilidade
- Código bem testado (testes manuais aceitáveis para projetos simples)
- Tratamento explícito de edge cases
- Logging apenas se necessário para debugging (não prematuro)
- Fail gracefully - nunca quebrar a experiência do Anki

### 4. Facilidade de Expansão
- Arquitetura que permite adicionar features **se precisar** (não "quando precisar")
- Código autodocumentado (nomes claros > comentários excessivos)
- Documentação clara de pontos de extensão **reais**

## Git Workflow (OBRIGATÓRIO)

### Regra de Ouro: NUNCA trabalhar diretamente na `main`

**SEMPRE use feature branches para qualquer implementação.**

#### Processo Padrão:

```bash
# 1. Garantir que main está atualizada
git checkout main
git pull origin main

# 2. Criar feature/fix branch com nome descritivo
git checkout -b feature/nome-descritivo  # ou fix/nome-bug

# 3. Implementar, testar, commitar na branch
git add .
git commit -m "feat: descrição"

# 4. Push branch para remote
git push -u origin feature/nome-descritivo

# 5. CRIAR PULL REQUEST (OBRIGATÓRIO)
gh pr create --title "feat: descrição" --body "Detalhes..."

# 6. Aguardar review de outra instância
# (Usar /compounding-engineering:review ou revisão manual)

# 7. Após aprovação do PR, mergear
gh pr merge <número>

# 8. Voltar para main e atualizar
git checkout main
git pull origin main

# 9. (Opcional) Deletar feature branch
git branch -d feature/nome-descritivo
```

#### 🚨 REGRA CRÍTICA: Pull Requests são OBRIGATÓRIOS

**NUNCA implemente mudanças diretamente sem criar PR primeiro.**

**Fluxo correto quando mudanças são propostas:**

1. **Receber proposta de mudança** (ex: issues de code review)
2. **Criar branch** (`fix/nome-descritivo`)
3. **Implementar mudanças**
4. **Commit na branch**
5. **Push para remote**
6. **CRIAR PR** ← OBRIGATÓRIO
7. **Aguardar review**
8. **Mergear após aprovação**

**❌ ERRADO:**
- Implementar mudanças direto na branch atual
- Commitar sem criar PR
- Mergear sem review

**✅ CORRETO:**
- Criar branch → Implementar → PR → Review → Merge

#### Nomenclatura de Branches:

- **Features:** `feature/nome-descritivo` (ex: `feature/v2-implementation`)
- **Bugfixes:** `fix/nome-do-bug` (ex: `fix/weekend-detection`)
- **Docs:** `docs/nome-doc` (ex: `docs/update-readme`)
- **Refactor:** `refactor/nome` (ex: `refactor/simplify-config`)

#### Por quê?

- ✅ **main sempre estável** - Código funcional garantido
- ✅ **Experimentação segura** - Pode quebrar à vontade na branch
- ✅ **Histórico limpo** - Commits organizados por propósito
- ✅ **Facilita review** - Isola mudanças para revisão
- ✅ **Preparado para CI/CD** - Se configurar depois, main nunca quebra

#### ❌ Red Flags:

- Commitar diretamente na `main` (exceto `.gitignore`, `README` inicial)
- Branches sem prefixo (`feature/`, `fix/`, etc.)
- Feature branches que vivem por semanas (mergear frequentemente)

---

## Stack Técnica

### Linguagem
- **Python 3.9+** (versão mínima suportada pelo Anki moderno)

### Ambiente
- **Anki 25.x** (versão alvo)
- **Anki API** (método de integração a ser determinado após pesquisa)

### Dependências
- Apenas dependências do próprio Anki (manter addon leve)
- Nenhuma biblioteca externa adicional

## Padrões de Código

### Nomenclatura
- **Funções**: `snake_case`, verbos descritivos (`filter_new_cards`, `is_weekend`)
- **Classes**: `PascalCase`, substantivos (`SchedulerManager`, `ConfigHandler`)
- **Constantes**: `UPPER_SNAKE_CASE` (`WEEKEND_DAYS`, `DEFAULT_CONFIG`)
- **Variáveis privadas**: prefixo `_` (`_cache`, `_internal_state`)

### Documentação
- Docstrings em todas as funções públicas
- Formato: breve descrição + args + returns + raises (se aplicável)
```python
def is_weekend(date=None):
    """
    Verifica se uma data é final de semana.

    Args:
        date: datetime object ou None (usa data atual)

    Returns:
        bool: True se for sábado ou domingo
    """
```

### Type Hints
- Usar type hints em todas as funções
- Facilita manutenção e catching de bugs

### Tratamento de Erros
- Catch específico, nunca `except Exception` genérico
- Log de erros para debugging
- Fallback graceful (em caso de erro, não bloquear funcionalidade do Anki)

### Testes
- Testes unitários para toda lógica core
- Mocks para APIs do Anki
- Testes de edge cases (meia-noite, mudança de timezone, etc.)
- Coverage mínimo de 80%

## Erros a Evitar (Lições da v1.0)

### 1. Não Modificar Estado do Anki de Forma Invasiva
❌ **Evitar**: Modificações que possam conflitar com outras funcionalidades
✅ **Fazer**: Integração limpa e não-invasiva

### 2. Não Criar Dependências Complexas
❌ **Evitar**: Módulos que dependem uns dos outros em círculo
✅ **Fazer**: Dependências unidirecionais e claras

### 3. Não Assumir Estado do Sistema
❌ **Evitar**: Assumir que o Anki está em determinado estado
✅ **Fazer**: Sempre validar estado antes de operar

### 4. Não Ignorar Edge Cases
❌ **Evitar**: Testar apenas caso feliz
✅ **Fazer**: Testar meia-noite, virada de dia, timezones, primeiro uso, etc.

### 5. Não Adicionar Features Sem Necessidade
❌ **Evitar**: "Seria legal se também fizesse X, Y, Z..."
✅ **Fazer**: Apenas o que é necessário para o core functionality

### 6. Não Usar Variáveis Globais Mutáveis
❌ **Evitar**: Estado global que pode ser modificado por múltiplos pontos
✅ **Fazer**: Estado encapsulado em classes ou passado explicitamente

### 7. Não Confiar em Timing Preciso
❌ **Evitar**: Assume que eventos ocorrem em ordem específica
✅ **Fazer**: Código defensivo que funciona independente de timing

---

## Seções a Preencher (Após Pesquisa e Planejamento)

> **IMPORTANTE**: As seções abaixo devem ser preenchidas APÓS:
> 1. Pesquisa de best practices (@best-practices-researcher)
> 2. Planejamento arquitetural (/compounding-engineering:plan)
> 3. Validação das decisões

### Decisões Técnicas
**Status**: 🔴 Pendente (preencher após pesquisa)

Documentar aqui:
- Abordagem de integração com Anki escolhida
- Alternativas consideradas e por que foram descartadas
- Método de filtro de cards (hooks/events/filters/outro)
- Estratégia de detecção de tipo de card
- Fontes/referências que informaram as decisões

### Arquitetura e Estrutura
**Status**: 🔴 Pendente (preencher após plano)

Documentar aqui:
- Estrutura de módulos/arquivos
- Fluxo de dados
- Pontos de integração com Anki
- Diagrama conceitual (se útil)

### Configuração do Usuário
**Status**: 🔴 Pendente (preencher após plano)

Documentar aqui:
- Formato de configuração
- Valores padrão
- Como persistir configurações
- Interface de configuração (se houver)

### Estratégia de Testes
**Status**: 🔴 Pendente (preencher após plano)

Documentar aqui:
- Como mockar Anki API
- Casos de teste críticos
- Abordagem para edge cases

---

## Recursos Úteis

### Documentação Anki
- [Anki Add-ons Documentation](https://addon-docs.ankiweb.net/)
- [Anki Manual](https://docs.ankiweb.net/)
- [PyQt5 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt5/)

### Comunidade
- [Anki Add-ons Forum](https://forums.ankiweb.net/c/add-ons/11)
- [r/Anki Subreddit](https://reddit.com/r/Anki)

---

**Última atualização**: 2025-01-11
**Versão**: 2.0 (planejamento inicial)
**Status**: 🟡 Aguardando pesquisa e planejamento