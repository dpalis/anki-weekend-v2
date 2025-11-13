# 🟢 Issues de Baixa Prioridade - Anki Weekend Addon v2.0

**Status**: Melhorias opcionais, não bloqueiam release
**Data da Review**: 2025-11-12
**Total de Issues**: 4

---

## Issue #13: Oportunidades de Simplificação

**Severidade**: 🟢 BAIXA
**Localização**: Arquivo inteiro
**Categoria**: Simplicidade de Código
**Impacto**: Redução de LOC, maior clareza

### Contexto

O agente **code-simplicity-reviewer** encontrou que o código pode ser reduzido de **154 linhas para ~75-80 linhas** (redução de 47%) removendo abstrações desnecessárias e documentação excessiva.

### Oportunidades Identificadas

#### 1. Funções Helper de Config (Desnecessárias)

**Atual** (23 linhas):
```python
def get_original_limit(config_id: int) -> int | None:
    limits = get_config().get('original_limits', {})
    return limits.get(str(config_id))


def store_original_limit(config_id: int, limit: int) -> None:
    config = get_config()
    if 'original_limits' not in config:
        config['original_limits'] = {}
    config['original_limits'][str(config_id)] = limit
    mw.addonManager.writeConfig(__name__, config)
```

**Simplificado** (inline, 0 linhas extras):
```python
# Em apply_weekend_mode():
config = get_config()
limits = config.setdefault('original_limits', {})

if str(deck['conf']) not in limits:
    limits[str(deck['conf'])] = deck_config['new']['perDay']

# No final:
mw.addonManager.writeConfig(__name__, config)
```

**Análise**:
- As funções helper adicionam indireção sem valor
- Operações de dict são triviais em Python
- Inline torna o fluxo de dados óbvio

#### 2. Docstrings Excessivas

**Atual** (6 linhas):
```python
def is_weekend() -> bool:
    """
    Check if today is Saturday or Sunday.

    Returns:
        bool: True if today is Saturday (5) or Sunday (6), False otherwise
    """
    return datetime.now().weekday() in [5, 6]
```

**Simplificado** (1 linha):
```python
def is_weekend() -> bool:
    return datetime.now().weekday() in [5, 6]  # Sat=5, Sun=6
```

**Análise**:
- Nome da função já explica o que faz
- Implementação é uma linha óbvia
- Docstring adiciona ruído, não clareza

#### 3. Cabeçalhos de Seção ASCII Art

**Atual** (15 linhas):
```python
# ==========================================
# Weekend Detection
# ==========================================

def is_weekend() -> bool:
    ...


# ==========================================
# Config Management
# ==========================================

def get_config() -> dict:
    ...
```

**Simplificado** (0 linhas):
```python
def is_weekend() -> bool:
    ...


def get_config() -> dict:
    ...
```

**Análise**:
- Nomes de funções já indicam propósito
- ASCII art é ruído visual
- Arquivo tem 154 linhas - facilmente escaneável sem seções

#### 4. Docstring de Módulo Verbosa

**Atual** (9 linhas):
```python
"""
Anki Weekend Addon v2.0

Pauses new cards on weekends (Saturday & Sunday) while keeping reviews active.
Supports travel mode for extended pauses and cross-platform sync via AnkiWeb.

Author: [Your Name]
License: MIT
Version: 2.0.0
"""
```

**Simplificado** (2 linhas):
```python
"""Anki Weekend Addon v2.0 - Pausa novos cards aos fins de semana"""
```

**Análise**:
- Metadados (author, license, version) devem estar em manifest/setup.py
- Descrição detalhada está no README
- Docstring deve ser concisa

### Versão Minimalista Completa (~75 linhas)

