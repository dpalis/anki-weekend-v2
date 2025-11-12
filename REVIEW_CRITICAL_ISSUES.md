# 🔴 Issues Críticos - Anki Weekend Addon v2.0

**Status**: BLOQUEADORES - Devem ser corrigidos ANTES do release
**Data da Review**: 2025-11-12
**Total de Issues**: 3

---

## Issue #1: Perda Catastrófica de Dados

**Severidade**: 🔴 CRÍTICA
**Localização**: `__init__.py:91-92`
**Categoria**: Integridade de Dados
**Impacto**: Perda permanente de configurações do usuário

### Descrição do Problema

Se o addon for desinstalado durante o modo fim de semana, o usuário perde permanentemente suas configurações de deck sem possibilidade de recuperação.

### Cenário de Falha

```
Sábado 10:00:
  - Usuário tem 5 decks com limites: 20, 15, 30, 25, 10 cards/dia
  - Addon define todos os limites como 0
  - Armazena original_limits em config.json

Sábado 14:00:
  - Usuário acha que addon está bugado
  - Desinstala addon
  - config.json é DELETADO
  - original_limits = PERDIDO PARA SEMPRE

Segunda 08:00:
  - Limites ainda estão em 0
  - Usuário não tem registro do que eram os valores originais
  - Deve adivinhar/recriar meses de ajustes
```

### Código Problemático

```python
# Linhas 58-70: store_original_limit()
def store_original_limit(config_id: int, limit: int) -> None:
    config = get_config()
    if 'original_limits' not in config:
        config['original_limits'] = {}
    config['original_limits'][str(config_id)] = limit
    mw.addonManager.writeConfig(__name__, config)  # ← ÚNICO ponto de armazenamento
```

**Problemas**:
- ❌ Armazenamento em um único local (addon config)
- ❌ Addon config NÃO sincroniza via AnkiWeb
- ❌ Deletado quando addon é removido
- ❌ Sem backup
- ❌ Sem mecanismo de recuperação

### Solução Recomendada

Implementar armazenamento redundante usando collection config do Anki (que sincroniza via AnkiWeb e sobrevive à desinstalação do addon):

```python
import json

def store_original_limit(config_id: int, limit: int) -> None:
    """
    Armazena limite original com redundância.

    Estratégia:
    1. Armazenamento primário: collection config (sincroniza, persiste)
    2. Armazenamento secundário: addon config (performance, compatibilidade)
    """
    # Armazenamento secundário (addon config) - mantém existente
    config = get_config()
    if 'original_limits' not in config:
        config['original_limits'] = {}
    config['original_limits'][str(config_id)] = limit
    mw.addonManager.writeConfig(__name__, config)

    # NOVO: Armazenamento primário (collection config)
    # Sobrevive à desinstalação do addon e sincroniza entre dispositivos
    if mw.col:
        try:
            # Ler limites existentes
            limits_json = mw.col.get_config('weekend_addon_original_limits', '{}')
            limits = json.loads(limits_json)

            # Adicionar/atualizar
            limits[str(config_id)] = limit

            # Salvar de volta
            mw.col.set_config('weekend_addon_original_limits', json.dumps(limits))
        except Exception as e:
            print(f"[Anki Weekend Addon] AVISO: Falha ao salvar em collection config: {e}")
            # Continua - pelo menos temos o addon config


def get_original_limit(config_id: int) -> int | None:
    """
    Recupera limite original com fallback redundante.

    Ordem de prioridade:
    1. Collection config (mais confiável)
    2. Addon config (fallback)
    """
    # Tentar collection config primeiro
    if mw.col:
        try:
            limits_json = mw.col.get_config('weekend_addon_original_limits', '{}')
            limits = json.loads(limits_json)
            limit = limits.get(str(config_id))
            if limit is not None:
                return limit
        except Exception as e:
            print(f"[Anki Weekend Addon] AVISO: Falha ao ler collection config: {e}")

    # Fallback para addon config
    limits = get_config().get('original_limits', {})
    return limits.get(str(config_id))
```

### Função de Recuperação de Emergência

Adicionar função que usuários podem executar no console de debug do Anki:

