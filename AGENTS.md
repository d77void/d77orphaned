# AGENTS.md — Regras para 1100, 1200 e outros agentes

## Missão

Planear e, **apenas após autorização**, implementar a PoC D77orphaned, sistema live Void Linux orientado a recuperação, diagnóstico, análise forense cuidadosa e uma seleção limitada de pentesting autorizado.

## Regra zero: PLAN FIRST

A tarefa inicial é **investigar e documentar**. Não escrever código de build, não instalar pacotes no host, não alterar o repositório d77void, não portar software e não executar `mkd77.sh` até existir um inventário revisto e uma decisão explícita do utilizador. Se a execução for pedida futuramente, separar essa autorização da autorização para alterar projetos partilhados.

**Exceção (fase 2):** a partir da fase 2 é permitido instalar pacotes **apenas em ambiente descartável** (VM, chroot ou contentor criado para o efeito e destruído no fim) para verificar dependências e funcionamento. Nunca no host, nunca em máquinas pessoais do utilizador e nunca em repositórios irmãos.

## Antes de propor mudanças

1. Localizar e ler os ficheiros relevantes; **não presumir** estrutura, caminhos, sintaxe ou semântica de `mkd77.sh`.
2. Identificar branch, estado Git, alterações locais, remotes, submódulos e origem dos pacotes d77. Não modificar ficheiros com alterações não relacionadas.
3. Distinguir: **observado**, **verificado por comando**, **inferido**, **proposto** e **desconhecido**.
4. Não inventar disponibilidade de pacotes Void, dependências, versões, compatibilidade com arquitetura ou funcionamento real.
5. Registar comandos de verificação, data, arquitetura, repositório e resultados em `docs/PACKAGE_INVENTORY.md` ou relatório equivalente.

## Política de pacotes

Prioridade: (1) Void oficial e funcional; (2) binário já existente e utilizável do repositório d77void; (3) build/empacotamento próprio apenas quando essencial e sustentável; (4) excluir/adiar. **Nunca** converter uma lista de desejos em lista de instalação sem validação.

Classificar esforço de port por pacote: trivial, baixo, médio, alto, inviável/desaconselhado. Contar dependências novas e manutenção contínua, não apenas o tempo de compilar uma vez. Limiares de ports novos indispensáveis:

- **≥ 5:** parar e apresentar ao utilizador uma revisão de escopo antes de continuar.
- **≈ 30:** a conceção é inviável; propor redução drástica de escopo.

Em ambos os casos, **não iniciar os ports**. Estes números são sinais de alerta, não orçamento de trabalho.

## Fronteiras entre projetos

- O repositório fonte **`d77void/d77orphaned` é novo e independente**, irmão de `d77-immutable` na organização GitHub `d77void`. Nunca trabalhar dentro de `d77void`, numa branch desse projeto, nem dentro de `d77-immutable`.
- O repositório **binário** d77void é partilhado/reutilizado, não copiado nem reorganizado por conveniência da PoC.
- **Nunca alterar o `mkd77.sh` original ou quaisquer ficheiros de repositórios irmãos no âmbito deste projeto.** Investigar em modo read-only. Se necessário, propor uma cópia/adaptação local ou um builder próprio em `d77orphaned`, sujeito a aprovação, licença e rastreabilidade da origem.
- Não alterar configurações globais de Utumno, qsd77, pwm ou wasp para acomodar uma necessidade exclusiva do D77orphaned.
- Preferir overlays e configurações **locais ao D77orphaned**; evitar hardcodes e dependências circulares.
- Não publicar pacotes no repositório d77void sem revisão separada de segurança, licenças, manutenção e impacto nos utilizadores atuais.

## Segurança e integridade

- Não montar discos alvo em escrita automaticamente; qualquer escrita requer ação consciente e confirmação.
- Distinguir `mount -o ro` de garantias reais de preservação forense (journaling, replay, swap, automount, alterações em dispositivos, cadeia de custódia). Riscos concretos a tratar e testar:
  - montagem automática de RAID (mdadm) e ativação de LVM pelas regras do udev, também **depois** do initramfs;
  - abertura automática de volumes LUKS pelo dracut (`rd.luks=0`, `rd.md=0`, `rd.lvm=0`, `rd.dm=0` como requisito a testar);
  - udisks2/udiskie/gvfs a montar discos nas sessões gráficas (não incluir em autostart);
  - ext4 e XFS fazem *replay* do journal mesmo com `ro`: usar `noload` (ext4) / `norecovery` (XFS) e `blockdev --setro` antes de montar;
  - ativação automática de swap encontrada nos discos alvo.
- Ferramentas de pentesting são apenas para ambientes autorizados; não incluir mecanismos de persistência clandestina, recolha de credenciais ou exploração automatizada como comportamento por defeito.
- Dados persistentes são opcionais e independentes da imagem; LUKS2 recomendado; não desbloquear automaticamente segredos.
- Scripts de instalação de pen não podem reformatar dispositivos sem confirmação inequívoca de dispositivo, partições e perda de dados.

## Entregáveis da primeira fase

- Inventário verificado com fontes/comandos e lacunas.
- Matriz de funções essenciais e alternativas.
- Auditoria do `mkd77.sh` e do que pode ser **reutilizado sem modificar**.
- Estimativa de esforço, footprint e riscos, incluindo dependências de GUI e arquitetura.
- Lista **mínima** proposta para PoC, lista adiada e lista rejeitada.
- Perguntas de decisão ao utilizador, incluindo eventuais bloqueios.

## Forma de comunicar

Ser direto, técnico e conciso. Não declarar sucesso sem teste. Não fazer trabalho adicional «já agora». Não criar ficheiros auxiliares desnecessários. Quando uma ideia surgir, perguntar: **que problema resolve na PoC?** Se não houver resposta concreta, registar como futuro opcional.
