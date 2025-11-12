# 🟡 Issues de Média Prioridade - Anki Weekend Addon v2.0

**Status**: Melhorias recomendadas para performance e qualidade
**Data da Review**: 2025-11-12
**Total de Issues**: 5

---

## Issue #8: Iteração O(n) Incondicional em Todo Startup

**Severidade**: 🟡 MÉDIA
**Localização**: `__init__.py:123-147`
**Categoria**: Performance / Otimização
**Impacto**: Atraso perceptível no startup para usuários com muitos decks

### Descrição do Problema

A cada abertura de perfil (startup do Anki + sync + troca de perfil), o addon itera através de TODOS os decks mesmo quando o modo não mudou. Isso é desnecessário e causa atrasos perceptíveis para power users.

### Análise de Performance

| Quantidade de Decks | Operações (pior caso) | Tempo Estimado | Experiência do Usuário |
|---------------------|----------------------|----------------|------------------------|
| 10 | 20-30 operações | 50-100ms | Imperceptível |
| 100 | 200-300 operações | 500ms-2s | **Atraso perceptível** |
| 1000 | 2000-3000 operações | 5-20s | **Inaceitável** |

### Comportamento Atual

```python
# Linha 154: Hook registrado
gui_hooks.profile_did_open.append(on_profile_open)

# Este hook dispara em:
# 1. Startup do Anki (ok, necessário)
# 2. Sync completa (ok se dia mudou, MAS...)
# 3. Sync durante o mesmo dia (DESNECESSÁRIO!)
# 4. Troca de perfil (ok, necessário)
# 5. Múltiplos syncs por dia (DESNECESSÁRIO!)
```

**Exemplo de Uso Real**:
```
Usuário típico abre Anki 10 vezes por dia:
- 100 decks × 10 aberturas = 1000 iterações de deck/dia
- 95% dessas iterações são DESNECESSÁRIAS (modo não mudou)
```

### Código Problemático

```python
def on_profile_open() -> None:
    if not mw.col:
        return

    config = get_config()

    if config.get('travel_mode', False):
        apply_weekend_mode()  # ← Sempre executa se travel_mode ativo
    elif is_weekend():
        apply_weekend_mode()  # ← Sempre executa em fim de semana
    else:
        apply_weekday_mode()  # ← Sempre executa em dia de semana

# Resultado: Itera todos os decks TODA VEZ mesmo que já tenha sido aplicado
```

### Solução: State Tracking

Adicionar rastreamento do último modo aplicado para evitar trabalho redundante:

```python
def on_profile_open() -> None:
    """
    Executa quando perfil abre (startup + sync).
    Aplica modo apropriado baseado em flag de travel mode ou dia atual.

    Otimização: Rastreia último modo aplicado para evitar iteração
    desnecessária de decks quando modo não mudou.
    """
    if not mw.col:
        return

    config = get_config()

    # Determinar modo desejado
    if config.get('travel_mode', False):
        desired_mode = 'travel'
    elif is_weekend():
        desired_mode = 'weekend'
    else:
        desired_mode = 'weekday'

    # Verificar modo atual
    current_mode = config.get('last_applied_mode')

    # OTIMIZAÇÃO: Aplicar APENAS se modo mudou
    if current_mode != desired_mode:
        # Modo mudou - aplicar atualização
        if desired_mode in ['weekend', 'travel']:
            apply_weekend_mode()
        else:
            apply_weekday_mode()

        # Armazenar modo aplicado
        config['last_applied_mode'] = desired_mode
        mw.addonManager.writeConfig(__name__, config)
    # Else: Modo não mudou - SKIP (economiza 95% das iterações!)
```

### Schema de Config Atualizado

```json
{
  "travel_mode": false,
  "original_limits": {},
  "last_applied_mode": "weekday"
}
```

