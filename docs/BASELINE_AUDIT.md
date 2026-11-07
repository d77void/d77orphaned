# BASELINE_AUDIT — Fase 0 (somente leitura)

- **Data:** 2026-11-07
- **Repositório auditado:** `https://github.com/d77void/d77void`, branch `main`, commit `c567d0cf` (2026-11-05), versão `0.26`. Clone limpo, sem alterações locais. 1 submódulo (`common/.bash_it`, Bash-it), não inicializado.
- **Índices consultados (descarregados e lidos, nada instalado):**
  - Void `current/x86_64-repodata`, `current/nonfree/x86_64-repodata`, e equivalentes `musl`
  - d77void `sourceforge.net/projects/d77void/files/d77void-repo/x86_64-repodata` e `d77void-musl/x86_64-musl-repodata`
- **Pacotes d77 abertos para inspeção (ELF/ficheiros):** `qsd77-1.3.3_1`, `utumno-0.2.0_1`, `wasp-0.10.1_1`, `pwm-0.6.7_1` (x86_64).
- **Ambiente da auditoria:** host Ubuntu 24.04 (não Void). **Nada foi construído, instalado ou arrancado.** Nenhum ficheiro do d77void foi alterado.

Legenda: **[OBS]** observado no código · **[VER]** verificado por comando · **[INF]** inferido · **[PROP]** proposto · **[DESC]** desconhecido

---

## 1. O que é o `mkd77.sh`

- [OBS] O repositório é um **fork do `void-mklive`** (README). Licenças: `COPYING` BSD-2 (void-mklive, Juan RP / Dave Elusive) e `LICENSE` MIT (Daniel Azevedo, 2025).
- [OBS] `mkd77.sh` é um **wrapper de `mklive.sh`**, adaptado de `mkiso.sh`. Não gera ISO sozinho: monta `PKGS`, `SERVICES` e um diretório temporário `INCLUDEDIR`, e no fim chama:
  ```
  ./mklive.sh -a "$TARGET_ARCH" -o "$IMG" -p "$PKGS" -S "$SERVICES" -I "$INCLUDEDIR" [-v kernel] [-r repo…] "$@"
  ```
- [OBS] Pontos de entrada: `d77` → `mkd77.sh`; `d77nc` → `--nc`; `musl-d77` → `--musl`; `musl-d77nc` → `--musl --nc`.
- [OBS] CLI: `-a arch`, `-b variante` (repetível), `-d data`, `-t arch-data-variante`, `-r repo`, `--musl`, `--nc`, `-h`, `-V`; tudo depois de `--` passa para `mklive.sh`.
- [OBS] **As variantes estão codificadas** num `case $variant in … esac` (~30 entradas: base, pwm, wasp, qsd77, spitfire, hyprland…). **Não há forma de definir uma variante nova sem editar `mkd77.sh`.** → O D77orphaned não pode usar o `mkd77.sh` sem o modificar.
- [OBS] Cada variante combina listas partilhadas (`D77_CORE`, `XORG_PKGS`, `WAYLAND_PKGS`, `$CALAMARES`) e funções `include_*` que copiam `common/` e `<variante>/skel` para `INCLUDEDIR/etc/skel`.
- [OBS] O instalador (`d77void-installer`, de `installer.sh`) só é incluído com `--nc` em x86_64/i686; caso contrário é um stub.