```python
def emergency_restore_all_limits():
    """
    Função de emergência para restaurar todos os limites de deck.

    Como usar:
    1. Abrir Anki
    2. Tools → Add-ons → Weekend Addon → Config
    3. Copiar valores de original_limits
    4. Usar esse código no console de debug

    Ou simplesmente executar esta função se ainda estiver no código.
    """
    if not mw.col:
        print("ERRO: Coleção não carregada")
        return

    # Tentar collection config primeiro
    try:
        limits_json = mw.col.get_config('weekend_addon_original_limits', '{}')
        limits = json.loads(limits_json)
    except:
        # Fallback para addon config
        addon_config = mw.addonManager.getConfig(__name__)
        limits = addon_config.get('original_limits', {}) if addon_config else {}

    if not limits:
        print("ERRO: Nenhum limite original encontrado!")
        return

    # Restaurar todos
    restored = 0
    for config_id_str, original_limit in limits.items():
        try:
            config_id = int(config_id_str)
            config = mw.col.decks.get_config(config_id)
            if config:
                config['new']['perDay'] = original_limit
                mw.col.decks.save(config)
                restored += 1
                print(f"✓ Restaurado config {config_id}: {original_limit} cards/dia")
        except Exception as e:
            print(f"✗ Falha ao restaurar config {config_id_str}: {e}")

    print(f"\n✓ Total restaurado: {restored} configurações de deck")


# Registrar no menu do Anki para fácil acesso
from aqt.qt import QAction

def setup_emergency_menu():
    """Adiciona item de menu para recuperação de emergência."""
    action = QAction("🆘 Restaurar Limites Originais", mw)
    action.triggered.connect(emergency_restore_all_limits)
    mw.form.menuTools.addAction(action)

gui_hooks.main_window_did_init.append(setup_emergency_menu)
```

### Teste da Correção

```python
# Cenário de teste:
# 1. Instalar addon, configurar decks
# 2. Ativar modo fim de semana
# 3. Desinstalar addon
# 4. Reinstalar addon
# 5. Verificar se limites são recuperados do collection config

# Código de teste:
def test_redundant_storage():
    # Simular armazenamento
    store_original_limit(123, 20)

    # Verificar ambos os locais
    addon_config = mw.addonManager.getConfig(__name__)
    assert addon_config['original_limits']['123'] == 20

    col_limits = json.loads(mw.col.get_config('weekend_addon_original_limits', '{}'))
    assert col_limits['123'] == 20

    # Simular desinstalação (limpar addon config)
    mw.addonManager.writeConfig(__name__, {'travel_mode': False, 'original_limits': {}})

    # Verificar que ainda conseguimos recuperar
    recovered = get_original_limit(123)
    assert recovered == 20, "Falha: limite não recuperado do collection config!"

    print("✓ Teste de armazenamento redundante PASSOU")
```

### Estimativa de Esforço

- **Complexidade**: Média
- **Tempo estimado**: 1-2 horas
- **Arquivos afetados**: `__init__.py` (linhas 44-70)
- **Testes necessários**: Sim (cenário de desinstalação)

### Prioridade

**P0 (Máxima)**: Este é um bug destrutivo que pode causar perda permanente de dados do usuário. Deve ser corrigido antes de qualquer release público.

---

## Issue #2: Violação de Compatibilidade Python 3.9

**Severidade**: 🔴 CRÍTICA
**Localização**: `__init__.py:44`
**Categoria**: Compatibilidade
**Impacto**: Addon não funciona em Python 3.9 (versão mínima suportada pelo Anki)

### Descrição do Problema

A sintaxe `int | None` para type hints foi introduzida no Python 3.10 (PEP 604), mas CLAUDE.md especifica Python 3.9+ como versão mínima suportada.

### Código Problemático

```python
# Linha 44
def get_original_limit(config_id: int) -> int | None:
    """..."""
    limits = get_config().get('original_limits', {})
    return limits.get(str(config_id))
```

### Erro Gerado em Python 3.9

```
TypeError: unsupported operand type(s) for |: 'type' and 'type'
```

Usuários com Anki em Python 3.9 não conseguirão nem importar o addon.

### Solução 1: Future Annotations (Recomendada)

Adicionar no **início do arquivo** (linha 1 ou 2):