**Valores possíveis para `last_applied_mode`**:
- `"weekend"`: Limites estão pausados (fim de semana)
- `"weekday"`: Limites estão restaurados (dia de semana)
- `"travel"`: Limites estão pausados (travel mode)
- `null` ou ausente: Primeira execução, modo não aplicado ainda

### Ganho de Performance

**Antes** (sem state tracking):
```
Segunda 08:00: on_profile_open() → Itera 100 decks
Segunda 10:00: Sync → on_profile_open() → Itera 100 decks (DESNECESSÁRIO)
Segunda 14:00: Sync → on_profile_open() → Itera 100 decks (DESNECESSÁRIO)
Segunda 18:00: Sync → on_profile_open() → Itera 100 decks (DESNECESSÁRIO)

Total: 400 iterações de deck em um único dia
```

**Depois** (com state tracking):
```
Segunda 08:00: on_profile_open() → Modo mudou (weekend→weekday) → Itera 100 decks ✓
Segunda 10:00: Sync → on_profile_open() → Modo não mudou → SKIP ✓
Segunda 14:00: Sync → on_profile_open() → Modo não mudou → SKIP ✓
Segunda 18:00: Sync → on_profile_open() → Modo não mudou → SKIP ✓

Total: 100 iterações de deck (75% de redução!)
```

**Impacto Real**:
- Usuário com 100 decks: 2s → 0.5s na primeira abertura, <10ms nas subsequentes
- Usuário com 1000 decks: 20s → 5s na primeira abertura, <50ms nas subsequentes

### Edge Cases

#### Edge Case 1: Múltiplas Máquinas

```
Desktop A:
  Sábado 10:00: Apply weekend mode
  last_applied_mode = "weekend"
  Sincroniza (mas last_applied_mode NÃO sincroniza - addon config)

Desktop B:
  Sábado 14:00: Sincroniza
  Recebe: limites em 0
  last_applied_mode = null (não tem config ainda)
  Detecta: weekend mode, mas limites já estão em 0
  Ação: Redundante mas SEGURA (re-aplica weekend mode)
```

**Conclusão**: Seguro. Pior caso é uma iteração redundante, não incorreção.

#### Edge Case 2: Travel Mode Toggle

```
Usuário liga travel mode:
  Antes: last_applied_mode = "weekday"
  Ação: desired_mode = "travel" ≠ "weekday"
  Aplica: apply_weekend_mode()
  Atualiza: last_applied_mode = "travel" ✓

Usuário desliga travel mode (em dia de semana):
  Antes: last_applied_mode = "travel"
  Ação: desired_mode = "weekday" ≠ "travel"
  Aplica: apply_weekday_mode()
  Atualiza: last_applied_mode = "weekday" ✓

Usuário desliga travel mode (em fim de semana):
  Antes: last_applied_mode = "travel"
  Ação: desired_mode = "weekend" ≠ "travel"
  Aplica: apply_weekend_mode()
  Atualiza: last_applied_mode = "weekend" ✓
```

**Conclusão**: Funciona corretamente para todos os casos.

### Teste da Otimização

```python
import time

def test_state_tracking_performance():
    """Medir ganho de performance com state tracking."""

    # Configurar 100 decks de teste
    # ... setup ...

    # Teste 1: Primeira execução (modo muda)
    start = time.time()
    on_profile_open()
    first_run = time.time() - start
    print(f"Primeira execução (modo muda): {first_run:.3f}s")

    # Teste 2: Segunda execução (modo NÃO muda)
    start = time.time()
    on_profile_open()
    second_run = time.time() - start
    print(f"Segunda execução (modo igual): {second_run:.3f}s")

    # Verificar ganho
    improvement = (1 - second_run / first_run) * 100
    print(f"Melhoria: {improvement:.1f}%")

    assert second_run < 0.1, "Segunda execução deve ser < 100ms (quase instantânea)"
    assert improvement > 90, "Deve ter pelo menos 90% de melhoria"
```

### Estimativa de Esforço