### `mklive.sh` (o construtor real)
- [OBS] Opções úteis: `-p` pacotes, `-S` serviços, `-I` diretório de inclusão (repetível), `-C` cmdline do kernel, `-T` título, `-k` keymap, `-l` locale, `-x` script pós-setup, `-c/-H` caches, `-s/-i` compressão, `-v` kernel.
- [OBS] Obriga a ser executado **a partir da raiz do repositório** (`. ./lib.sh`, `keys/`, `dracut/`, `grub/`, `isolinux/` por caminho relativo).
- [OBS] Escreve `xbps-cachedir-*` e `mklive-build.*` no diretório atual, salvo `-c`/`-H` e a variável `ROOTDIR`.
- [OBS] Acrescenta **sempre** os repositórios Void oficiais (`current`, `current/musl`, `current/aarch64`) aos `-r` passados.
- [OBS] ISO híbrida (isolinux BIOS + GRUB EFI em partição GPT anexada), squashfs xz, overlay **overlayfs**, label fixa `VOID_LIVE`. Em x86 inclui sempre `syslinux grub-i386-efi grub-x86_64-efi memtest86+` → **o memtest86+ já vem no menu de arranque**.
- [OBS] Cmdline de todas as entradas GRUB/isolinux: `root=live:CDLABEL=VOID_LIVE ro … rd.luks=0 rd.md=0 rd.dm=0 …`. **O initramfs já não monta automaticamente LUKS, MD nem DM.** Ver §5 para o que acontece depois do pivot.
- [OBS] Entradas: normal, RAM (`rd.live.ram`), sem gráficos (`nomodeset`), e as três com síntese de voz.

### Módulo dracut `vmklive` (comportamento live)
- [OBS] `adduser.sh`:
  - cria o utilizador `anon` com os grupos `audio,video,wheel`;
  - **define a palavra-passe `voidlinux` para root e para anon**;
  - dá `NOPASSWD: ALL` no sudo;
  - escreve uma regra polkit que **autoriza tudo ao grupo `wheel` sem pedir nada**.
- [OBS] Herdado do void-mklive, mas relevante: `mkd77.sh` ativa **`sshd` em todas as variantes** (`SERVICES="sshd chronyd"`). Ver §5.

## 2. Repositório binário d77void

- [VER] x86_64: **74 pacotes**; x86_64-musl: **38 pacotes**. Assinados com RSA-4096, `signature-by: Daniel Azevedo <daniazevedo77@posteo.net>`.
- [VER] A chave pública no `index-meta.plist` é **idêntica byte a byte** a `keys/2b:d7:d1:cf:67:ab:53:3a:56:03:f5:f0:c2:de:a6:1a.plist` no repositório. As outras duas chaves em `keys/` são da Void Linux. **Não há chaves privadas no repositório.**
- [OBS] URL documentado no INSTALL.md: `https://sourceforge.net/projects/d77void/files/d77void-repo` (e `d77void-musl`).
- [VER] Diferenças relevantes entre glibc e musl:

| Pacote | x86_64 | x86_64-musl |
|---|---|---|
| `pwm` | 0.6.7_1 | 0.6.7_1 |
| `wasp` | 0.10.1_1 | **AUSENTE** |
| `scenefx0.5` (dependência do wasp) | 0.5_1 | **AUSENTE** |
| `utumno` | 0.2.0_1 | 0.2.0_1 |
| `qsd77` | 1.3.3_1 | 1.3.3_1 |
| `fresh-editor`, `joshuto`, `ollama` | presentes | ausentes |

→ **[VER] O ambiente wasp + Utumno só existe hoje em x86_64 glibc.** Em musl obrigaria a portar `wasp` e `scenefx0.5`.

## 3. Componentes gráficos — o que realmente precisam

### pwm (X11)
- [VER] Binário Rust; `NEEDED`: libX11, libXft, fontconfig, libgcc_s, libc. Depende de `dmenu`, `d77-st`, `wireless_tools`, `font-JetBrainsMono`.
- [VER] O pacote traz `/etc/xdg/pwm/startup.sh`, que arranca **`udiskie -a` (montagem automática)**, além de conky, feh, dunst, xcompmgr, xautolock+slock, redshift e sxhkd.
- [OBS] `config.toml.example` documenta `startup_script = "/etc/xdg/pwm/startup.sh"`. **[INF]** Isto pode ser sobreposto na configuração do utilizador, sem tocar no pacote. Falta testar.
- [OBS] A sessão (`pwm.desktop`) é `dbus-launch pwm`. Na variante d77void o login é feito pelo SDDM.

