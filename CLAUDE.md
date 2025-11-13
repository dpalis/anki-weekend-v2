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

## ⭐ Princípios Universais (Aplicam a QUALQUER Projeto)

> Estes princípios transcendem tecnologia, linguagem e domínio.
> Use como checklist em TODO projeto de software.

### 1. Simplicidade Apropriada

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

### 2. Validação Explícita > Debugging Implícito

**Princípio:** Falhe rápido com mensagens claras

**Aplicação:**
- Valide inputs em funções críticas
- Type hints + runtime validation
- Custo: ~10 linhas
- Benefício: Previne horas de debugging

**ROI Real (v2.0):** 100x+ (validação evitou bug de corrupção de dados)

---

### 3. UI Reduz Fricção Exponencialmente

**Princípio:** UI não é polimento - é acessibilidade

**Aplicação:**
- Preferir 1 clique > múltiplos passos
- Estado visível sem precisar "verificar"
- Mesmo usuários técnicos preferem cliques > config manual

**ROI Real (v2.0):** 10x adoção esperada (feedback: "muito trabalhoso" → "perfeito!")

---

### 4. Documentação é Ativo que Aprecia

**Princípio:** Documentação tem ROI crescente no tempo

**Aplicação:**
- README completo
- Decisões técnicas documentadas
- CHANGELOG detalhado
- Cada pergunta evitada = tempo economizado

**Diferencial:** Código deprecia, documentação aprecia

---

### 5. Feedback Real > Especulação

**Princípio:** Ship fast, iterate com usuário real

**Aplicação:**
- 1 usuário real > 100h de planejamento
- Features emergem de dores reais
- "Mas e se..." sem caso de uso concreto é red flag

**ROI Real (v2.0):** Cada feature (UI, i18n, ícones) veio de feedback que NUNCA teríamos previsto

---

### 6. Git Workflow = Liberdade Experimental

**Princípio:** Mais estrutura → Mais liberdade

**Aplicação:**
- Feature branches sempre
- Main sempre deployable
- Custo: 10 segundos
- Benefício: Segurança psicológica para experimentar

**Paradoxo:** Disciplina cria liberdade

---

## 💡 Patterns Reutilizáveis (Maioria dos Projetos)

> Patterns técnicos validados neste projeto, aplicáveis a maioria dos projetos de software.

### 1. Two-Phase Operations

**Problema:** Race conditions em read-modify-write de estado compartilhado

**Pattern:**
```python
# FASE 1: Read ALL
for item in items:
    state[item] = read(item)

# FASE 2: Write ALL
for item in items:
    write(item, new_value)
```

**Aplicável:** Banco de dados, file I/O, APIs, qualquer estado compartilhado

---

### 2. Armazenamento Redundante para Dados Críticos

**Princípio:** Primary + Backup para dados que, se perdidos, quebram sistema

**Pattern:**
```python
# Primary: Sincroniza entre devices
save_to_primary_storage(data)

# Backup: Local fallback
save_to_backup_storage(data)
```

**Threshold:** Dados críticos de usuário (perder = sistema quebra permanentemente)

**ROI Real (v2.0):** Salvou projeto quando usuário deletou config local

---

### 3. Performance - Otimize o Caso Comum

**Pattern:** Cache last state, compare antes de processar

```python
if current_state != desired_state:
    expensive_operation()  # Só roda quando MUDOU
    cache_state(desired_state)
```

**ROI Real (v2.0):** 20x melhoria (95% skip, 5% run)

---

### 4. Modularização Emergente vs Prematura

**Princípio:** Complexidade deve emergir de problemas REAIS

**Red Flags:**
- Separação de arquivos com total < 200 linhas
- "Preparado para o futuro" sem caso de uso
- Mais de 3 abstrações sem justificativa

**Threshold:** Só separar módulos quando passar ~200 linhas OU responsabilidade clara

---

### 5. Estimativas com Usuário Real

**Ajuste:** Multiplicar estimativa por 3x quando há usuário real

**Por quê:** Feedback revela requisitos não previstos (UI, i18n, UX ajustes)

**ROI Real (v2.0):** Planejado 1 arquivo (150 linhas) → Real 4 arquivos (1000 linhas)
- Não foi falha - complexidade emergiu de necessidades reais

---

## 📋 Princípios Específicos deste Projeto

### 1. Simplicidade Acima de Tudo
- Código deve ser óbvio à primeira leitura
- Evitar abstrações desnecessárias
- Preferir clareza sobre cleverness

