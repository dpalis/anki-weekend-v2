# 🟠 Issues de Alta Prioridade - Anki Weekend Addon v2.0

**Status**: Devem ser corrigidos antes de v2.1
**Data da Review**: 2025-11-12
**Total de Issues**: 4

---

## Issue #4: Race Condition no Acesso à Coleção

**Severidade**: 🟠 ALTA
**Localização**: `__init__.py:83-96, 105-116`
**Categoria**: Concorrência / Estabilidade
**Impacto**: Potencial crash do Anki ou estado inconsistente

### Descrição do Problema

O código verifica se `mw.col` não é None no início da função, mas depois acessa `mw.col` múltiplas vezes dentro do loop. Em teoria, a coleção pode ser fechada/descarregada entre o check inicial e os acessos posteriores, causando `AttributeError`.

### Código Problemático

```python
# Linhas 83-96: apply_weekend_mode()
def apply_weekend_mode() -> None:
    if not mw.col:  # ← Check inicial
        return

    for deck_id in mw.col.decks.all_names_and_ids():  # ← mw.col pode ser None aqui
        deck = mw.col.decks.get_legacy(deck_id.id)     # ← e aqui
        config = mw.col.decks.get_config(deck['conf'])  # ← e aqui

        if get_original_limit(deck['conf']) is None:
            store_original_limit(deck['conf'], config['new']['perDay'])

        config['new']['perDay'] = 0
        mw.col.decks.save(config)  # ← e aqui
```

**Janela de Race Condition**:
```
T=0: Check if not mw.col → OK (coleção existe)
T=1: Início do loop
T=2: [EVENTO EXTERNO] Anki fecha coleção (usuário troca perfil, sync falha, etc.)
T=3: Acesso mw.col.decks → AttributeError: 'NoneType' object has no attribute 'decks'
```

### Probabilidade

Embora o Anki seja majoritariamente single-threaded, existem cenários onde isso pode ocorrer:
- Troca rápida de perfil durante processamento
- Sync falha enquanto addon está iterando
- Hooks concorrentes do Anki (eventos internos)
- Janelas de tempo muito pequenas, mas não zero

### Solução: Store Reference Pattern

Armazenar referência local de `mw.col` uma vez, antes do loop:

```python
def apply_weekend_mode() -> None:
    """
    Define novos cards por dia = 0 para todos os decks.
    Armazena limites originais antes da modificação para restauração futura.
    Mudanças são marcadas para sincronização AnkiWeb automaticamente.
    """
    # Armazenar referência da coleção UMA VEZ
    col = mw.col
    if not col:
        return

    # Usar referência local em todo o código
    for deck_id in col.decks.all_names_and_ids():
        deck = col.decks.get_legacy(deck_id.id)
        config = col.decks.get_config(deck['conf'])

        # Armazenar original se ainda não armazenado
        if get_original_limit(deck['conf']) is None:
            store_original_limit(deck['conf'], config['new']['perDay'])

        # Definir limite para 0
        config['new']['perDay'] = 0
        col.decks.save(config)  # Marca para sincronização AnkiWeb


def apply_weekday_mode() -> None:
    """
    Restaura limites originais de novos cards por dia para todos os decks.
    Apenas restaura se limite original foi previamente armazenado.
    Mudanças são marcadas para sincronização AnkiWeb automaticamente.
    """
    # Armazenar referência da coleção UMA VEZ
    col = mw.col
    if not col:
        return

    # Usar referência local
    for deck_id in col.decks.all_names_and_ids():
        deck = col.decks.get_legacy(deck_id.id)
        config = col.decks.get_config(deck['conf'])

        # Restaurar original se existe
        original = get_original_limit(deck['conf'])
        if original is not None:
            config['new']['perDay'] = original
            col.decks.save(config)
```

### Por Que Isso Funciona

**Python References 101**:
```python
col = mw.col  # col agora aponta para o MESMO objeto que mw.col

# Se mw.col for definido como None depois:
mw.col = None

# col AINDA aponta para o objeto de coleção original
# porque Python usa contagem de referências
print(col)  # <Collection object> (ainda válido!)
```