### wasp + Utumno (Wayland)
- [VER] `wasp`: binário C (dwl), com libwlroots-0.20, libscenefx-0.5, lua5.4, fcft, libinput e xkbcommon. `wasp-session` faz `dbus-run-session -- sh -c 'wasp-statusbar | wasp'` e grava o registo em `~/.local/state/wasp/`.
- [VER] **`utumno` é só QML** (`/usr/share/quickshell/utumno/…`) e corre com o **Quickshell** (`qs -c utumno`). O pacote **não declara** `quickshell` nem `qsd77` como dependência; declara apenas power-profiles-daemon, alsa-utils, alsa-tools, brightnessctl, wireless_tools e matugen.
- [VER] **`qsd77` é uma CLI em Go**, ligada só a libc/libresolv, que envia chamadas IPC ao Quickshell (`qsd77 -c utumno launcher`).
- [OBS] Na variante d77void `wasp`, o `quickshell` só entra por acaso, através de `include_greetd` (`dwl greetd quickshell`). **→ O D77orphaned tem de listar explicitamente `quickshell` e `qsd77`.**
- [OBS] O skel do wasp (`wasp/skel/.config/wasp/config.lua`) arranca automaticamente:
  - awww-daemon, o script de wallpaper do Utumno, dunst;
  - **`udiskie -a`**;
  - pipewire, `qsd77 run -c utumno`, swayidle, o polkit-mate, xdg-user-dirs e `~/.auto.sh`.
- [OBS] `~/.auto.sh` (de `common/`) abre automaticamente o `calamares` (com `sudo -E`) se estiver instalado, e depois o `d77-welcome`.
- [VER] **O Utumno faz pedidos de rede sozinho**: `modules/Weather.qml` executa `curl https://wttr.in/…`. Não há opção de configuração para o desligar (`config/` só tem `Colors.qml`). **[INF]** Isto expõe o IP público e a geolocalização aproximada a um serviço externo sempre que a sessão gráfica arranca. É relevante numa ISO de resposta a incidentes.
- [Utilizador, 2026-11-07] Sem rede, o Utumno funciona normalmente: o widget mostra uma indicação de indisponível ou sem rede. Isto bate com o código (`"weather unavailable"`). A falha é benigna; a questão em aberto é apenas o pedido de saída **quando há rede**. [PROP] Bloquear `wttr.in` no overlay do D77orphaned (por exemplo `0.0.0.0 wttr.in` em `/etc/hosts`), sem tocar no Utumno.
- [OBS] O Utumno também tem o popup de chat Ollama. A variante d77void inclui o `ollama` (72 MiB) e o serviço ativo. **[DESC]** Falta saber como o Utumno se comporta sem Ollama instalado.
- [OBS] O README do Utumno diz que foi testado com niri e Hyprland. O d77void usa-o com wasp e spitfire; o módulo de workspaces tem versões para Hyprland e Sway. **[DESC]** Falta confirmar quais widgets funcionam no wasp.

### Launcher
- [OBS] pwm: `rofi` (via sxhkd/skel) e `dmenu` (dependência do pwm). wasp: `wmenu-run` (`wasp.menu`), o launcher do Utumno (`super+space`) e `d77run` (`super+r`).
- [VER] `d77run` é GTK4: acrescenta 182 pacotes / 369 MiB face ao `base-system`. **[PROP]** Dispensável na PoC: `wmenu` e `dmenu` chegam.

## 4. O que se pode reutilizar **sem modificar**

