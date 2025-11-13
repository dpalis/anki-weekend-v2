# Weekend Addon v2.0

Pause novos cards aos finais de semana enquanto mantém seus reviews ativos.

## Recursos

- **Modo Fim de Semana**: Pausa automaticamente novos cards aos sábados e domingos
- **Modo Viagem**: Pausa novos cards por tempo indeterminado (útil para férias)
- **Detecção automática de idioma**: Suporte para Português (PT-BR) e Inglês
- **Interface simples**: Menu integrado em Tools → Weekend Addon
- **Sincronização via AnkiWeb**: Configurações sincronizam entre dispositivos
- **Restauração segura**: Sempre restaura seus limites originais corretamente

## Como Usar

### Instalação

1. Baixe o arquivo `.ankiaddon` da [página de releases](https://github.com/dpalis/anki-weekend-addon/releases)
2. No Anki, vá em **Tools → Add-ons**
3. Clique em **Install from file...** e selecione o arquivo baixado
4. Reinicie o Anki

### Uso Básico

Acesse **Tools → Weekend Addon** no menu do Anki:

- **✅ Modo Fim de Semana**: Ativa/desativa a pausa automática nos finais de semana
  - Quando ativado (padrão): Novos cards são pausados automaticamente aos sábados e domingos
  - Quando desativado: Addon não faz modificações automáticas

- **✅ Modo Viagem**: Ativa/desativa pausa manual de novos cards
  - Quando ativado: Todos os novos cards ficam pausados até você desativar
  - Útil para férias, viagens ou períodos sem estudo

- **Ver Status**: Mostra informações detalhadas sobre o estado atual do addon

### Como Funciona

O addon modifica temporariamente a configuração "Novos cards por dia" dos seus decks:

- **Durante a semana** (segunda a sexta): Seus limites normais estão ativos
- **Nos finais de semana** (sábado e domingo): Novos cards = 0
- **Reviews**: Continuam sempre ativos, independente do dia

Seus limites originais são armazenados de forma segura e restaurados automaticamente:
- Na segunda-feira (fim do fim de semana)
- Ao desativar o Modo Viagem
- Ao desativar o Modo Fim de Semana

## Prioridade de Modos

O addon segue esta ordem de prioridade:

1. **Modo Fim de Semana OFF**: Restaura limites e não faz modificações automáticas
2. **Modo Viagem ON**: Pausa novos cards (ignora dia da semana)
3. **Final de semana** (sábado/domingo): Pausa novos cards
4. **Dia de semana** (segunda a sexta): Restaura limites originais

## Idiomas Suportados

- **Português (PT-BR)**: Detectado automaticamente
- **Inglês (EN)**: Idioma padrão

O addon detecta o idioma do Anki e ajusta automaticamente a interface.

## Limitações Conhecidas

### Deck-Specific Overrides

O addon **não funciona** com decks que usam configurações individuais na aba "This deck".

**Por quê?**
Quando você usa "This deck" no Anki, o deck não segue um preset compartilhado. O addon só consegue modificar presets compartilhados, não configurações individuais de decks.

**Solução:**
1. Abra as opções do deck problemático
2. Na aba "This deck", clique no dropdown ao lado de "Options group"
3. Selecione um preset compartilhado (ex: "Default") ou crie um novo
4. Salve as alterações
5. O addon agora funcionará com esse deck

**Planejamento futuro:**
Suporte para deck-specific overrides está planejado para v2.1. Veja [Issue #17](https://github.com/dpalis/anki-weekend-addon/issues/17).

## Perguntas Frequentes

### O que acontece com meus reviews?

Nada! O addon **apenas** modifica novos cards. Reviews continuam normais sempre.

### Meus limites originais estão seguros?

Sim! O addon usa armazenamento redundante:
- Primary: Dentro do arquivo `collection.anki2` (sincroniza via AnkiWeb)
- Backup: Na configuração do addon

### O addon sincroniza entre dispositivos?

Sim! As configurações são armazenadas no `collection.anki2`, que sincroniza via AnkiWeb.

### Posso usar em múltiplos perfis?

Sim! Cada perfil do Anki tem suas próprias configurações independentes.

### O que acontece se eu desinstalar o addon?

Seus limites serão restaurados automaticamente na próxima vez que você abrir o Anki (mesmo sem o addon instalado), pois os limites ficam salvos no banco de dados.

## Resolução de Problemas

### Addon não aparece no menu Tools

1. Verifique se o addon está ativo em **Tools → Add-ons**
2. Reinicie o Anki
3. Verifique se você abriu um perfil (addon só funciona com perfil aberto)

### Limites não estão sendo restaurados corretamente

1. Vá em **Tools → Weekend Addon → Ver Status**
2. Verifique quantos limites estão armazenados
3. Se estiver incorreto, desative e reative o Modo Fim de Semana durante um dia de semana
4. O addon recapturará seus limites atuais

### Deck específico não está sendo afetado

Veja a seção [Limitações Conhecidas](#limitações-conhecidas) acima.

## Desenvolvimento

### Estrutura do Projeto

```
Anki Weekend Addon v2/
├── __init__.py       # Lógica principal do addon
├── ui.py             # Interface de menu
├── i18n.py           # Sistema de traduções
├── config.json       # Configurações padrão
├── manifest.json     # Metadados do addon
└── README.md         # Este arquivo
```

### Testando em Modo Desenvolvedor (Mac)

1. Clone o repositório
2. Crie um symlink para o diretório de addons do Anki:
```bash
ln -s "/caminho/para/Anki Weekend Addon v2" \
      "/Users/seu-usuario/Library/Application Support/Anki2/addons21/weekend_addon"
```
3. Reinicie o Anki
4. Modificações no código refletem após reiniciar o Anki

### Logs de Debug

O addon imprime logs no console. Para vê-los no Mac:

```bash
/Applications/Anki.app/Contents/MacOS/anki
```

Procure por linhas com `[Weekend Addon]`.

## Changelog

Veja [CHANGELOG.md](CHANGELOG.md) para histórico completo de versões.

## Licença

MIT License - veja LICENSE para detalhes.

## Autor

Daniel Palis

## Contribuindo

Contribuições são bem-vindas! Por favor:

1. Abra uma issue descrevendo o bug ou feature
2. Faça fork do repositório
3. Crie uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
4. Commit suas mudanças (`git commit -m 'Add: Minha feature'`)
5. Push para a branch (`git push origin feature/MinhaFeature`)
6. Abra um Pull Request

## Agradecimentos

Obrigado à comunidade Anki por todo o suporte e feedback!