- **Complexidade**: Baixa
- **Tempo estimado**: 30-45 minutos
- **Arquivos afetados**: `__init__.py` (linhas 123-147), `config.json` (adicionar key)
- **Testes necessários**: Sim (verificar transições de modo)

### Prioridade

**P2 (Média)**: Não afeta correção funcional, mas melhora significativamente UX para power users. Altamente recomendado.

---

## Issue #9: Escritas de Config Dentro do Loop

**Severidade**: 🟡 MÉDIA
**Localização**: `__init__.py:92` (dentro do loop de decks)
**Categoria**: Performance / I/O
**Impacto**: Múltiplas escritas de disco causam lentidão

### Descrição do Problema

`store_original_limit()` é chamado dentro do loop e escreve o config no disco a cada chamada. Para usuários instalando o addon pela primeira vez com muitos decks, isso resulta em N escritas sequenciais de arquivo.

### Análise de I/O

**Operações de I/O por escrita de config**:
1. Serializar dict Python → JSON string
2. Escrever arquivo no disco
3. Sync do filesystem (fsync)

**Tempo típico por escrita**: 5-20ms (SSD), 10-50ms (HDD)

### Impacto de Performance

| Novos Decks | Escritas de Config | Tempo Total (SSD) | Tempo Total (HDD) |
|-------------|-------------------|-------------------|-------------------|
| 10 | 10 | 50-200ms | 100-500ms |
| 100 | 100 | 500ms-2s | 1-5s |
| 1000 | 1000 | 5-20s | 10-50s |

**Experiência do usuário**: Anki parece "travado" durante primeira instalação com muitos decks.

### Código Problemático

```python
# Linhas 86-96: apply_weekend_mode()
for deck_id in mw.col.decks.all_names_and_ids():
    deck = mw.col.decks.get_legacy(deck_id.id)
    config = mw.col.decks.get_config(deck['conf'])

    # Armazenar original se não já armazenado
    if get_original_limit(deck['conf']) is None:
        store_original_limit(deck['conf'], config['new']['perDay'])
        # ↑ PROBLEMA: Chama writeConfig() DENTRO do loop

    config['new']['perDay'] = 0
    mw.col.decks.save(config)
```

```python
# Linhas 58-70: store_original_limit()
def store_original_limit(config_id: int, limit: int) -> None:
    config = get_config()
    if 'original_limits' not in config:
        config['original_limits'] = {}
    config['original_limits'][str(config_id)] = limit
    mw.addonManager.writeConfig(__name__, config)  # ← ESCRITA DE DISCO
```

### Solução: Batch Writes

Acumular todas as mudanças em memória e escrever uma única vez no final:

```python
def apply_weekend_mode() -> None:
    """
    Define novos cards por dia = 0 para todos os decks.
    Armazena limites originais antes da modificação para restauração futura.

    Otimização: Batcheia todas as atualizações de config em memória
    e escreve uma única vez ao final (100x mais rápido).
    """
    col = mw.col
    if not col:
        return

    # Ler config UMA VEZ
    config = get_config()
    original_limits = config.setdefault('original_limits', {})
    limits_modified = False

    for deck_id in col.decks.all_names_and_ids():
        deck = col.decks.get_legacy(deck_id.id)
        deck_config = col.decks.get_config(deck['conf'])
        config_id_str = str(deck['conf'])

        # Armazenar em MEMÓRIA (não disco ainda)
        if config_id_str not in original_limits:
            current_limit = deck_config['new']['perDay']
            if current_limit > 0 or not is_weekend():
                original_limits[config_id_str] = current_limit
                limits_modified = True

        # Modificar deck config
        deck_config['new']['perDay'] = 0
        col.decks.save(deck_config)

    # ESCRITA ÚNICA no final (se houve modificações)
    if limits_modified:
        config['original_limits'] = original_limits
        mw.addonManager.writeConfig(__name__, config)
```

### Ganho de Performance