O objeto de coleção não será garbage-collected enquanto `col` existir no escopo da função.

### Verificação Adicional (Defensiva)

Para máxima segurança, adicionar checks dentro do loop:

```python
def apply_weekend_mode() -> None:
    col = mw.col
    if not col:
        return

    try:
        deck_ids = col.decks.all_names_and_ids()
    except (AttributeError, RuntimeError) as e:
        print(f"[Anki Weekend Addon] ERRO: Coleção não disponível: {e}")
        return

    for deck_id in deck_ids:
        try:
            deck = col.decks.get_legacy(deck_id.id)
            if not deck:
                continue

            config = col.decks.get_config(deck['conf'])
            if not config:
                continue

            # ... resto da lógica

        except (AttributeError, KeyError, RuntimeError) as e:
            print(f"[Anki Weekend Addon] AVISO: Pulando deck {deck_id.id}: {e}")
            continue
```

### Estimativa de Esforço

- **Complexidade**: Baixa
- **Tempo estimado**: 15-30 minutos
- **Arquivos afetados**: `__init__.py` (linhas 77-117)
- **Testes necessários**: Difícil (requer simular fechamento de coleção)

### Prioridade

**P1 (Alta)**: Embora improvável, um crash durante startup é experiência de usuário muito ruim. Correção é trivial.

---

## Issue #5: Perda de Dados no Primeiro Uso em Fim de Semana

**Severidade**: 🟠 ALTA
**Localização**: `__init__.py:91-92`
**Categoria**: Lógica de Negócio / Integridade de Dados
**Impacto**: Limites originais incorretos armazenados permanentemente

### Descrição do Problema

Se o addon for instalado pela primeira vez em um sábado/domingo, e o usuário já tiver manualmente definido seus limites como 0 para o fim de semana, o addon armazena 0 como "limite original". Na segunda-feira, o addon restaura para 0 ao invés do valor real que o usuário usava durante a semana.

### Cenário Detalhado

```
Segunda a Sexta (sem addon):
  - Usuário tem deck com 20 novos cards/dia
  - Usuário estuda normalmente

Sábado 10:00 (sem addon):
  - Usuário manualmente abre Deck Options
  - Define "New cards per day" de 20 para 0
  - Quer descansar no fim de semana (processo manual)

Sábado 14:00:
  - Usuário descobre este addon
  - Instala addon
  - Abre Anki

Sábado 14:01:
  - on_profile_open() executa
  - is_weekend() retorna True
  - apply_weekend_mode() executa
  - Linha 91: get_original_limit(conf_id) retorna None (primeira vez)
  - Linha 92: store_original_limit(conf_id, 0)  ← PROBLEMA: armazena 0!
  - original_limits = {"123": 0}

Segunda 08:00:
  - on_profile_open() executa
  - is_weekend() retorna False
  - apply_weekday_mode() executa
  - Linha 115: original = 0
  - Linha 116: config['new']['perDay'] = 0  ← ERRO: deveria ser 20!
  - Usuário não recebe novos cards
```

**Resultado**: Limites permanecem em 0 para sempre. Usuário deve descobrir o problema e corrigir manualmente.

### Código Problemático

```python
# Linhas 90-92
if get_original_limit(deck['conf']) is None:
    store_original_limit(deck['conf'], config['new']['perDay'])
    # ↑ Se config['new']['perDay'] == 0, armazena 0 como "original"
```

**Lógica falha**:
- Assume que `config['new']['perDay']` no momento da captura é o "original"
- Não considera que o valor pode já estar modificado (manualmente ou por outro addon)
- Não distingue entre "0 é o valor real" vs "0 é temporário para fim de semana"

### Soluções Possíveis

#### Solução 1: Não Armazenar Zero (Simples)

```python
# Linhas 90-96
if get_original_limit(deck['conf']) is None:
    current_limit = config['new']['perDay']

    # NOVO: Só armazenar se limit > 0
    if current_limit > 0:
        store_original_limit(deck['conf'], current_limit)
    # Se current_limit == 0, esperar até dia de semana para capturar valor real
```

