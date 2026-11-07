# Contrato de integração com d77void e persistência

## Topologia Git obrigatória

```text
d77void/                    # organização GitHub
├── d77void                  # repositório existente; read-only para este trabalho
├── d77-immutable            # repositório irmão; read-only para este trabalho
└── d77orphaned              # NOVO repositório autónomo; único local de trabalho
```

O nome da organização e os repositórios irmãos são contexto arquitetural, não autorização para editar, criar remotamente ou publicar. A criação do remoto requer autorização explícita.

## Regra principal

**D77orphaned é consumidor do ecossistema d77void, não seu proprietário.** O código, a configuração, os pacotes e os utilizadores atuais do d77void têm prioridade sobre conveniências desta PoC.

## Preservar explicitamente

1. **Repositório binário d77void:** URL, estrutura, metadados, assinaturas/chaves públicas, política de publicação, versões e compatibilidade. Não duplicar nem substituir o repositório; não publicar builds experimentais sem autorização separada.
2. **`mkd77.sh`:** localizar e documentar antes de usar. Preservar CLI, argumentos, defaults, caminhos, seleção de pacotes, fluxo de construção, lógica de boot, overlays, hooks, assinatura e comportamento para as ISOs existentes, **na medida em que existam realmente**. Não presumir que todas estas capacidades existem.
3. **Projetos gráficos:** pwm/X11; wasp/Wayland com Utumno; launcher e qsd77 existentes. Não inserir código específico do D77orphaned em componentes partilhados.
4. **Configs e branding:** não substituir ficheiros globais do d77void. Branding e presets exclusivos vivem em overlays/configuração do D77orphaned.
5. **Segurança e segredos:** nunca copiar chaves privadas de assinatura, tokens, passwords ou dados pessoais de builds anteriores.
6. **Regressão:** se uma alteração partilhada vier a ser indispensável, criar proposta separada, plano de rollback e testes das variantes existentes antes de aprovação.

## Estratégia preferida de build — a verificar

- Repositório fonte independente com manifesto de pacotes, overlays e eventual wrapper **próprio**.
- Reutilizar `void-mklive`/infraestrutura já disponível **se** a auditoria confirmar adequação.
- Consumir repositório d77void como origem adicional de pacotes compatíveis, mantendo assinaturas e verificações normais.
- **Proibidas alterações in-place de `mkd77.sh` e de qualquer repositório irmão.** Após investigação e aprovação, reutilizar código com cópia/adaptação **dentro de `d77orphaned`**, se licença e dependências permitirem, ou desenvolver builder próprio. Não propor mudanças no d77void como atalho para a PoC.

## Persistência de dados (opcional)

Objetivo: conservar documentação, scripts, configurações, ferramentas pessoais e eventualmente credenciais protegidas **sem** persistir sistema, pacotes ou `/`.

### Princípios

- ISO/ambiente live funciona sem partição de dados.
- Partição separada identificada por UUID/PARTUUID conhecido e validado; label humana apenas como conveniência.
- Preferir LUKS2 + filesystem suportado; desbloqueio explícito e sem credenciais embutidas.
- Montagem num ponto estável, por exemplo `/mnt/d77-data`, inicialmente sob ação do utilizador.
- Não ligar automaticamente `/home` ou `/etc` ao volume persistente; importar configs seletivamente só numa fase posterior.
- O sistema não deve bloquear o boot por volume ausente, encriptado, corrompido ou incompatível.
- Regravação/atualização da imagem live deve preservar a partição **somente se o método de escrita o garantir e isso tiver sido testado**. Um `dd` da ISO para o dispositivo inteiro pode destruir a tabela de partições e os dados; não prometer atualização segura sem um fluxo próprio.
- Um volume persistente **não é backup**; aconselhar cópias externas.

### Questões ainda abertas

- Método de preparar a pen (imagem híbrida, instalador próprio, cópia de ficheiros para partição boot, etc.).
- Compatibilidade BIOS/UEFI e layout GPT/MBR.
- Capacidade de reservar/expandir partição de dados e atualização da imagem sem a apagar.
- Ext4 vs outro filesystem, tamanho, política de montagem e ferramenta de desbloqueio.

Estas questões exigem teste; **não desenhar layout definitivo nem ferramenta de formatação na fase de investigação**.

## Separação de responsabilidades

| Local | Pode conter | Não deve conter |
|---|---|---|
| d77void existente | Pacotes e ferramentas generalistas, infraestrutura já validada | Lógica exclusiva D77orphaned imposta aos outros remasters |
| D77orphaned | Manifesto, overlay, branding, testes, documentação, scripts específicos futuros | Fork permanente de toda a infraestrutura d77void |
| Partição persistente do utilizador | Dados, scripts e configs pessoais, opcionalmente encriptados | Substituição da raiz live ou pressuposto obrigatório de boot |

## Gate de mudança

**Todos os commits do D77orphaned são feitos apenas no repositório `d77orphaned`.** Se algum dia surgir uma necessidade de alterar `d77void`, `d77-immutable` ou outro projeto, isso será um pedido separado, fora do escopo deste plano, sujeito a autorização explícita. Nunca executar essa alteração como efeito colateral da PoC.