| Item | Reutilização | Notas |
|---|---|---|
| `mklive.sh`, `lib.sh`, `dracut/`, `grub/`, `isolinux/`, `keys/` | **Sim**, se forem chamados como estão a partir de um checkout fixo (por exemplo um submódulo read-only num commit fixo), com `-I <overlay do d77orphaned>`, `-c/-H` e `ROOTDIR` apontados para fora do checkout | Não exige editar nada. O `mklive.sh` aceita vários `-I`, `-x` (pós-setup) e `-C`. |
| `mkd77.sh` | **Não** | Variantes codificadas; a lógica `include_*` traz udiskie, polkit permissivo, Calamares, plymouth, etc. |
| `common/` e skels pwm/wasp | **Parcial / desaconselhado** | Contêm automontagem e o `.auto.sh`. Melhor ter um overlay próprio, inspirado neles. |
| `common/os-release`, branding | Não | Identidade d77void; o D77orphaned deve ter a sua. |
| Repositório binário d77void | **Sim**, como `-r` adicional | pwm, wasp, utumno, qsd77 e d77-st; assinatura verificada. |

**[PROP] Estratégia de build:** um wrapper próprio no `d77orphaned` (manifesto de pacotes + overlay + cmdline) que chama o `mklive.sh` do d77void num **commit fixo**, sem cópia. A alternativa é copiar o `mklive.sh` e os seus ficheiros (BSD-2, manter `COPYING` e a origem), se se quiser independência total das mudanças futuras do d77void. Fica para decisão.

## 5. Riscos de integridade e segurança herdados

| Risco | Origem | Estado |
|---|---|---|
| Montagem automática de discos alvo | `udiskie -a` no startup do pwm (no pacote) e no skel do wasp; regra polkit `50-udisks.rules` dá mount/unlock sem autenticação ao grupo `storage`; `adduser.sh` dá tudo ao `wheel` | [OBS] **Bloqueante**: o overlay do D77orphaned não pode trazer udiskie/gvfs/udisks2 em autostart. |
| `sshd` ativo com palavra-passe conhecida (`anon:voidlinux`) | `mkd77.sh` (`SERVICES="sshd …"`) + `adduser.sh` | [OBS] Numa rede comprometida, isto é uma porta aberta. [PROP] Não ativar o sshd por defeito na PoC. |
| Montagem automática de RAID/LVM **depois** do initramfs | Regras udev do `mdadm`/`lvm2` no sistema real; `rd.md=0 rd.dm=0` só cobrem o initramfs | [DESC] Testar em VM com RAID/LVM de teste. Opções a avaliar: `rd.md=0`, `rd.lvm=0`, `lvm.conf` com `event_activation=0`/`auto_activation_volume_list = []`, `/etc/mdadm.conf` com `AUTO -all`. |
| Ativação de swap encontrada nos discos | Void runit `core-services` (fstab/swap) | [INF] O fstab live não deve listar swap. [DESC] Confirmar. |
| Replay do journal ao montar `ro` | Comportamento do kernel ext4/XFS | Usar `-o ro,noload` (ext4) / `ro,norecovery` (XFS); para trabalho forense, `blockdev --setro` antes de montar. |
| Pedido de rede automático (wttr.in) | Utumno `Weather.qml` | [VER] Não se desliga por configuração; alterar o Utumno está fora do âmbito. Decisão do utilizador. |
| Calamares a abrir automaticamente | `.auto.sh` | Não aplicável se o Calamares não for incluído e o `.auto.sh` não for copiado. |
| Label `VOID_LIVE` fixa | `mklive.sh` | [INF] Conflito se outra pen Void live estiver ligada. Menor. |

## 6. Estimativa de footprint (instalado, não comprimido)

[VER] Fecho de dependências calculado a partir de `run_depends` dos índices x86_64 (o método não segue `shlib-requires` nem pacotes virtuais complexos; usar como **estimativa**):

