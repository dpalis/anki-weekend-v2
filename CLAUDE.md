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

### 1. Simplicidade Acima de Tudo
- Código deve ser óbvio à primeira leitura
- Evitar abstrações desnecessárias
- Preferir clareza sobre cleverness
- Se algo parece complicado, provavelmente está errado

### 2. Modularidade
- Separação clara de responsabilidades
- Cada módulo tem um propósito específico e bem definido
- Baixo acoplamento entre componentes
- Fácil de testar isoladamente

### 3. Estabilidade e Confiabilidade
- Código bem testado
- Tratamento explícito de edge cases
- Logging adequado para debugging
- Fail gracefully - nunca quebrar a experiência do Anki

### 4. Facilidade de Expansão
- Arquitetura que permite adicionar features sem reescrever código existente
- Código autodocumentado
- Documentação clara de pontos de extensão

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