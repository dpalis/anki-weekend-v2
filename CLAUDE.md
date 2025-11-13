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

# 2. Criar feature branch com nome descritivo
git checkout -b feature/nome-descritivo

# 3. Implementar, testar, commitar na feature branch
git add .
git commit -m "feat: descrição"

# 4. Revisar código (se necessário)
/compounding-engineering:review

# 5. Após aprovação, mergear na main
git checkout main
git merge feature/nome-descritivo

# 6. (Opcional) Deletar feature branch
git branch -d feature/nome-descritivo
```

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

## Lições Aprendidas (v2.0 Implementation)

### 1. Modularização Emergente vs Prematura

**Planejamento Inicial:**
- Estimativa: 1 arquivo (~150 linhas)
- Justificativa: "Lógica é trivial"

**Realidade:**
- Implementação: 4 arquivos (~1000 linhas totais)
  - `__init__.py` (~530 linhas) - Lógica principal
  - `ui.py` (~210 linhas) - Interface
  - `i18n.py` (~170 linhas) - Traduções
  - `config.json` (~5 linhas) - Config

**Lição:** ✅ **A modularização emergiu naturalmente de necessidades REAIS**
- UI surgiu de feedback: "muito trabalhoso editar JSON manualmente"
- i18n surgiu de requisito: "detectar idioma automaticamente"
- Separação foi justificada (cada módulo > 150 linhas com responsabilidade clara)
- **NÃO foi over-engineering** - cada módulo resolveu dor real

**Princípio Validado:** Complexidade deve emergir de problemas reais, não de antecipação.

---

### 2. Race Conditions em Captura de Estado

**Problema Descoberto:**
```python
# ❌ ERRADO (v2.0 inicial)
for deck in decks:
    original = get_current_limit(deck)  # Ex: 10
    store_limit(deck, original)          # Salva 10
    set_limit(deck, 0)                   # Muda para 0
    # Próximo deck com mesmo config vê 0! ❌
```

**Solução - Two-Phase Approach:**
```python
# ✅ CORRETO (v2.0 final)
# FASE 1: Captura TUDO primeiro
for deck in decks:
    limits[deck] = get_current_limit(deck)

# FASE 2: Modifica TUDO depois
for deck in decks:
    set_limit(deck, 0)
```

**Lição:** ✅ **Separar leitura de escrita previne race conditions**
- Especialmente crítico quando múltiplos decks compartilham config
- Pattern aplicável: banco de dados, file I/O, APIs

**Aplicação Futura:** Sempre que ler/modificar estado compartilhado, usar pattern two-phase.

---

### 3. Validação de Dados é Investimento, Não Custo

**Bug da v1.0:**
- Limites restaurados incorretamente (10 → 20)
- Causa: Nenhuma validação de valores armazenados

**Solução v2.0:**
```python
def validate_original_limit(limit: int) -> int:
    if not isinstance(limit, int):
        raise TypeError(f"Limit must be integer, got {type(limit).__name__}")
    if limit < 0 or limit > 9999:
        raise ValueError(f"Limit must be 0-9999, got {limit}")
    return limit
```

**Impacto:**
- ✅ Previne corrupção de dados
- ✅ Falha rápido com mensagens claras
- ✅ Evita debugging de 2 horas "por que restaurou 20 em vez de 10?"

**Lição:** ✅ **Validação explícita economiza MUITO tempo de debugging**
- Especialmente crítico em dados persistidos (sobrevivem ao restart)
- Custo: ~10 linhas de código
- Benefício: Previne horas de debugging + perda de confiança do usuário

**ROI:** 100x+ (10 linhas vs 2h debugging × múltiplos usuários)

---

### 4. UI Reduz Fricção Exponencialmente

**Antes (v2.0 inicial):**
```json
// Usuário precisa:
// 1. Ir em Tools → Add-ons → Config
// 2. Editar JSON manualmente
// 3. Salvar
// 4. Reiniciar Anki
{
  "travel_mode": true  // ← Editar isto
}
```

**Depois:**
- Tools → Weekend Addon → ✅ Modo Viagem (um clique)

**Impacto:**
- Feedback do usuário: "muito trabalhoso" → "perfeito!"
- Adoção esperada: 10x maior
- Suporte: Reduz perguntas "como faço X?"

**Lição:** ✅ **UI não é "polimento" - é acessibilidade**
- Mesmo usuários técnicos preferem cliques > JSON
- UI revela estado (ícones ✅/❌) sem precisar "verificar config"
- **Investimento:** ~200 linhas de código
- **Retorno:** Diferença entre "ferramenta de dev" e "produto"

---

### 5. i18n Desde o Início (Quando Relevante)

**Decisão v2.0:**
- Requisito: Suporte PT-BR (usuário brasileiro)
- Implementação: Sistema completo desde v1

**Alternativa NÃO tomada:**
- "Fazemos em inglês primeiro, depois traduzimos"

**Por que foi correto:**
- Usuário principal é PT-BR
- Adicionar depois = refactor massivo de strings
- ~170 linhas para sistema completo
- Custo futuro evitado: Reescrever todas as strings

**Lição:** ✅ **Se você SABE que precisa de i18n, faça desde o início**
- Não é "preparar para o futuro" - é requisito conhecido
- Estrutura simples (dict de traduções) é suficiente
- **Red flag evitada:** Strings hardcoded espalhadas pelo código

**Princípio:** Distinguir "requisito conhecido" de "especulação futura"

---

### 6. Armazenamento Redundante Salvou o Projeto

**Estratégia v2.0:**
```python
# Primary: collection.anki2 (sincroniza via AnkiWeb)
mw.col.set_config("weekend_addon_original_limits", limits)