| Conjunto | Pacotes | Instalado |
|---|---|---|
| `base-system` (inclui kernel 6.18 e linux-firmware) | 136 | 1118 MiB |
| Core consola proposto (inventário §core) | 249 | 1465 MiB |
| + opcionais | 299 | 1805 MiB |
| Core + pwm | 373 | 2090 MiB |
| Core + pwm + wasp/Utumno | 479 | 2371 MiB |
| Tudo (core + opcionais + pwm + wasp) | 512 | 2660 MiB |

[INF] Com squashfs xz, a ISO deve ficar entre **≈0,9 e 1,2 GiB**. Não foi medida. O maior consumidor é `linux-firmware-network` (442 MiB), essencial para Wi-Fi.

## 7. Ports novos

[VER] **Indispensáveis: 0.** Todas as capacidades centrais existem no Void oficial ou nonfree (nmap) para glibc e musl. As ferramentas gráficas d77 existem no repositório d77void para glibc. Ausentes sem necessidade de port: `dc3dd` (alternativa `dcfldd`), `bulk_extractor` (adiar), `tshark` como pacote próprio (`wireshark` é o pacote CLI; `wireshark-qt` é a GUI).

## 8. Desconhecidos que exigem teste

1. Arranque BIOS/UEFI da ISO resultante em VM e hardware (incluindo o T480s com Libreboot).
2. Utumno no wasp: widgets, IPC, comportamento sem Ollama.
3. Se o pwm aceita `startup_script` no ficheiro do utilizador como a documentação sugere.
4. Automontagem por udev de MD/LVM no sistema live.
5. Sessão gráfica a partir da TTY sem display manager (`startx`/`wasp-session`), se se decidir não incluir SDDM/greetd.
6. Fluxo de escrita da pen que preserve uma partição de dados (o `mklive.sh` gera uma ISO híbrida com partição EFI anexada; acrescentar uma partição depois de um `dd` é possível em teoria, mas não foi testado).

## Reprodução num host Void

```sh
xbps-query -R -p pkgver,installed_size <pacote>
xbps-query -R -x <pacote>                      # dependências diretas
xbps-install -n -R -r /tmp/dryroot <lista>      # fecho e tamanho, sem instalar
xbps-query --repository=https://sourceforge.net/projects/d77void/files/d77void-repo -Rs .
```

## 9. Decisões do utilizador

| # | Data | Questão | Decisão |
|---|---|---|---|
| D1 | 2026-11-07 | Pedido automático do Utumno a `wttr.in` | **PoC:** bloquear no overlay do D77orphaned (`0.0.0.0 wttr.in` em `/etc/hosts`), sem tocar no Utumno; aceita-se ver «weather unavailable» na barra durante a PoC. **Se o projeto avançar além da PoC:** opção na própria Utumno (por exemplo `UTUMNO_WEATHER=0`, que esconde o widget **e** para o `Timer`), feita como alteração separada no repositório Utumno, com autorização própria e nova versão do pacote; o D77orphaned passa a exportar a variável e retira a entrada do `/etc/hosts`. |
| D2 | 2026-11-07 | Arquitetura | **x86_64 glibc.** wasp e scenefx0.5 só existem em glibc; ports novos indispensáveis = 0. musl fora da PoC. |
| D3 | 2026-11-07 | Estratégia de build | **Revisto pelo utilizador (2026-11-07):** o `d77orphaned` começa como **clone integral do d77void @ `c567d0cf`, com histórico e sem remote**, e é depois podado; `git diff c567d0cf` mostra tudo o que divergiu. Sem bash-it (sem submódulos nem dependências externas no build). Texto original: **Copiar para dentro do `d77orphaned`** `mklive.sh`, `lib.sh`, `dracut/`, `grub/`, `isolinux/` e `keys/` do d77void no commit `c567d0cf`. Manter `COPYING` (BSD-2, void-mklive) e registar a origem (repositório, commit, ficheiros, data) num ficheiro de proveniência. O original fica intocado. A cópia pode depois ser adaptada **localmente** (por exemplo `sshd` desligado, polkit menos permissivo em `adduser.sh`, label própria), com cada desvio documentado. |
| D4 | 2026-11-07 | Login gráfico | **greetd com o greeter da quickshell-d77** (`common/quickshell-d77/greeter` no d77void; Daniel, MIT), copiado para o overlay do D77orphaned. Ver nota abaixo. |