**Prós**:
- Simples
- Funciona para 99% dos casos
- Sem complexidade adicional

**Contras**:
- Usuário que REALMENTE quer 0 cards/dia na semana não seria capturado
- Edge case extremo: usuário com limit=0 permanente

#### Solução 2: Capturar Apenas em Dias de Semana (Mais Segura)

```python
def apply_weekend_mode() -> None:
    col = mw.col
    if not col:
        return

    for deck_id in col.decks.all_names_and_ids():
        deck = col.decks.get_legacy(deck_id.id)
        config = col.decks.get_config(deck['conf'])

        # NOVO: Verificar se é primeira execução
        if get_original_limit(deck['conf']) is None:
            current_limit = config['new']['perDay']

            # Se for fim de semana E limite já está em 0, não armazenar agora
            if is_weekend() and current_limit == 0:
                # Aguardar até dia de semana para capturar valor real
                print(f"[Anki Weekend Addon] Aguardando dia de semana para capturar limite original do deck config {deck['conf']}")
            elif current_limit > 0:
                # Seguro armazenar: ou é dia de semana, ou é fim de semana com limite ativo
                store_original_limit(deck['conf'], current_limit)

        # Definir limite para 0
        config['new']['perDay'] = 0
        col.decks.save(config)
```

**Prós**:
- Mais robusto
- Captura valor correto mesmo em instalação de fim de semana
- Explica ao usuário o que está acontecendo (via log)

**Contras**:
- Mais complexo
- Requer esperar até segunda para capturar (aceitável)

#### Solução 3: Avisar Usuário e Pedir Confirmação (Melhor UX)

```python
from aqt.utils import askUser

def apply_weekend_mode() -> None:
    col = mw.col
    if not col:
        return

    first_run = False
    uncaptured_decks = []

    for deck_id in col.decks.all_names_and_ids():
        deck = col.decks.get_legacy(deck_id.id)
        config = col.decks.get_config(deck['conf'])

        if get_original_limit(deck['conf']) is None:
            first_run = True
            current_limit = config['new']['perDay']

            if is_weekend() and current_limit == 0:
                uncaptured_decks.append(deck.get('name', f'Deck ID {deck_id.id}'))
            elif current_limit > 0:
                store_original_limit(deck['conf'], current_limit)

        config['new']['perDay'] = 0
        col.decks.save(config)

    # Se primeira execução em fim de semana com limites já em 0
    if first_run and uncaptured_decks:
        msg = f"""Weekend Addon: Primeira Execução

Foi detectado que este é o primeiro uso do addon em um fim de semana.

Os seguintes decks já têm limite = 0:
{chr(10).join('• ' + name for name in uncaptured_decks[:5])}
{f'... e mais {len(uncaptured_decks) - 5}' if len(uncaptured_decks) > 5 else ''}

O addon NÃO consegue saber qual era seu limite original (usado em dias de semana).

Na segunda-feira, por favor:
1. Abra Deck Options manualmente
2. Configure seus limites normais de dia de semana
3. O addon capturará e salvará esses valores

Ou: Configure agora em Tools → Add-ons → Weekend Addon → Config"""

        askUser(msg, defaultno=False, title="Weekend Addon: Configuração Inicial")
```

**Prós**:
- Melhor experiência de usuário
- Transparente sobre o que está acontecendo
- Dá instruções claras

**Contras**:
- Mais complexo
- Requer código de UI
- Pode assustar usuário iniciante

### Recomendação

**Usar Solução 2** (capturar apenas em dias de semana):
- Balanceio entre simplicidade e robustez
- Não requer UI adicional
- Resolve o problema core
- Log explica o que está acontecendo

### Implementação Recomendada

