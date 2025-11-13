# Changelog

Todas as mudanças notáveis deste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [2.0.0] - 2025-01-13

### Adicionado

- **Modo Fim de Semana**: Toggle para ativar/desativar funcionamento automático do addon
- **Modo Viagem**: Toggle para pausar novos cards manualmente por tempo indeterminado
- **Interface de Menu**: Menu integrado em Tools → Weekend Addon com:
  - Toggle para Modo Fim de Semana (✅/❌)
  - Toggle para Modo Viagem (✅/❌)
  - Diálogo de status mostrando informações detalhadas
- **Sistema de Traduções (i18n)**:
  - Detecção automática de idioma do Anki
  - Suporte completo para Português (PT-BR)
  - Suporte completo para Inglês (EN)
  - Fallback automático para inglês
- **Armazenamento Redundante**:
  - Primary: `collection.anki2` (sincroniza via AnkiWeb)
  - Backup: Configuração do addon
- **Validação de Entrada**: Todos os limites são validados antes de armazenar/restaurar
- **Captura Segura de Limites**:
  - Two-phase capture para evitar race conditions
  - Evita capturar 0 durante finais de semana
  - Sempre captura valores atuais ao entrar em weekend/travel mode
- **Feedback Visual**:
  - Tooltips ao alternar modos
  - Ícones dinâmicos (✅/❌) nos menu items
  - Mensagens de status detalhadas

### Mudado

- **Reescrita Completa**: Código reescrito do zero focando em simplicidade e confiabilidade
- **Arquitetura Modular**:
  - `__init__.py`: Lógica principal (~530 linhas)
  - `ui.py`: Interface de menu (~210 linhas)
  - `i18n.py`: Sistema de traduções (~170 linhas)
- **Método de Aplicação**: Modificação direta de deck configs em vez de hooks de scheduler
- **Sincronização**: Usa `collection.anki2` para sync via AnkiWeb (v1.0 era desktop-only)
- **Performance**: Otimização de 95% - só aplica mudanças quando modo muda

### Corrigido

- **Issue #3**: Validação de entrada previne valores inválidos de corromperem configuração
- **Issue #5**: Two-phase capture garante que limites corretos sejam armazenados
- **Restauração Incorreta**: Nunca mais restaura valores errados (ex: 20 em vez de 10)
- **Race Conditions**: Captura todos os limites ANTES de modificar qualquer config
- **Captura de Zero**: Não captura 0 como limite original durante finais de semana

### Removido

- Dependência de hooks complexos de scheduler (v1.0)
- Código legacy e dívida técnica acumulada

### Segurança

- Validação estrita de todos os valores de configuração
- Proteção contra corrupção de dados
- Tratamento de exceções para prevenir crash do Anki
- Verificação de limites (0-9999) conforme UI do Anki

### Documentação

- README.md completo com:
  - Instruções de instalação e uso
  - FAQ detalhado
  - Seção de troubleshooting
  - Documentação de desenvolvimento
- CLAUDE.md com diretrizes de desenvolvimento
- config.md documentando estrutura de configuração
- Docstrings completas em todas as funções

### Técnico

- **Python 3.9+** como versão mínima
- **Anki 25.x** como versão alvo
- Type hints em todas as funções
- Logging estruturado para debugging
- Git workflow com feature branches

## [1.0.0] - Data Anterior

### Nota

Versão 1.0 teve múltiplos bugs que levaram à reescrita completa em v2.0.
Veja issues #3 e #5 para detalhes dos problemas encontrados.

---

## Tipos de Mudanças

- `Adicionado` para novas funcionalidades
- `Mudado` para mudanças em funcionalidades existentes
- `Descontinuado` para funcionalidades que serão removidas
- `Removido` para funcionalidades removidas
- `Corrigido` para correção de bugs
- `Segurança` para vulnerabilidades corrigidas