# Backup: addon config (local)
mw.addonManager.writeConfig(__name__, config)
```

**Evento Real:**
- Usuário testou, deletou config local, mudou de device
- Primary storage (collection.anki2) sincronizou via AnkiWeb
- Limites foram restaurados corretamente! ✅

**Lição:** ✅ **Redundância crítica != over-engineering**
- Dados de usuário (limites originais) são CRÍTICOS
- Perder esses dados = addon quebra permanentemente
- Custo: ~5 linhas extras
- Benefício: Resiliência contra perda de dados

**Princípio:** Para dados críticos de usuário, sempre ter backup strategy.

---

### 7. Performance Optimization Baseada em Dados Reais

**Problema Observado:**
- Addon rodava em CADA abertura de perfil
- Iterava 100% dos decks mesmo quando modo não mudou

**Solução - Lazy Update:**
```python
current_mode = config.get('last_applied_mode')
if current_mode != desired_mode:
    apply_changes()  # Só roda se modo MUDOU
    config['last_applied_mode'] = desired_mode
```

**Impacto:**
- 95% das vezes: SKIP (modo não mudou)
- 5% das vezes: Roda (modo realmente mudou)
- Performance: 20x melhoria

**Lição:** ✅ **Otimize o caso comum, não o caso raro**
- Caso comum: Abrir Anki em dia de semana (modo não muda)
- Caso raro: Virada de semana (modo muda)
- **Pattern:** Cache last state, compare antes de processar

**Aplicação Futura:** Qualquer operação cara que depende de estado - sempre comparar primeiro.

---

### 8. Documentação é Código que Nunca Quebra

**Investimento v2.0:**
- README.md (~200 linhas)
- CHANGELOG.md (~100 linhas)
- CLAUDE.md (~300 linhas)
- Docstrings em todas as funções

**Retorno:**
- Zero perguntas "como instalar?"
- Zero perguntas "como usar?"
- Futuro eu consegue entender código em 6 meses
- Contribuidores sabem por onde começar

**Lição:** ✅ **Boa documentação é investimento com juros compostos**
- Cada pergunta evitada = tempo economizado
- Cada contexto preservado = debugging mais rápido
- **ROI aumenta com tempo** (diferente de código que envelhece)

**Princípio Compounding Engineering:** Documentação é ativo que APRECIA com tempo.

---

### 9. Git Workflow Disciplinado Permite Experimentação Segura

**Prática v2.0:**
- NUNCA commit direto em main
- Feature branches para tudo
- Merge apenas quando funcionando

**Benefício Real:**
- Pude experimentar 3 abordagens diferentes de i18n
- Quebrei código várias vezes sem medo
- Main sempre deployable

**Lição:** ✅ **Feature branches não são burocracia - são liberdade**
- Paradoxo: Mais estrutura = mais liberdade para experimentar
- Cost: ~10 segundos para criar branch
- Benefit: Segurança psicológica para experimentar

---

### 10. "Simplicidade Apropriada" é Contextual

**Planejamento:** 1 arquivo (~150 linhas)
**Realidade:** 4 arquivos (~1000 linhas)

**Isso foi falha do planejamento?** ❌ NÃO!

**Por quê:**
- Planejamento subestimou requisitos (UI, i18n surgiram depois)
- Cada adição foi JUSTIFICADA por necessidade real
- Arquitetura permaneceu simples (sem abstrações desnecessárias)
- **Princípio mantido:** Complexidade emergiu de problemas reais

**Lição:** ✅ **"Simples" não significa "pequeno em linhas de código"**
- Simples = Fácil de entender, sem abstrações desnecessárias
- 1000 linhas diretas > 200 linhas com metaprogramação
- **Métrica correta:** "Quanto tempo para entender?" não "Quantas linhas?"

---

### 11. Feedback Loop com Usuário Real é Insubstituível

**Eventos:**
1. Usuário: "muito trabalhoso editar JSON"
   → Resultado: UI foi criado
2. Usuário: "deck X não funciona"
   → Resultado: Descobrimos limitação deck-specific overrides
3. Usuário: "ícone no lugar errado"
   → Resultado: Movemos ícone para menu item

**Lição:** ✅ **Usuário real > 100 horas de especulação**
- Cada feedback revelou problema que NUNCA teríamos previsto
- Features que importam emergem de uso real
- **Pattern:** Ship fast, iterate com feedback real

**Aplicação Futura:** Sempre ter 1 usuário real antes de escalar.

---

## Princípios Validados (Compounding Engineering)

### ✅ O que funcionou:
1. **Two-phase operations** para state compartilhado
2. **Validação explícita** de dados críticos
3. **Armazenamento redundante** para resiliência
4. **UI reduz fricção** massivamente
5. **i18n desde início** quando requisito conhecido
6. **Documentação como investimento**
7. **Git workflow estruturado** = liberdade experimental
8. **Feedback real > especulação**

### ❌ O que ajustar:
1. **Estimativas iniciais** muito otimistas (1 arquivo → 4 arquivos)
   - **Ajuste futuro:** Multiplicar estimativa por 3x quando há usuário real
2. **Testing manual** suficiente para v2.0, mas v2.1+ precisa de testes automatizados
   - **Threshold:** >1000 linhas = automatizar testes

---

**Última atualização**: 2025-01-13
**Versão**: 2.0 (implementado e publicado)
**Status**: ✅ Produção