```python
def apply_weekend_mode() -> None:
    """
    Define novos cards por dia = 0 para todos os decks.
    Armazena limites originais antes da modificação para restauração futura.

    Nota: Em instalação durante fim de semana com limites já em 0,
    aguarda até dia de semana para capturar valores originais reais.
    """
    col = mw.col
    if not col:
        return

    for deck_id in col.decks.all_names_and_ids():
        deck = col.decks.get_legacy(deck_id.id)
        config = col.decks.get_config(deck['conf'])

        # Capturar original se ainda não armazenado
        if get_original_limit(deck['conf']) is None:
            current_limit = config['new']['perDay']

            # Lógica de captura segura
            if current_limit > 0:
                # Seguro: valor positivo é confiável
                store_original_limit(deck['conf'], current_limit)
            elif not is_weekend():
                # Dia de semana com limit=0: usuário realmente quer 0
                store_original_limit(deck['conf'], 0)
            # Else: Fim de semana com limit=0: AGUARDAR dia de semana
            # (não armazenar nada ainda)

        # Definir limite para 0 (mesmo que já esteja)
        config['new']['perDay'] = 0
        col.decks.save(config)
```

### Teste da Correção

```python
def test_first_run_weekend():
    """Simula instalação em fim de semana com limites já em 0."""

    # Setup: Simular sábado
    import unittest.mock as mock
    with mock.patch('__main__.is_weekend', return_value=True):

        # Setup: Deck com limit = 0 (manualmente definido pelo usuário)
        # Simular que original_limits está vazio (primeira execução)
        config = get_config()
        config['original_limits'] = {}
        mw.addonManager.writeConfig(__name__, config)

        # Executar apply_weekend_mode
        apply_weekend_mode()

        # Verificar: NÃO deve ter armazenado 0 como original
        stored = get_original_limit(123)  # Assumindo deck config ID = 123
        assert stored is None, f"ERRO: Armazenou 0 como original! stored={stored}"

        print("✓ Teste primeira execução em fim de semana: PASSOU")


def test_first_run_weekday():
    """Simula instalação em dia de semana."""

    import unittest.mock as mock
    with mock.patch('__main__.is_weekend', return_value=False):

        # Setup: Deck com limit = 20 (valor normal de dia de semana)
        # ... setup do deck ...

        # Executar apply_weekend_mode
        apply_weekend_mode()

        # Verificar: DEVE ter armazenado 20 como original
        stored = get_original_limit(123)
        assert stored == 20, f"ERRO: Não armazenou corretamente! stored={stored}"

        print("✓ Teste primeira execução em dia de semana: PASSOU")
```

### Estimativa de Esforço

- **Complexidade**: Média
- **Tempo estimado**: 1 hora
- **Arquivos afetados**: `__init__.py` (linhas 77-96)
- **Testes necessários**: Sim (cenário específico de primeira execução)

### Prioridade

**P1 (Alta)**: Afeta nova instalação, que é a primeira impressão do usuário. Bug de lógica que leva a comportamento permanentemente incorreto.

---

## Issue #6: Falta Tratamento de Erros

**Severidade**: 🟠 ALTA
**Localização**: `__init__.py:77-117` (todas as operações de deck)
**Categoria**: Estabilidade / Resiliência
**Impacto**: Crash do Anki ou estado inconsistente dos decks

### Descrição do Problema

Nenhuma operação de deck tem tratamento de exceções. Se QUALQUER erro ocorrer (KeyError, AttributeError, IOError, etc.), a exceção propaga e pode:

1. **Crashar o Anki** durante startup
2. **Deixar decks em estado inconsistente** (alguns pausados, outros não)
3. **Corromper config** se escrita falhar no meio

CLAUDE.md diz explicitamente: **"Fail gracefully - nunca quebrar a experiência do Anki"**

### O Que Pode Dar Errado

#### Erro 1: Estrutura de Deck Inesperada
```python
deck = col.decks.get_legacy(deck_id.id)
config = col.decks.get_config(deck['conf'])  # ← KeyError se deck não tem 'conf'
```

#### Erro 2: Estrutura de Config Mudou
```python
config['new']['perDay'] = 0  # ← KeyError se Anki mudou estrutura
```

#### Erro 3: Falha de I/O
```python
mw.addonManager.writeConfig(__name__, config)  # ← IOError se disco cheio
```

