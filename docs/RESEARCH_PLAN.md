# Plano de investigação — bloqueio antes de construir

## Fase 0 — Reconhecimento (somente leitura)

- **Primeira pergunta:** x86_64 glibc ou musl. Determina se pwm, wasp e Utumno existem já compilados no repositório d77void para essa variante (resultado da fase 0: wasp e scenefx0.5 só existem em glibc — ver `BASELINE_AUDIT.md` §2).
- Identificar distribuição, arquitetura(s) alvo, versão Void, init e método live pretendido.
- Inspecionar repositório d77void e localizar `mkd77.sh` real. Determinar se é gerador de ISO, wrapper de `void-mklive`, script de remaster ou outra coisa. **Não assumir**.
- Levantar origem, licenças, dependências e estado de builds de pwm, wasp, Utumno, qsd77 e demais componentes já empacotados.
- Verificar funcionamento do `void-mklive` ou mecanismo existente na versão pretendida, incluindo boot BIOS/UEFI e opções de instalação/boot da pen.
- Identificar como os repositórios binários d77void são configurados, prioridades, assinatura/chaves e compatibilidade. Não incorporar chaves privadas.

**Saída:** `docs/BASELINE_AUDIT.md` com factos, referências, pontos desconhecidos e riscos. Se os repositórios não estiverem disponíveis, solicitar caminhos/URLs em vez de inventar.

## Fase 1 — Matriz de capacidades (sem instalar)

Pesquisar por **capacidade**, não por popularidade:

1. Discos: SMART/NVMe, identificação, tabela de partições, clonagem e recuperação de ficheiros.
2. Filesystems e volumes: ext4, XFS, Btrfs, FAT/exFAT, NTFS, LUKS, LVM, RAID; ZFS **somente se viável**, com análise especial do kernel/módulos.
3. Boot: EFI, GRUB, chroot, initramfs, identificação de bootloaders e recuperação controlada.
4. Rede: ligação com e sem fios, DNS, SSH, transferência segura, captura e diagnóstico.
5. Forense: imagem de disco, hashing, metadados, timeline/análise **se justificadas**, preservação e registo.
6. Segurança/pentesting limitado: descoberta e auditoria de rede, captura/análise de tráfego e verificação de serviços em sistemas próprios/autorizados.
7. Operação: terminal, editor, pager, man pages, firmware e drivers necessários, logs, compressão, ferramentas USB.
8. Gráficos: dependências mínimas para pwm/X11 e wasp/Wayland+Utumno, terminal e launcher existentes.

**Saída:** `docs/PACKAGE_INVENTORY.md` preenchido com evidência por candidato, incluindo alternativas e redundâncias.

## Fase 2 — Verificação de cada pacote

Para cada candidato:

- Nome **exato** em XBPS ou no repo d77void; arquitetura e variante libc.
- Origem e comando de verificação (`xbps-query`, `xbps-install -n` quando aplicável, consulta do índice de repositório, template Void etc.).
- Dependências, tamanho instalado e impacto estimado na ISO (distinguir estimativa de medição).
- Presença de binário, compatibilidade de runtime e teste funcional em VM/ambiente descartável quando possível.
- Restrições: permissões, kernel, módulos, firmware, rede, GUI, privilégios, licenças.
- Estado: `NÃO PESQUISADO`, `ENCONTRADO`, `TESTADO`, `INCOMPATÍVEL`, `A PORTAR`, `ADIADO`, `REJEITADO`.

**Importante:** pacote listado num índice ≠ pacote instalado ≠ ferramenta funcional em live.

## Fase 3 — Triagem e viabilidade

Construir três listas:

- **Core PoC**: indispensável, disponível e testável com baixo risco.
- **Optional/phase 2**: útil mas não necessário para demonstrar valor.
- **Out**: redundante, pesado, arriscado, não mantível ou sem benefício claro.

Estimar o número de ports próprios novos. Para cada port proposto, justificar por que não existe alternativa suficiente e estimar manutenção de versões/dependências. Se o total chegar a **5**, parar e rever o escopo com o utilizador; se se aproximar de **30**, a conceção é inviável — nada de «portar tudo».

## Fase 4 — Gate de aprovação

Apresentar ao utilizador:

- Lista final mínima, ferramentas opcionais e exclusões.
- Disponibilidade real e evidência de funcionamento.
- Ports necessários e esforço previsto.
- Reutilização exata do d77void e mudanças que **não** serão feitas.
- Plano de testes e riscos conhecidos.
- Perguntas pendentes (por exemplo, x86_64 glibc vs musl, método de escrita da pen, tamanho de ISO, firmware, persistência).

**Não passar à implementação sem aprovação explícita.**

## Fase 5 — Implementação futura (não autorizada por este documento)

Somente depois do gate: protótipo console-first; boot em VM e hardware; depois sessões gráficas; depois partição de dados opcional. Sem `forensics.qml` na PoC.

## Verificações funcionais mínimas futuras

- Boot UEFI e BIOS em condições suportadas; fallback TTY sem GUI.
- Rede e armazenamento identificados; ferramentas centrais executam sem bibliotecas em falta.
- pwm em X11; wasp + Utumno em Wayland, sem tentar Utumno no X11.
- Disco alvo não montado em escrita automaticamente; comandos destrutivos não executados por arranque.
- Com discos de teste com RAID MD, LVM, LUKS, swap e journal ext4/XFS por fechar: nada é assemblado, ativado, desbloqueado, montado nem tem o journal reproduzido sem ação explícita.
- Live funciona sem partição de dados; LUKS2 opcional desbloqueável apenas por ação do utilizador.
- Repetir testes com pen de dados ausente, bloqueada, danificada e com UUID divergente.
- Regressão: repo d77void, scripts e pacotes partilhados mantêm comportamento original.