| D5 | 2026-11-07 | Login live | **Autologin** pelo `[initial_session]` do greetd, como `anon`. Só se aplica no primeiro arranque do greetd. Ao sair dessa sessão aparece o greeter (`default_session`), onde se escolhe a outra sessão. |
| D6 | 2026-11-07 | Sessão de autologin | **pwm (X11)**, por ser a mais compatível com hardware variado. `initial_session` = `startx /usr/bin/env dbus-launch pwm` (o mesmo que o greeter usa para xsessions); wasp + Utumno ficam disponíveis no greeter depois de sair. Requer `xinit`. [INF] Combina com a entrada `nomodeset`: o X11 tem fbdev/vesa via `xorg-video-drivers`. |
| D7 | 2026-11-07 | Arranque só com consola | **Entrada GRUB/isolinux própria** com um parâmetro (por exemplo `d77.nogui`) que impede o greetd de arrancar; as TTY ficam como único ambiente. [PROP] Implementar como hook pre-pivot no `dracut/vmklive` copiado (o mesmo padrão de `nomodeset.sh`): remover `etc/runit/runsvdir/default/greetd` no novo root quando o parâmetro existe. Alternativa: verificar `/proc/cmdline` no `run` do serviço. Decidir na implementação. |
| D8 | 2026-11-07 | Rede ao arrancar | **`dhcpcd` ativo por defeito** (rede pronta ao estilo Grml). |
| D9 | 2026-11-07 | Relógio | **`chronyd` ativo por defeito** (sincronização automática por NTP). |
| D10 | 2026-11-07 | Gate da fase 4 | **Aprovado** (`APPROVAL_GATE.md`): avançar para a fase 5 — repositório local, builder copiado, manifesto, overlay, build e testes em VM. Sem remoto, sem publicação, sem alterações a outros projetos. Autoinstaller do dracut removido da cópia do `mklive.sh`. |

**Nota D4 — o que o greeter implica** [OBS/VER]:
- Arranque: greetd → `/etc/greetd/greet-dwl.sh` → `dwl -s "qs -p <greeter>"`, como utilizador `_greeter`, no VT 7. As TTY 1–6 continuam livres para a consola.
- Pacotes: `greetd` (Void), `dwl` 0.9_1 (**d77void**, só glibc, depende de wlroots0.20), `quickshell` (Void), `xinit` (para as sessões X11). Fecho de `greetd dwl quickshell xinit`: 161 pacotes / ≈298 MiB além do `base-system`, em grande parte partilhados com o conjunto wasp/Utumno.
- Sessões: o greeter lê `/usr/share/wayland-sessions` e `/usr/share/xsessions`. Mostra **wasp** (`wasp-session`) e **pwm** (`dbus-launch pwm`, lançado como `startx /usr/bin/env dbus-launch pwm`). Lista também qualquer outra sessão instalada; a PoC só deve instalar estas duas.
- [OBS] No d77void, o greetd só é usado nas variantes Wayland (`include_greetd`); as X11, incluindo a `pwm`, usam SDDM. [Utilizador, 2026-11-07] Uso diário do greeter com sessões X11 no portátil: funciona bem. → O suporte X11 está confirmado em uso real. **[DESC]** A combinação greetd + pwm ainda não foi exercitada em nenhuma ISO live; fica no plano de testes.
- A autenticação passa pelo PAM do greetd. O utilizador live (`anon`) tem a palavra-passe `voidlinux`, definida pelo `adduser.sh`.
- **[DESC]** Falta testar o greeter dentro do overlay live (permissões de `_greeter`, grupo `video`, seat via elogind).