```python
"""
Anki Weekend Addon v2.0
...
"""

from __future__ import annotations  # ← ADICIONAR ESTA LINHA

from aqt import mw, gui_hooks
from datetime import datetime
```

**Por que funciona**: A importação `__future__.annotations` faz com que todas as anotações de tipo sejam tratadas como strings em tempo de execução, sendo avaliadas apenas por ferramentas de type checking (mypy, pyright), não pelo interpretador Python.

### Solução 2: Typing.Optional (Alternativa)

Se preferir compatibilidade explícita:

```python
from typing import Optional

def get_original_limit(config_id: int) -> Optional[int]:
    """..."""
    limits = get_config().get('original_limits', {})
    return limits.get(str(config_id))
```

**Desvantagem**: Mais verboso, sintaxe antiga.

### Comparação

| Abordagem | Compatibilidade | Modernidade | Verbosidade |
|-----------|----------------|-------------|-------------|
| `from __future__ import annotations` | ✅ Python 3.7+ | ✅ Sintaxe moderna | ✅ Conciso |
| `Optional[int]` | ✅ Python 3.5+ | ⚠️ Sintaxe antiga | ❌ Verboso |

### Implementação Completa

```python
"""
Anki Weekend Addon v2.0

Pauses new cards on weekends (Saturday & Sunday) while keeping reviews active.
Supports travel mode for extended pauses and cross-platform sync via AnkiWeb.

Author: Daniel Palis
License: MIT
Version: 2.0.0
"""

from __future__ import annotations  # ← CORREÇÃO: Compatibilidade Python 3.9

from aqt import mw, gui_hooks
from datetime import datetime


# ==========================================
# Weekend Detection
# ==========================================

def is_weekend() -> bool:
    """
    Check if today is Saturday or Sunday.

    Returns:
        bool: True if today is Saturday (5) or Sunday (6), False otherwise
    """
    return datetime.now().weekday() in [5, 6]


# Resto do código permanece inalterado...
```

### Teste da Correção

```bash
# Verificar versão do Python
python3 --version

# Testar import em Python 3.9
python3.9 -c "from __init__ import *; print('✓ Import bem-sucedido')"

# Se não tiver Python 3.9 instalado, testar sintaxe:
python3 -m py_compile __init__.py
```

### Estimativa de Esforço

- **Complexidade**: Trivial
- **Tempo estimado**: 2 minutos
- **Arquivos afetados**: `__init__.py` (adicionar 1 linha após docstring)
- **Testes necessários**: Sim (verificar import em Python 3.9)

### Prioridade

**P0 (Máxima)**: Sem esta correção, o addon não funciona em instalações Anki com Python 3.9, afetando uma parte significativa da base de usuários.

---

## Issue #3: Nenhuma Validação de Entrada

**Severidade**: 🔴 CRÍTICA
**Localização**: `__init__.py:54-55, 69`
**Categoria**: Segurança / Integridade de Dados
**Impacto**: Crashes do addon, corrupção de configurações de deck no Anki

### Descrição do Problema

O código lê limites armazenados em `config.json` sem validar tipo ou range. Se o arquivo for corrompido ou editado manualmente com valores inválidos, pode causar:

1. **Crash do addon** (TypeError ao restaurar limites)
2. **Corrupção da configuração de deck no Anki** (limites negativos, absurdamente altos)
3. **Comportamento indefinido** do scheduler do Anki

### Cenários de Falha

#### Cenário 1: Corrupção de Arquivo
```json
// config.json corrompido (erro de disco, crash durante escrita)
{
  "travel_mode": false,
  "original_limits": {
    "123": -5,           // Negativo
    "456": "vinte",      // String ao invés de int
    "789": 999999,       // Absurdamente alto
    "null": 20,          // Chave inválida
    "012.5": 15          // Float (config_id deve ser int)
  }
}
```

#### Cenário 2: Edição Manual Maliciosa/Equivocada
Usuário tenta "consertar" manualmente e introduz valores inválidos.

#### Cenário 3: Bug em Versão Futura
Uma versão futura do addon armazena dados em formato incompatível.

### Código Problemático