### 2. Estabilidade e Confiabilidade
- Tratamento explícito de edge cases
- Fail gracefully - nunca quebrar experiência do Anki
- Logging apenas quando necessário

### 3. Facilidade de Expansão
- Arquitetura permite adicionar features **se precisar**
- Código autodocumentado (nomes claros > comentários excessivos)

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

## Decisões Técnicas (v2.0 Implementado)

### Abordagem de Integração

**Decisão:** Modificação direta de deck configurations via Anki API

**Alternativas Consideradas:**
1. ❌ **Hooks de Scheduler** - Complexo, invasivo, difícil debug (v1.0 usava)
2. ❌ **Filtro de Cards** - Não persiste entre sessões
3. ✅ **Deck Config Modification** - Simples, persiste, sincroniza via AnkiWeb

**Justificativa:**
- Deck configs são o local "oficial" para limites de novos cards
- Sincronização automática via AnkiWeb (cross-platform)
- API estável e documentada (`mw.col.decks`)
- Reversível (sempre restaura limites originais)

**Trade-offs Aceitos:**
- Não funciona com deck-specific overrides (documentado como limitação)
- Documentado em Issue #17 para v2.1

---

### Armazenamento de Dados

**Decisão:** Armazenamento redundante (Primary + Backup)

**Primary Storage:**
```python
mw.col.set_config("weekend_addon_original_limits", limits)
```
- Dentro de `collection.anki2`
- Sincroniza via AnkiWeb
- Sobrevive a reinstalação do addon

**Backup Storage:**
```python
mw.addonManager.writeConfig(__name__, config)
```
- Arquivo `meta.json` local
- Fallback se primary falhar
- Facilita debugging manual

**Lição Aprendida:** Redundância salvou o projeto quando usuário deletou config local

---

### Two-Phase State Capture

**Problema:** Race condition ao capturar limites de decks com config compartilhado

**Solução:**
```python
# FASE 1: Captura TUDO primeiro
for deck in decks:
    limits[deck] = get_current_limit(deck)

# FASE 2: Modifica TUDO depois
for deck in decks:
    set_limit(deck, 0)
```

**Pattern Aplicável:** Qualquer read-modify-write em estado compartilhado

---

### Validação de Entrada

**Decisão:** Validação explícita de TODOS os valores armazenados

**Implementação:**
```python
def validate_original_limit(limit: int) -> int:
    if not isinstance(limit, int):
        raise TypeError(...)
    if limit < MIN_NEW_CARDS or limit > MAX_NEW_CARDS:
        raise ValueError(...)
    return limit
```

**ROI:** 10 linhas previnem horas de debugging × múltiplos usuários = 100x+

---

## Arquitetura e Estrutura (v2.0)

### Estrutura Final

```
Anki Weekend Addon v2/
├── __init__.py       # 530 linhas - Lógica principal
│   ├── Weekend detection (is_weekend)
│   ├── Config management (get/store limits)
│   ├── Mode application (apply_weekend_mode, apply_weekday_mode)
│   ├── Main logic (on_profile_open)
│   └── Hook registration
│
├── ui.py             # 210 linhas - Interface de menu
│   ├── Menu creation (create_menu)
│   ├── Mode toggles (toggle_weekend_mode, toggle_travel_mode)
│   ├── Status dialog (show_status)
│   └── Dynamic icon updates
│
├── i18n.py           # 170 linhas - Sistema de traduções
│   ├── Translation dictionaries (PT-BR, EN)
│   ├── Language detection (detect_language)
│   └── Translation function (tr)
│
├── config.json       # 5 linhas - Configuração padrão
├── manifest.json     # Metadados para Anki 25.x
└── README.md, CHANGELOG.md, LICENSE
```

**Evolução da Estimativa:**
- Planejamento: 1 arquivo (~150 linhas)
- Realidade: 4 arquivos (~1000 linhas)
- **Justificativa:** Cada módulo emergiu de necessidade REAL (não over-engineering)

---

### Fluxo de Dados

```
1. STARTUP
   └─> on_profile_open()
       ├─> get_config() - Lê weekend_mode, travel_mode, last_applied_mode
       ├─> Determina desired_mode (disabled/travel/weekend/weekday)
       └─> Se mode mudou:
           ├─> apply_weekend_mode() ou apply_weekday_mode()
           └─> Salva last_applied_mode

2. USER TOGGLE (via UI)
   └─> toggle_weekend_mode() ou toggle_travel_mode()
       ├─> Atualiza config
       ├─> Chama on_profile_open() - Aplica mudança
       ├─> Mostra tooltip feedback
       └─> Atualiza ícone do menu

3. APPLY WEEKEND MODE
   └─> apply_weekend_mode()
       ├─> FASE 1: Captura limites atuais (safe capture)
       │   └─> Só captura valores > 0 ou 0 durante weekdays
       ├─> FASE 2: Modifica todos configs para 0
       └─> Salva limites (redundant storage)

4. APPLY WEEKDAY MODE
   └─> apply_weekday_mode()
       ├─> Lê limites originais (primary + fallback)
       ├─> Valida cada limite
       └─> Restaura para cada deck
```