#### Erro 4: Deck Deletado Durante Iteração
```python
for deck_id in col.decks.all_names_and_ids():
    deck = col.decks.get_legacy(deck_id.id)  # ← Deck foi deletado entre chamadas
```

### Cenário de Falha Parcial

```
Processando 5 decks:
  Deck 1: Sucesso (perDay=0, original armazenado)
  Deck 2: Sucesso (perDay=0, original armazenado)
  Deck 3: CRASH - KeyError: 'conf'
  Deck 4: Não processado
  Deck 5: Não processado

Resultado: Usuário tem estado inconsistente:
  - Decks 1-2: Sem novos cards
  - Decks 4-5: Com novos cards (não pausados)
  - Usuário confuso: "Por que só alguns decks foram pausados?"
```

### Solução: Defensive Error Handling

```python
def apply_weekend_mode() -> None:
    """
    Define novos cards por dia = 0 para todos os decks.
    Armazena limites originais antes da modificação para restauração futura.
    Mudanças são marcadas para sincronização AnkiWeb automaticamente.

    Tratamento de erros: Falhas em decks individuais não impedem
    processamento de outros decks. Erros são logados mas não propagam.
    """
    col = mw.col
    if not col:
        return

    success_count = 0
    skip_count = 0
    error_count = 0

    # Obter lista de deck IDs com tratamento de erro
    try:
        deck_ids = col.decks.all_names_and_ids()
    except Exception as e:
        print(f"[Anki Weekend Addon] ERRO CRÍTICO: Falha ao obter lista de decks: {e}")
        return

    for deck_id in deck_ids:
        try:
            # Obter deck
            deck = col.decks.get_legacy(deck_id.id)
            if not deck:
                skip_count += 1
                continue

            # Verificar estrutura do deck
            if 'conf' not in deck:
                print(f"[Anki Weekend Addon] AVISO: Deck {deck_id.id} não tem 'conf', pulando")
                skip_count += 1
                continue

            # Obter config do deck
            config = col.decks.get_config(deck['conf'])
            if not config:
                print(f"[Anki Weekend Addon] AVISO: Config {deck['conf']} não encontrado, pulando")
                skip_count += 1
                continue

            # Verificar estrutura do config
            if 'new' not in config or 'perDay' not in config['new']:
                print(f"[Anki Weekend Addon] AVISO: Config {deck['conf']} tem estrutura inesperada, pulando")
                skip_count += 1
                continue

            # Armazenar original se ainda não armazenado
            if get_original_limit(deck['conf']) is None:
                try:
                    current_limit = config['new']['perDay']
                    if current_limit > 0 or not is_weekend():
                        store_original_limit(deck['conf'], current_limit)
                except Exception as e:
                    print(f"[Anki Weekend Addon] AVISO: Falha ao armazenar limite original para config {deck['conf']}: {e}")
                    # Continuar mesmo assim - pelo menos pausamos o deck

            # Definir limite para 0
            config['new']['perDay'] = 0
            col.decks.save(config)
            success_count += 1

        except (KeyError, AttributeError, TypeError) as e:
            # Erros de estrutura/tipo - deck específico problemático
            error_count += 1
            print(f"[Anki Weekend Addon] ERRO ao processar deck {deck_id.id}: {type(e).__name__}: {e}")
            continue

        except Exception as e:
            # Erro inesperado - logar mas continuar
            error_count += 1
            print(f"[Anki Weekend Addon] ERRO INESPERADO ao processar deck {deck_id.id}: {e}")
            import traceback
            traceback.print_exc()
            continue

    # Log resumo
    if error_count > 0 or skip_count > 0:
        print(f"[Anki Weekend Addon] Modo fim de semana aplicado: {success_count} sucesso, {skip_count} pulados, {error_count} erros")


def apply_weekday_mode() -> None:
    """
    Restaura limites originais de novos cards por dia para todos os decks.
    Apenas restaura se limite original foi previamente armazenado.
    Mudanças são marcadas para sincronização AnkiWeb automaticamente.

    Tratamento de erros: Falhas em decks individuais não impedem
    processamento de outros decks. Erros são logados mas não propagam.
    """
    col = mw.col
    if not col:
        return

    success_count = 0
    skip_count = 0
    error_count = 0

    try:
        deck_ids = col.decks.all_names_and_ids()
    except Exception as e:
        print(f"[Anki Weekend Addon] ERRO CRÍTICO: Falha ao obter lista de decks: {e}")
        return

    for deck_id in deck_ids:
        try:
            deck = col.decks.get_legacy(deck_id.id)
            if not deck or 'conf' not in deck:
                skip_count += 1
                continue

            config = col.decks.get_config(deck['conf'])
            if not config or 'new' not in config or 'perDay' not in config['new']:
                skip_count += 1
                continue

            # Restaurar original se existe
            original = get_original_limit(deck['conf'])
            if original is not None:
                config['new']['perDay'] = original
                col.decks.save(config)
                success_count += 1
            else:
                skip_count += 1

        except (KeyError, AttributeError, TypeError) as e:
            error_count += 1
            print(f"[Anki Weekend Addon] ERRO ao restaurar deck {deck_id.id}: {type(e).__name__}: {e}")
            continue

        except Exception as e:
            error_count += 1
            print(f"[Anki Weekend Addon] ERRO INESPERADO ao restaurar deck {deck_id.id}: {e}")
            import traceback
            traceback.print_exc()
            continue

    if error_count > 0 or skip_count > 0:
        print(f"[Anki Weekend Addon] Modo dia de semana aplicado: {success_count} restaurados, {skip_count} pulados, {error_count} erros")
```