```python
# Linhas 44-55: get_original_limit() - SEM VALIDAÇÃO
def get_original_limit(config_id: int) -> int | None:
    limits = get_config().get('original_limits', {})
    return limits.get(str(config_id))  # ← Retorna QUALQUER COISA que estiver armazenada


# Linha 115: apply_weekday_mode() - USA SEM VALIDAR
original = get_original_limit(deck['conf'])
if original is not None:
    config['new']['perDay'] = original  # ← PERIGO: original pode ser string, negativo, etc.
    mw.col.decks.save(config)
```

### O Que Pode Acontecer

```python
# Se original_limits["123"] = "vinte"
config['new']['perDay'] = "vinte"
mw.col.decks.save(config)  # ← Anki salva, mas comportamento é indefinido

# Se original_limits["123"] = -10
config['new']['perDay'] = -10  # ← Anki pode travar ou mostrar -10 novos cards

# Se original_limits["123"] = 999999
config['new']['perDay'] = 999999  # ← Usuário recebe 999,999 novos cards na segunda!
```

### Solução: Validação Abrangente

```python
def validate_original_limit(limit: any) -> int | None:
    """
    Valida limite original armazenado.

    Regras de validação:
    - Deve ser inteiro
    - Deve estar no range 0-9999 (máximo do Anki)
    - None é aceitável (não armazenado)

    Args:
        limit: Valor a validar (pode ser qualquer tipo)

    Returns:
        int: Limite válido
        None: Valor inválido ou não armazenado
    """
    if limit is None:
        return None

    # Validação de tipo
    if not isinstance(limit, (int, float)):
        print(f"[Anki Weekend Addon] ERRO: Tipo de limite inválido: {type(limit).__name__} (valor: {limit})")
        return None

    # Converter para int se for float
    limit = int(limit)

    # Validação de range
    if limit < 0:
        print(f"[Anki Weekend Addon] ERRO: Limite negativo detectado: {limit}, usando 0")
        return 0

    if limit > 9999:
        print(f"[Anki Weekend Addon] AVISO: Limite muito alto detectado: {limit}, limitando a 9999")
        return 9999

    return limit


def get_original_limit(config_id: int) -> int | None:
    """
    Recupera limite original armazenado com validação.

    Args:
        config_id: ID da configuração de deck

    Returns:
        int: Limite válido (0-9999)
        None: Não armazenado ou valor inválido
    """
    # Validar config_id
    if not isinstance(config_id, int) or config_id < 0:
        print(f"[Anki Weekend Addon] ERRO: config_id inválido: {config_id}")
        return None

    limits = get_config().get('original_limits', {})
    raw_limit = limits.get(str(config_id))

    # Validar valor recuperado
    validated = validate_original_limit(raw_limit)

    if validated is None and raw_limit is not None:
        # Valor armazenado mas inválido - limpar da config
        print(f"[Anki Weekend Addon] Removendo limite inválido para config {config_id}")
        config = get_config()
        if str(config_id) in config.get('original_limits', {}):
            del config['original_limits'][str(config_id)]
            mw.addonManager.writeConfig(__name__, config)

    return validated


def store_original_limit(config_id: int, limit: int) -> None:
    """
    Armazena limite original com validação.

    Args:
        config_id: ID da configuração de deck (deve ser inteiro não-negativo)
        limit: Limite de novos cards por dia (deve ser 0-9999)

    Raises:
        ValueError: Se config_id ou limit forem inválidos
    """
    # Validar inputs
    if not isinstance(config_id, int) or config_id < 0:
        raise ValueError(f"config_id inválido: {config_id} (deve ser inteiro não-negativo)")

    # Validar limite
    validated_limit = validate_original_limit(limit)
    if validated_limit is None:
        raise ValueError(f"limit inválido: {limit} (deve ser inteiro 0-9999)")

    config = get_config()
    if 'original_limits' not in config:
        config['original_limits'] = {}

    config['original_limits'][str(config_id)] = validated_limit

    try:
        mw.addonManager.writeConfig(__name__, config)
    except Exception as e:
        print(f"[Anki Weekend Addon] ERRO ao escrever config: {e}")
        raise
```

### Validação de Schema de Config

Adicionar validação na leitura do config:

```python
def get_config() -> dict:
    """
    Lê configuração do addon com validação de schema.

    Returns:
        dict: Configuração válida com defaults seguros
    """
    try:
        raw_config = mw.addonManager.getConfig(__name__)

        if raw_config is None:
            print("[Anki Weekend Addon] Config não encontrado, usando defaults")
            return {'travel_mode': False, 'original_limits': {}}

        # Validar tipo
        if not isinstance(raw_config, dict):
            print(f"[Anki Weekend Addon] ERRO: Config não é dict: {type(raw_config)}, usando defaults")
            return {'travel_mode': False, 'original_limits': {}}

        # Validar travel_mode
        travel_mode = raw_config.get('travel_mode', False)
        if not isinstance(travel_mode, bool):
            print(f"[Anki Weekend Addon] AVISO: travel_mode inválido: {travel_mode}, usando False")
            travel_mode = False

        # Validar original_limits
        original_limits = raw_config.get('original_limits', {})
        if not isinstance(original_limits, dict):
            print(f"[Anki Weekend Addon] ERRO: original_limits não é dict, usando vazio")
            original_limits = {}

        # Validar cada entrada em original_limits
        cleaned_limits = {}
        for key, value in original_limits.items():
            if not isinstance(key, str):
                print(f"[Anki Weekend Addon] AVISO: Chave inválida ignorada: {key}")
                continue

            validated = validate_original_limit(value)
            if validated is not None:
                cleaned_limits[key] = validated
            else:
                print(f"[Anki Weekend Addon] AVISO: Valor inválido ignorado: {key}={value}")

        return {
            'travel_mode': travel_mode,
            'original_limits': cleaned_limits
        }

    except Exception as e:
        print(f"[Anki Weekend Addon] EXCEÇÃO ao ler config: {e}")
        return {'travel_mode': False, 'original_limits': {}}
```

### Teste da Correção

```python
def test_validation():
    """Testes unitários para validação."""

    # Teste 1: Valores válidos
    assert validate_original_limit(20) == 20
    assert validate_original_limit(0) == 0
    assert validate_original_limit(9999) == 9999
    assert validate_original_limit(None) is None

    # Teste 2: Valores inválidos - tipo
    assert validate_original_limit("vinte") is None
    assert validate_original_limit([20]) is None
    assert validate_original_limit({"limit": 20}) is None

    # Teste 3: Valores inválidos - range
    assert validate_original_limit(-10) == 0  # Clamped
    assert validate_original_limit(999999) == 9999  # Clamped

    # Teste 4: Float convertido para int
    assert validate_original_limit(20.7) == 20

    print("✓ Todos os testes de validação PASSARAM")


# Teste com config corrompido
def test_corrupted_config():
    """Simula config.json corrompido."""

    # Criar config corrompido
    corrupted = {
        'travel_mode': "yes",  # Deveria ser bool
        'original_limits': {
            '123': -5,
            '456': "vinte",
            '789': 999999
        }
    }

    mw.addonManager.writeConfig(__name__, corrupted)

    # Ler com validação
    config = get_config()

    # Verificar que foi sanitizado
    assert config['travel_mode'] == False
    assert config['original_limits']['123'] == 0  # Clamped
    assert '456' not in config['original_limits']  # Removido
    assert config['original_limits']['789'] == 9999  # Clamped

    print("✓ Teste de config corrompido PASSOU")
```

### Estimativa de Esforço

- **Complexidade**: Média-Alta
- **Tempo estimado**: 2-3 horas (incluindo testes)
- **Arquivos afetados**: `__init__.py` (linhas 34-70)
- **Testes necessários**: Sim (crítico - testar múltiplos cenários de corrupção)

### Prioridade

**P0 (Máxima)**: Validação de entrada é princípio básico de segurança. Sem isso, o addon pode corromper dados do usuário ou crashar o Anki.

---

## Resumo de Issues Críticos

| Issue | Localização | Esforço | Impacto se Não Corrigido |
|-------|-------------|---------|--------------------------|
| #1: Perda de Dados | `__init__.py:58-70` | 1-2h | Perda permanente de configurações |
| #2: Python 3.9 | `__init__.py:1` | 2min | Addon não funciona em Python 3.9 |
| #3: Validação | `__init__.py:34-70` | 2-3h | Crashes e corrupção de dados |

**Tempo Total Estimado**: 3-5 horas
**Bloqueador para Release**: SIM - Todos os 3 devem ser corrigidos
