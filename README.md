# D77orphaned — Proof of Concept

> **Estado: PLANEAMENTO / INVESTIGAÇÃO.** Este repositório não declara nenhuma ISO funcional nem qualquer pacote validado.

## Visão

D77orphaned é uma proposta de sistema **live de recuperação, diagnóstico e análise**, baseado em **Void Linux**, com uma seleção pequena e justificada de ferramentas de segurança/pentesting para uso autorizado. Referência conceptual: **mais Grml do que Kali**. Não é uma distribuição independente, uma variante generalista do d77void, nem um substituto do Kali/Parrot/BlackArch.

## Identidade e fronteira do repositório

- **Novo repositório Git autónomo `d77void/d77orphaned`**, na mesma organização que `d77-immutable` e os restantes projetos. Não é um subdiretório, branch ou workspace de desenvolvimento do repositório `d77void`.
- **Toda a experimentação e todos os commits do D77orphaned ficam exclusivamente no seu próprio repositório.** Repositórios irmãos são dependências externas, não locais de trabalho.
- A auditoria de `d77void`, `mkd77.sh` e do repositório binário é **somente de leitura**. Se for útil aproveitar código, propor cópia/adaptação local no novo repositório, com proveniência e licença respeitadas; nunca editar o original.
- Nenhum agente pode criar ou publicar o repositório remoto sem autorização; inicialmente pode preparar o diretório Git local e a documentação, se solicitado.

## Decisões de arquitetura já tomadas

- Base Void Linux e gestão de pacotes XBPS; **não** criar gestor de pacotes, init ou repositório binário próprio.
- Uma ISO inicialmente; consola/TTY plenamente utilizável sem sessão gráfica.
- Dois ambientes opcionais na mesma ISO: **pwm (X11)** e **wasp (Wayland) + Utumno**. Utumno é Wayland-only e não deve ser proposta para pwm/X11.
- Reutilizar shells, compositores, ferramentas e pacotes **existentes** do ecossistema d77, sem alterar os projetos generalistas para servir esta ISO.
- Launcher existente para abrir aplicações. **Sem** dashboard `forensics.qml`, integrações novas no qsd77 ou painéis especiais na primeira prova de conceito.
- Persistência **opcional e apenas de dados** numa partição separada; sem overlay persistente de `/`, sem persistência integral de pacotes. Preferir LUKS2 quando houver dados sensíveis.
- Nenhuma operação destrutiva sobre discos alvo sem escolha explícita e confirmação; leitura não é sinónimo automático de preservação forense.

## Ordem de trabalho obrigatória

1. Ler `AGENTS.md`, `docs/RESEARCH_PLAN.md`, `docs/PACKAGE_INVENTORY.md` e `docs/INTEGRATION_CONTRACT.md`.
2. Inventariar o estado **real** do repositório d77void, dos pacotes próprios e do `mkd77.sh` — apenas leitura.
3. Investigar pacotes Void e ferramentas de recuperação/segurança com evidências reproduzíveis.
4. Classificar os pacotes, estimar esforço de manutenção e **apresentar decisões ao utilizador**.
5. Só depois de aprovação, preparar um plano de implementação e um protótipo mínimo.

**Gate:** na fase de investigação, nenhuma implementação ou alteração a scripts de build. **Em nenhuma fase existe autorização implícita para editar repositórios irmãos**, incluindo `d77void` e `d77-immutable`. O `mkd77.sh` original é sempre apenas de leitura; adaptações futuras, se aprovadas, vivem em `d77orphaned`.

## Escopo inicial

Recuperação de dados, diagnóstico de discos e sistemas de ficheiros, inspeção de boot/EFI, rede de emergência e ferramentas limitadas de análise e teste de segurança autorizado. A lista final depende da investigação; nomes sugeridos nos documentos são **candidatos, não pacotes confirmados**.

## Fora do escopo da PoC

Nova distro independente, kernel próprio, ambiente gráfico novo, interface QML forense, alterações a Utumno/qsd77/pwm/wasp, catálogo de centenas de ferramentas ofensivas, sincronização de credenciais, persistência da raiz, automações destrutivas e infraestrutura de pacotes duplicada.

## Critério de sucesso

Uma imagem que arranque em hardware real e VM, forneça consola útil, disponibilize ferramentas **verificadas**, permita iniciar cada sessão gráfica de forma controlada, não altere discos alvo por defeito e continue operacional sem partição persistente. Não prometer capacidades não testadas.