### Wrapping Top-Level Function

Adicionar try-except na função de entrada também:

```python
def on_profile_open() -> None:
    """
    Executa quando perfil abre (startup + sync).
    Aplica modo apropriado baseado em flag de travel mode ou dia atual.

    Tratamento de erros: Captura TODAS as exceções para prevenir
    crash do Anki. Addon pode falhar, mas Anki continua funcionando.
    """
    try:
        if not mw.col:
            return

        config = get_config()

        # Prioridade 1: Travel mode
        if config.get('travel_mode', False):
            apply_weekend_mode()
        # Prioridade 2: Fim de semana
        elif is_weekend():
            apply_weekend_mode()
        # Prioridade 3: Dia de semana
        else:
            apply_weekday_mode()

    except Exception as e:
        # CRÍTICO: Não deixar exceção propagar para Anki
        print(f"[Anki Weekend Addon] ERRO CRÍTICO em on_profile_open: {e}")
        import traceback
        traceback.print_exc()

        # Opcionalmente mostrar ao usuário (não intrusivo)
        # from aqt.utils import tooltip
        # tooltip("Weekend Addon encontrou um erro. Verifique o console.", period=3000)
```

### Estimativa de Esforço

- **Complexidade**: Média
- **Tempo estimado**: 1.5-2 horas
- **Arquivos afetados**: `__init__.py` (linhas 77-147)
- **Testes necessários**: Sim (simular vários tipos de erro)

### Prioridade

**P1 (Alta)**: Princípio fundamental de defensive programming. CLAUDE.md explicitamente requer "Fail gracefully".

---

## Issue #7: Configuração Não Sincroniza Entre Dispositivos

**Severidade**: 🟠 ALTA
**Localização**: Arquitetura geral do addon
**Categoria**: Multi-Dispositivo / Experiência de Usuário
**Impacto**: Comportamento inconsistente entre dispositivos, confusão do usuário

### Descrição do Problema

A configuração do addon é armazenada em `meta.json` (via `mw.addonManager.getConfig()`), que **NÃO sincroniza via AnkiWeb**. Apenas código e `config.json` (defaults) sincronizam.

**Do research_cross_platform_behavior.md:40-43**:
```
Data que NÃO sincroniza:
- Addon code ou settings (Python addons são desktop-only)
- Addon configuration files
- Hooks e modificações baseadas em Python
```

### Cenário de Problema Real