**Antes**:
```
100 novos decks:
  - 100 get_config() calls (leituras do disco/cache)
  - 100 writeConfig() calls (escritas do disco)
  - Tempo: 500ms-2s (SSD), 1-5s (HDD)
```

**Depois**:
```
100 novos decks:
  - 1 get_config() call (leitura)
  - 1 writeConfig() call (escrita)
  - Tempo: 5-20ms (SSD), 10-50ms (HDD)
```

**Melhoria**: 100x mais rápido para primeira instalação com muitos decks!

### Refatorar Também `apply_weekday_mode()`

Embora `apply_weekday_mode()` não escreva config (apenas lê), ainda se beneficia de ler uma vez:

```python
def apply_weekday_mode() -> None:
    """
    Restaura limites originais de novos cards por dia para todos os decks.

    Otimização: Lê config uma única vez ao invés de múltiplas chamadas.
    """
    col = mw.col
    if not col:
        return

    # Ler config UMA VEZ
    original_limits = get_config().get('original_limits', {})

    for deck_id in col.decks.all_names_and_ids():
        deck = col.decks.get_legacy(deck_id.id)
        deck_config = col.decks.get_config(deck['conf'])

        # Buscar em dict em memória (não chamar get_original_limit())
        original = original_limits.get(str(deck['conf']))
        if original is not None:
            deck_config['new']['perDay'] = original
            col.decks.save(deck_config)
```

### Implicações

**Funções Afetadas**:
- `get_original_limit()` - pode ser removida ou simplificada
- `store_original_limit()` - deve ser removida (inline no apply_weekend_mode)

**Trade-off**: Perde abstração, mas ganha performance significativa. Dado que o código já é simples (154 linhas), essa perda é aceitável.

### Estimativa de Esforço

- **Complexidade**: Baixa-Média
- **Tempo estimado**: 45-60 minutos
- **Arquivos afetados**: `__init__.py` (refatorar linhas 44-96)
- **Testes necessários**: Sim (verificar múltiplos decks)

### Prioridade

**P2 (Média)**: Afeta principalmente primeira instalação. Usuários existentes não notam tanto. Mas combinado com Issue #8, melhoria é dramática.

---

## Issue #10: Duplicação de Código (70%)

**Severidade**: 🟡 MÉDIA
**Localização**: `__init__.py:77-97 vs 99-117`
**Categoria**: Manutenibilidade / DRY
**Impacto**: Se lógica de iteração mudar, deve atualizar 2 lugares

### Descrição do Problema