```python
"""Anki Weekend Addon v2.0 - Pausa novos cards aos finais de semana"""

from __future__ import annotations
from aqt import mw, gui_hooks
from datetime import datetime


SATURDAY, SUNDAY = 5, 6


def is_weekend() -> bool:
    return datetime.now().weekday() in [SATURDAY, SUNDAY]


def apply_weekend_mode() -> None:
    """Pausa novos cards (limit=0), armazena originais"""
    col = mw.col
    if not col:
        return

    config = mw.addonManager.getConfig(__name__) or {}
    limits = config.setdefault('original_limits', {})
    limits_modified = False

    for deck_id in col.decks.all_names_and_ids():
        try:
            deck = col.decks.get_legacy(deck_id.id)
            if not deck or 'conf' not in deck:
                continue

            deck_config = col.decks.get_config(deck['conf'])
            if not deck_config or 'new' not in deck_config:
                continue

            config_id = str(deck['conf'])

            # Armazenar original se não armazenado
            if config_id not in limits:
                current = deck_config['new']['perDay']
                if current > 0 or not is_weekend():
                    limits[config_id] = current
                    limits_modified = True

            # Pausar
            deck_config['new']['perDay'] = 0
            col.decks.save(deck_config)

        except Exception as e:
            print(f"[Weekend Addon] Erro ao processar deck {deck_id.id}: {e}")
            continue

    # Escrever config uma vez
    if limits_modified:
        mw.addonManager.writeConfig(__name__, config)


def apply_weekday_mode() -> None:
    """Restaura limites originais"""
    col = mw.col
    if not col:
        return

    limits = (mw.addonManager.getConfig(__name__) or {}).get('original_limits', {})

    for deck_id in col.decks.all_names_and_ids():
        try:
            deck = col.decks.get_legacy(deck_id.id)
            if not deck or 'conf' not in deck:
                continue

            deck_config = col.decks.get_config(deck['conf'])
            if not deck_config or 'new' not in deck_config:
                continue

            original = limits.get(str(deck['conf']))
            if original is not None:
                deck_config['new']['perDay'] = original
                col.decks.save(deck_config)

        except Exception as e:
            print(f"[Weekend Addon] Erro ao restaurar deck {deck_id.id}: {e}")
            continue


def on_profile_open() -> None:
    """Hook: aplica modo apropriado"""
    try:
        if not mw.col:
            return

        config = mw.addonManager.getConfig(__name__) or {}

        if config.get('travel_mode', False) or is_weekend():
            apply_weekend_mode()
        else:
            apply_weekday_mode()

    except Exception as e:
        print(f"[Weekend Addon] Erro crítico: {e}")


gui_hooks.profile_did_open.append(on_profile_open)
```