```
Desktop A (Casa):
  Sexta 18:00: Usuário estuda
  Sexta 22:00: Modo fim de semana ativa
  Limites definidos para 0
  original_limits = {"123": 20, "456": 15}  ← Armazenado localmente
  Sincroniza com AnkiWeb (apenas deck configs, não addon config)

Laptop (Viagem):
  Sábado 10:00: Abre Anki, sincroniza
  Recebe: deck configs com limits=0 ✓
  NÃO recebe: original_limits do Desktop A ✗

  Sábado 14:00: Usuário decide voltar limites manualmente
  Muda para 25 e 10 (valores errados! Desktop A tinha 20 e 15)
  Sincroniza

Desktop A:
  Sábado 20:00: Sincroniza
  Recebe: limites 25 e 10 do Laptop
  Sobrescreve: limites 20 e 15 locais

Segunda:
  Desktop A: Restaura para 20 e 15 (seus valores locais)
  Laptop: Restaura para 25 e 10 (valores que usuário definiu manualmente)

  Resultado: CAOS - cada dispositivo restaura valores diferentes!
```

### Por Que Isso Acontece

```python
// Desktop A: meta.json (NÃO sincroniza)
{
  "original_limits": {"123": 20, "456": 15}
}

// Laptop: meta.json (diferente, NÃO sincroniza)
{
  "original_limits": {"123": 25, "456": 10}
}

// AnkiWeb: (não armazena meta.json de addons)
// Cada dispositivo tem sua própria "verdade"
```

### Solução

**JÁ COBERTA NO ISSUE #1 (Crítico)**: Usar collection config como armazenamento primário.

Collection config **sincroniza via AnkiWeb**, então todos os dispositivos terão a mesma `original_limits`.

### Resumo da Solução (Issue #1)

```python
# Armazenar em collection config (sincroniza)
mw.col.set_config('weekend_addon_original_limits', json.dumps(limits))

# Ler de collection config (sincroniza)
limits = json.loads(mw.col.get_config('weekend_addon_original_limits', '{}'))
```

### Nota Importante: Mobile

**AnkiMobile (iOS) e AnkiDroid não suportam addons Python.**

Estratégia atual (modificar deck configs) funciona para mobile:
- Desktop pausa cards (define limits=0)
- Sincroniza via AnkiWeb
- Mobile recebe configs com limits=0
- Usuário não vê novos cards no mobile ✓

**Mas**: Mobile não pode restaurar na segunda (sem addon rodando).

**Solução User-Facing**:
- Documentar que mobile receberá limits pausados
- Usuário deve sincronizar com desktop na segunda, OU
- Usuário manualmente restaura limites no mobile

**Do RECOMMENDATIONS.md:324-329**:
```
Estratégia 1: Modificar Deck Config (ESCOLHIDA)
Pros:
- Funciona cross-platform via sync
- Não invasivo ao SRS
- Reversível

Cons:
- Mobile não restaura automaticamente (requer sync com desktop)
```

### Estimativa de Esforço

- **Complexidade**: N/A (já coberto no Issue #1)
- **Tempo estimado**: Incluído no Issue #1
- **Documentação**: Adicionar nota sobre mobile no README.md

### Prioridade

**P1 (Alta)**: Incluído como parte do Issue #1 (armazenamento redundante). Sem isso, multi-dispositivo não funciona corretamente.

---

## Resumo de Issues de Alta Prioridade

| Issue | Localização | Esforço | Impacto |
|-------|-------------|---------|---------|
| #4: Race Condition | `__init__.py:83-116` | 30min | Crash potencial |
| #5: Primeiro Uso Weekend | `__init__.py:91-92` | 1h | Limites incorretos |
| #6: Falta Error Handling | `__init__.py:77-147` | 2h | Crashes e inconsistência |
| #7: Sync Multi-Dispositivo | Arquitetura | Issue #1 | Comportamento divergente |

**Tempo Total Estimado**: 3.5-4 horas (excluindo #7 que é parte de #1)
**Recomendação**: Corrigir antes de v2.1 ou uso público extensivo