`apply_weekend_mode()` e `apply_weekday_mode()` compartilham estrutura quase idêntica, violando o princípio DRY (Don't Repeat Yourself).

### Código Duplicado

```python
# apply_weekend_mode() - Linhas 83-96
if not mw.col:
    return

for deck_id in mw.col.decks.all_names_and_ids():
    deck = mw.col.decks.get_legacy(deck_id.id)
    config = mw.col.decks.get_config(deck['conf'])
    # ... lógica específica de weekend ...
    mw.col.decks.save(config)


# apply_weekday_mode() - Linhas 105-116
if not mw.col:
    return

for deck_id in mw.col.decks.all_names_and_ids():
    deck = mw.col.decks.get_legacy(deck_id.id)
    config = mw.col.decks.get_config(deck['conf'])
    # ... lógica específica de weekday ...
    mw.col.decks.save(config)
```

**Duplicação**: ~15 linhas de 20 (75%)

### Solução: Extrair Lógica Comum

#### Opção 1: Helper Function com Callback

```python
def _apply_to_all_deck_configs(modification_fn):
    """
    Aplica função de modificação a todas as configurações de deck.

    Args:
        modification_fn: Função(config_id: int, deck_config: dict) -> None
    """
    col = mw.col
    if not col:
        return

    for deck_id in col.decks.all_names_and_ids():
        try:
            deck = col.decks.get_legacy(deck_id.id)
            if not deck or 'conf' not in deck:
                continue

            deck_config = col.decks.get_config(deck['conf'])
            if not deck_config:
                continue

            # Aplicar modificação customizada
            modification_fn(deck['conf'], deck_config)

            # Salvar
            col.decks.save(deck_config)

        except Exception as e:
            print(f"[Anki Weekend Addon] Erro ao processar deck {deck_id.id}: {e}")
            continue


def apply_weekend_mode() -> None:
    """Define limites como 0, armazena originais."""

    # Preparar dados para captura de originais
    config = get_config()
    original_limits = config.setdefault('original_limits', {})
    limits_modified = False

    def pause_deck(config_id, deck_config):
        nonlocal limits_modified

        # Armazenar original se necessário
        config_id_str = str(config_id)
        if config_id_str not in original_limits:
            current = deck_config['new']['perDay']
            if current > 0:
                original_limits[config_id_str] = current
                limits_modified = True

        # Pausar
        deck_config['new']['perDay'] = 0

    # Aplicar a todos os decks
    _apply_to_all_deck_configs(pause_deck)

    # Salvar config se modificado
    if limits_modified:
        mw.addonManager.writeConfig(__name__, config)


def apply_weekday_mode() -> None:
    """Restaura limites originais."""

    # Carregar limites armazenados
    original_limits = get_config().get('original_limits', {})

    def restore_deck(config_id, deck_config):
        # Restaurar se existe original
        original = original_limits.get(str(config_id))
        if original is not None:
            deck_config['new']['perDay'] = original

    # Aplicar a todos os decks
    _apply_to_all_deck_configs(restore_deck)
```

**Prós**:
- Elimina duplicação
- Lógica de iteração em um único lugar
- Fácil adicionar tratamento de erros centralizado

**Contras**:
- Adiciona abstração (callback, closure com nonlocal)
- Pode ser considerado over-engineering para código de 154 linhas

#### Opção 2: Generator Pattern

```python
def _iter_deck_configs():
    """
    Generator que itera configurações de deck de forma segura.

    Yields:
        (config_id, deck_config): Tupla de ID e configuração de deck
    """
    col = mw.col
    if not col:
        return

    for deck_id in col.decks.all_names_and_ids():
        try:
            deck = col.decks.get_legacy(deck_id.id)
            if not deck or 'conf' not in deck:
                continue

            deck_config = col.decks.get_config(deck['conf'])
            if not deck_config:
                continue

            yield (deck['conf'], deck_config, col)

        except Exception as e:
            print(f"[Anki Weekend Addon] Erro ao processar deck {deck_id.id}: {e}")
            continue


def apply_weekend_mode() -> None:
    config = get_config()
    original_limits = config.setdefault('original_limits', {})
    limits_modified = False

    for config_id, deck_config, col in _iter_deck_configs():
        config_id_str = str(config_id)

        # Armazenar original
        if config_id_str not in original_limits:
            current = deck_config['new']['perDay']
            if current > 0:
                original_limits[config_id_str] = current
                limits_modified = True

        # Pausar
        deck_config['new']['perDay'] = 0
        col.decks.save(deck_config)

    if limits_modified:
        mw.addonManager.writeConfig(__name__, config)


def apply_weekday_mode() -> None:
    original_limits = get_config().get('original_limits', {})

    for config_id, deck_config, col in _iter_deck_configs():
        original = original_limits.get(str(config_id))
        if original is not None:
            deck_config['new']['perDay'] = original
            col.decks.save(deck_config)
```

**Prós**:
- Pythonic (generators são idiomáticos)
- Mantém lógica de negócio legível
- Centraliza error handling

**Contras**:
- Ainda adiciona abstração

### Recomendação

**Dada a ênfase do projeto em simplicidade ("Princípio 0: Simplicidade Apropriada")**, considerar se a duplicação é realmente um problema:

**Argumentos CONTRA refatoração**:
- Código tem apenas 154 linhas - pequeno o suficiente para gerenciar duplicação
- As duas funções são conceitualmente diferentes (pausar vs restaurar)
- Duplicação torna cada função independente e óbvia
- Abstração adiciona cognitive load

**Argumentos A FAVOR refatoração**:
- Se error handling for adicionado (Issue #6), teria que ser duplicado
- Se lógica de iteração mudar (ex: iterar configs ao invés de decks), 2 lugares
- Princípio DRY é bom design

### Decisão

**Adiar para v2.1**. Focar em issues críticos primeiro. Se após correções o código crescer além de 200 linhas, reconsiderar.

### Estimativa de Esforço

- **Complexidade**: Baixa-Média
- **Tempo estimado**: 45-60 minutos
- **Arquivos afetados**: `__init__.py` (refatorar linhas 77-117)
- **Testes necessários**: Sim (regressão funcional)

### Prioridade

**P2 (Média-Baixa)**: Melhoria de código, não bug. Pode ser adiado.

---

## Issue #11: Números Mágicos

**Severidade**: 🟡 BAIXA-MÉDIA
**Localização**: `__init__.py:27`
**Categoria**: Legibilidade
**Impacto**: Reduz clareza para leitores não familiarizados com weekday() API

### Descrição do Problema

A função `is_weekend()` usa `[5, 6]` hardcoded sem constantes nomeadas. Embora seja padrão Python (`datetime.weekday()` retorna 0=Segunda...6=Domingo), não é imediatamente óbvio.

### Código Atual

```python
def is_weekend() -> bool:
    """
    Check if today is Saturday or Sunday.

    Returns:
        bool: True if today is Saturday (5) or Sunday (6), False otherwise
    """
    return datetime.now().weekday() in [5, 6]
```

**Problemas**:
- `5` e `6` não são autoexplicativos
- Requer conhecimento da API datetime
- Docstring explica, mas constantes seriam mais claras

### Solução: Named Constants

```python
# Após imports, antes de funções
# Constantes de dia da semana (datetime.weekday() retorna 0=Mon...6=Sun)
MONDAY = 0
TUESDAY = 1
WEDNESDAY = 2
THURSDAY = 3
FRIDAY = 4
SATURDAY = 5
SUNDAY = 6
WEEKEND_DAYS = [SATURDAY, SUNDAY]


def is_weekend() -> bool:
    """
    Verifica se hoje é sábado ou domingo.

    Returns:
        bool: True se hoje é fim de semana
    """
    return datetime.now().weekday() in WEEKEND_DAYS
```

**Alternativa mais concisa**:
```python
SATURDAY, SUNDAY = 5, 6
WEEKEND_DAYS = [SATURDAY, SUNDAY]
```

### Benefícios

1. **Legibilidade**: `WEEKEND_DAYS` é autoexplicativo
2. **Manutenibilidade**: Se definição de "weekend" mudar (ex: incluir sexta), um único lugar
3. **Documentação embutida**: Código se documenta

### Expansibilidade Futura

Se houver necessidade de lógica mais complexa:

```python
# Exemplo: Feriados customizados
CUSTOM_WEEKEND_DAYS = [SATURDAY, SUNDAY]  # Configurável

def is_weekend() -> bool:
    """Verifica se hoje é dia de descanso (fim de semana ou feriado customizado)."""
    config = get_config()
    weekend_days = config.get('custom_weekend_days', CUSTOM_WEEKEND_DAYS)
    return datetime.now().weekday() in weekend_days
```

### Estimativa de Esforço

- **Complexidade**: Trivial
- **Tempo estimado**: 5 minutos
- **Arquivos afetados**: `__init__.py` (adicionar constantes após linha 13)
- **Testes necessários**: Não (mudança cosmética)

### Prioridade

**P3 (Baixa-Média)**: Melhoria de legibilidade, não afeta funcionamento. Nice-to-have.

---

## Issue #12: Inconsistência de Type Hints

**Severidade**: 🟡 BAIXA
**Localização**: `__init__.py:34, 44, 58, 77, 99, 123`
**Categoria**: Consistência de Código
**Impacto**: Type checkers podem reclamar, mas código funciona

### Descrição do Problema

Type hints são usados de forma inconsistente:
- `get_config()` retorna `dict` (vago)
- `get_original_limit()` retorna `int | None` (preciso)
- Algumas funções não especificam estrutura de dicts

### Exemplos de Inconsistência

```python
# Linha 34: Vago
def get_config() -> dict:
    return mw.addonManager.getConfig(__name__) or {}

# Linha 44: Preciso
def get_original_limit(config_id: int) -> int | None:
    limits = get_config().get('original_limits', {})
    return limits.get(str(config_id))
```

### Problema

Type checkers (mypy, pyright) não conseguem inferir:
- Quais keys existem em `dict`
- Tipos dos values em `dict`
- Se acessos como `config['original_limits']` são seguros

### Solução: Type Hints Mais Específicos

#### Opção 1: dict[str, Any]

```python
from typing import Any

def get_config() -> dict[str, Any]:
    """
    Lê configuração do addon.

    Returns:
        dict[str, Any]: Configuração com keys:
            - 'travel_mode': bool
            - 'original_limits': dict[str, int]
    """
    return mw.addonManager.getConfig(__name__) or {}
```

#### Opção 2: TypedDict (mais robusto)

```python
from typing import TypedDict

class AddonConfig(TypedDict, total=False):
    """Schema de configuração do Weekend Addon."""
    travel_mode: bool
    original_limits: dict[str, int]
    last_applied_mode: str  # 'weekend' | 'weekday' | 'travel'


def get_config() -> AddonConfig:
    """
    Lê configuração do addon com schema validado.

    Returns:
        AddonConfig: Configuração tipada
    """
    config = mw.addonManager.getConfig(__name__)
    return config if config is not None else {'travel_mode': False, 'original_limits': {}}
```

**Prós de TypedDict**:
- Type checkers entendem estrutura
- Auto-complete em IDEs
- Erros detectados em tempo de desenvolvimento

**Contras**:
- Mais verboso
- Requer manutenção se schema mudar

### Recomendação

Para projeto simples de 154 linhas, **`dict[str, Any]` é suficiente**. TypedDict é overkill.

### Implementação

```python
from __future__ import annotations  # Issue #2
from typing import Any  # Para type hints

from aqt import mw, gui_hooks
from datetime import datetime


def get_config() -> dict[str, Any]:
    """..."""
    return mw.addonManager.getConfig(__name__) or {}


def get_original_limit(config_id: int) -> int | None:
    """..."""  # Já está correto
    limits = get_config().get('original_limits', {})
    return limits.get(str(config_id))
```

### Estimativa de Esforço

- **Complexidade**: Trivial
- **Tempo estimado**: 10 minutos
- **Arquivos afetados**: `__init__.py` (adicionar import, atualizar linha 34)
- **Testes necessários**: Não (type hints não afetam runtime)

### Prioridade

**P3 (Baixa)**: Melhoria de qualidade de código, não afeta funcionamento. Útil se usar type checkers.

---

## Resumo de Issues de Média Prioridade

| Issue | Localização | Esforço | Impacto | Quando Fazer |
|-------|-------------|---------|---------|--------------|
| #8: O(n) Iteração | `__init__.py:123-147` | 45min | Performance 95%↑ | Antes v2.1 |
| #9: Batch Writes | `__init__.py:92` | 60min | Performance 100x↑ | Antes v2.1 |
| #10: Duplicação | `__init__.py:77-117` | 60min | Manutenibilidade | v2.1+ |
| #11: Magic Numbers | `__init__.py:27` | 5min | Legibilidade | v2.1 |
| #12: Type Hints | `__init__.py:34` | 10min | Qualidade | v2.1 |

**Tempo Total Estimado**: 3 horas
**Recomendação**: Priorizar #8 e #9 (performance), adiar #10-#12 para v2.1