**Contagem**: ~80 linhas (inclui error handling do Issue #6)

### Trade-offs da Simplificação

**Prós**:
- ✅ Código mais conciso (47% menos linhas)
- ✅ Fluxo de dados óbvio (sem indireção)
- ✅ Mais alinhado com Princípio 0 (Simplicidade Apropriada)
- ✅ Mais fácil de escanear

**Contras**:
- ❌ Perde abstração (pode dificultar mudanças futuras)
- ❌ Funções mais longas (menos modular)
- ❌ Menos documentação (curva de aprendizado maior para novos contribuidores)

### Recomendação

**NÃO implementar agora**. Razões:

1. **Código atual já está escrito e funciona**
2. **Foco deve ser em correções críticas** (Issues #1-#7)
3. **Simplificação é uma reescrita**, não uma correção
4. **Risco de introduzir novos bugs** durante refatoração
5. **Princípio de estabilidade** do CLAUDE.md

**Quando considerar**:
- v2.1+ se código crescer além de 200 linhas
- Se manutenção se tornar difícil devido a abstrações
- Como exercício educacional de refatoração

### Estimativa de Esforço

- **Complexidade**: Média (reescrita completa)
- **Tempo estimado**: 3-4 horas (incluindo testes de regressão)
- **Arquivos afetados**: `__init__.py` (reescrita completa)
- **Testes necessários**: Sim (extensivos - garantir funcionalidade idêntica)

### Prioridade

**P4 (Muito Baixa)**: Opcional. Código atual é aceitável para projeto de 154 linhas.

---

## Issue #14: Placeholder de Autor

**Severidade**: 🟢 BAIXA (mas BLOQUEIA merge)
**Localização**: `__init__.py:7`
**Categoria**: Metadados
**Impacto**: Código de produção contém placeholder

### Descrição do Problema

Header do módulo contém placeholder não substituído:

```python
"""
Anki Weekend Addon v2.0

Pauses new cards on weekends (Saturday & Sunday) while keeping reviews active.
Supports travel mode for extended pauses and cross-platform sync via AnkiWeb.

Author: [Your Name]  # ← PLACEHOLDER
License: MIT
Version: 2.0.0
"""
```

### Solução

Substituir pelo nome real do autor:

```python
"""
Anki Weekend Addon v2.0

Pauses new cards on weekends (Saturday & Sunday) while keeping reviews active.
Supports travel mode for extended pauses and cross-platform sync via AnkiWeb.

Author: Daniel Palis
License: MIT
Version: 2.0.0
"""
```

### Estimativa de Esforço

- **Complexidade**: Trivial
- **Tempo estimado**: 10 segundos
- **Arquivos afetados**: `__init__.py` (linha 7)
- **Testes necessários**: Não

### Prioridade

**P1 (Alta) para merge**: Embora seja cosmético, código com placeholders não deve ir para produção.

---

## Issue #15: Falta .gitignore

**Severidade**: 🟢 BAIXA (mas BLOQUEIA merge)
**Localização**: Raiz do repositório
**Categoria**: Configuração do Repositório
**Impacto**: Risco de commitar arquivos temporários/cache

### Descrição do Problema

Repositório não tem `.gitignore`. Isso pode levar a commits acidentais de:
- Cache Python (`__pycache__/`, `*.pyc`)
- Arquivos de IDE (`.vscode/`, `.idea/`)
- Arquivos de sistema (`.DS_Store` no macOS)

### Solução

Criar `.gitignore` na raiz do repositório:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# macOS
.DS_Store
.AppleDouble
.LSOverride

# Windows
Thumbs.db
ehthumbs.db
Desktop.ini

# Testing
.pytest_cache/
.coverage
htmlcov/

# Anki specific
*.apkg
*.colpkg

# Temporary files
*.log
*.tmp
.ankiaddon
```

### Verificar Status Atual

Antes de criar `.gitignore`, verificar se já existem arquivos não rastreados:

```bash
git status --ignored
```

Se houver arquivos que deveriam estar ignorados (ex: `__pycache__/`), remover do repositório:

```bash
git rm -r --cached __pycache__/
git commit -m "chore: remove cached Python bytecode"
```

### Estimativa de Esforço

- **Complexidade**: Trivial
- **Tempo estimado**: 2 minutos
- **Arquivos afetados**: `.gitignore` (criar novo)
- **Testes necessários**: Não

### Prioridade

**P1 (Alta) para merge**: Boa prática básica de Git. Deve existir antes do primeiro commit com código.

---

## Issue #16: URLs Placeholder na Documentação

**Severidade**: 🟢 BAIXA
**Localização**: `README.md:69,71` e `config.md:60`
**Categoria**: Documentação
**Impacto**: Links quebrados para usuários

### Descrição do Problema

Documentação contém URLs placeholder que não funcionam:

**README.md**:
```markdown
- **Issues:** https://github.com/yourusername/anki-weekend-addon/issues
- **Documentation:** See `config.md` for detailed configuration options
- **AnkiWeb:** Coming soon
```

**config.md**:
```markdown
For issues or questions:
- GitHub Issues: https://github.com/yourusername/anki-weekend-addon
- AnkiWeb Reviews: Coming soon
```

### Solução

#### Opção 1: Substituir por URL Real (se repositório GitHub criado)

```markdown
- **Issues:** https://github.com/dpalis/anki-weekend-addon/issues
- **AnkiWeb:** https://ankiweb.net/shared/info/XXXXXXXXXX
```

#### Opção 2: Remover Placeholders (se ainda não publicado)

```markdown
- **Issues:** See addon configuration page in Anki for support
- **Documentation:** See `config.md` for detailed configuration options
```

### Quando Fazer

- **Antes de publicar no AnkiWeb**: URLs devem funcionar
- **Pode ser adiado**: Se addon ainda está em desenvolvimento privado

### Estimativa de Esforço

- **Complexidade**: Trivial
- **Tempo estimado**: 5 minutos
- **Arquivos afetados**: `README.md`, `config.md`
- **Testes necessários**: Não (verificar links funcionam)

### Prioridade

**P2 (Média) para release público**: Links quebrados são má experiência de usuário, mas não afetam funcionalidade.

---

## Issue Bônus: Considerações de Simplificação Adicional

### Variáveis com Nomes Redundantes

**Observação**: Variável `config` é reutilizada para significados diferentes:

```python
# Linha 66: 'config' = addon config
config = get_config()

# Linha 88: 'config' = deck config
config = mw.col.decks.get_config(deck['conf'])
```

**Solução** (se refatorar):
```python
addon_config = get_config()
deck_config = mw.col.decks.get_config(deck['conf'])
```

**Decisão**: Aceitável no contexto atual (escopos diferentes). Só mudar se causar confusão.

---

## Resumo de Issues de Baixa Prioridade

| Issue | Localização | Esforço | Quando Fazer | Bloqueia Merge? |
|-------|-------------|---------|--------------|-----------------|
| #13: Simplificação | Todo o arquivo | 4h | v2.1+ (opcional) | ❌ Não |
| #14: Placeholder Autor | `__init__.py:7` | 10s | Antes merge | ✅ Sim |
| #15: .gitignore | Raiz | 2min | Antes merge | ✅ Sim |
| #16: URLs Placeholder | README, config.md | 5min | Antes release público | ❌ Não |

**Tempo Total Estimado**: 4 horas (se fazer simplificação) ou 10 minutos (apenas blockers)

**Recomendação**:
1. **Fazer agora** (antes de merge): #14, #15
2. **Fazer antes de release público**: #16
3. **Considerar para v2.1+**: #13 (se código crescer)

---

## Checklist de Issues por Severidade

### 🔴 Críticos (MUST FIX - Blockers para Release)
- [ ] **Issue #1**: Armazenamento redundante (perda de dados)
- [ ] **Issue #2**: Compatibilidade Python 3.9
- [ ] **Issue #3**: Validação de entrada

### 🟠 Alta Prioridade (Corrigir antes de v2.1)
- [ ] **Issue #4**: Race condition (store reference)
- [ ] **Issue #5**: Primeiro uso em weekend
- [ ] **Issue #6**: Error handling
- [ ] **Issue #7**: Multi-dispositivo (parte de #1)

### 🟡 Média Prioridade (Melhorias recomendadas)
- [ ] **Issue #8**: State tracking (performance)
- [ ] **Issue #9**: Batch writes (performance)
- [ ] **Issue #10**: Duplicação de código (manutenibilidade)
- [ ] **Issue #11**: Magic numbers (legibilidade)
- [ ] **Issue #12**: Type hints consistency

### 🟢 Baixa Prioridade (Opcional)
- [ ] **Issue #13**: Simplificação (v2.1+)
- [ ] **Issue #14**: Placeholder autor (BEFORE MERGE)
- [ ] **Issue #15**: .gitignore (BEFORE MERGE)
- [ ] **Issue #16**: URLs placeholder (antes de publicar)

**Total de Issues**: 16
**Blockers para Merge**: 5 (#1, #2, #3, #14, #15)
**Recomendados para v2.1**: 7 (#4, #5, #6, #8, #9, #11, #12)
**Opcionais**: 4 (#7 incluído em #1, #10, #13, #16)