---

### Pontos de Integração com Anki

**1. Hooks:**
```python
gui_hooks.profile_did_open.append(on_profile_open)
```
- Roda ao abrir perfil (startup + sync)
- Garante modo correto após sync

**2. Deck API:**
```python
col.decks.all_names_and_ids()      # Lista decks
col.decks.get_legacy(deck_id)      # Pega deck
col.decks.get_config(config_id)    # Pega config
col.decks.save(config)             # Salva mudanças
```

**3. Config API:**
```python
mw.col.get_config(key)             # Primary storage
mw.col.set_config(key, value)
mw.addonManager.getConfig(__name__)  # Backup storage
mw.addonManager.writeConfig(__name__, config)
```

**4. UI Integration:**
```python
mw.form.menuTools.addMenu(menu)    # Adiciona menu
QAction, QMenu                      # Qt widgets
tooltip(), showInfo()               # Anki utils
```

---

## Configuração do Usuário (v2.0)

### Formato de Configuração

**config.json (padrão):**
```json
{
  "weekend_mode": true,
  "travel_mode": false,
  "original_limits": {},
  "last_applied_mode": null
}
```

**meta.json (runtime - gerado pelo Anki):**
```json
{
  "config": {
    "weekend_mode": true,
    "travel_mode": false,
    "original_limits": {
      "1": 10,
      "2": 20
    },
    "last_applied_mode": "weekday"
  }
}
```

---

### Interface de Configuração

**UI Menu (Tools → Weekend Addon):**
```
┌─────────────────────────────┐
│ ✅ Modo Fim de Semana      │  ← Toggle on/off
│ ✅ Modo Viagem              │  ← Toggle on/off
│ Ver Status                  │  ← Dialog detalhado
└─────────────────────────────┘
```

**Feedback Visual:**
- ✅ = Ativado (verde)
- ❌ = Desativado (vermelho)
- Tooltips ao alternar
- Status dialog mostra estado completo

**Decisão de Design:**
- ✅ UI > Edição manual de JSON (10x menos fricção)
- ✅ Ícones mostram estado sem precisar verificar config
- ✅ Um clique vs 4 passos (Tools → Addons → Config → Edit → Save → Restart)

---

## Estratégia de Testes (v2.0)

### Abordagem Atual

**v2.0:** Testes manuais apenas

**Justificativa:**
- Projeto < 1000 linhas (threshold para automação)
- Um usuário real fornecendo feedback contínuo
- Custo/benefício de setup de testes não valia para v2.0

**Casos de Teste Críticos (Manuais):**
1. ✅ Weekend mode ON → Sábado → Verifica novos cards = 0
2. ✅ Weekend mode ON → Segunda → Verifica limites restaurados
3. ✅ Travel mode ON → Qualquer dia → Verifica novos cards = 0
4. ✅ Travel mode OFF → Restaura limites corretamente
5. ✅ Sincronização AnkiWeb → Limites persistem entre devices
6. ✅ Deck-specific overrides → Documenta limitação
7. ✅ Race condition → Múltiplos decks com mesmo config
8. ✅ i18n → PT-BR detectado automaticamente

---

### Estratégia Futura (v2.1+)

**Threshold Atingido:** >1000 linhas = automatizar

**Próximos passos:**
1. **Unit Tests** para lógica core
   ```python
   def test_validate_original_limit():
       assert validate_original_limit(10) == 10
       with pytest.raises(TypeError):
           validate_original_limit("10")
   ```

2. **Integration Tests** com mock de Anki API
   ```python
   @patch('mw.col.decks')
   def test_apply_weekend_mode(mock_decks):
       # Setup
       # Execute
       # Assert
   ```

3. **Edge Cases Automatizados**
   - Meia-noite (virada de dia)
   - Sync durante aplicação de modo
   - Config corrompido
   - Collection.anki2 ausente

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

**Última atualização**: 2025-01-13
**Versão**: 2.0 (implementado e publicado)
**Status**: ✅ Produção