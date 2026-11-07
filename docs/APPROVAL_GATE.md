# APPROVAL_GATE — Fase 4: gate de aprovação da PoC

- **Data:** 2026-11-07
- **Base:** `BASELINE_AUDIT.md` (decisões D1–D7) e `PACKAGE_INVENTORY.md`.
- **Estado:** **APROVADO em 2026-11-07** (D10); P1 = `dhcpcd` ativo, P2 = `chronyd` ativo. **Nada foi construído nem testado.** Todos os pacotes foram *encontrados nos índices* (x86_64 glibc, 2026-11-07); nenhum foi instalado.

Ao aprovar este documento autorizas a **fase 5 — protótipo**: criar o repositório local `d77orphaned`, copiar o builder, escrever o manifesto e o overlay, construir a ISO num host Void e testá-la em VM. Isso **não** inclui criar ou publicar o repositório remoto, publicar pacotes, nem alterar o d77void, a Utumno ou qualquer outro projeto.

---

## 1. Resumo

| | |
|---|---|
| Arquitetura | x86_64 glibc (D2) |
| Builder | cópia própria do `mklive.sh` e dos ficheiros de que depende (D3) |
| Login | greetd + greeter da quickshell-d77, com autologin no pwm (D4–D6) |
| Arranque só consola | entrada própria com `d77.nogui` (D7) |
| Ports novos | **0** |
| Pacotes no fecho da PoC | 456: Void 446, nonfree 1 (`nmap`), d77void 9 |
| Tamanho instalado (estimativa) | ≈ 2,2 GiB → ISO ≈ 0,9–1,1 GiB (**não medido**) |
| Pacotes indesejados no fecho | nenhum: verificado que `udisks2`, `udiskie`, `gvfs`, `NetworkManager`, `ollama`, `calamares`, `pipewire`, `sddm` e `pulseaudio` **não** entram |

## 2. Manifesto proposto

### 2.1 Incluído automaticamente pelo `mklive.sh` (não listar)
`base-system` (kernel 6.18, linux-firmware), `syslinux`, `grub-i386-efi`, `grub-x86_64-efi`, `memtest86+` e os pacotes do initramfs (`dracut-network`, `device-mapper`…).

### 2.2 Core — consola (66, todos Void exceto `nmap`)

| Grupo | Pacotes |
|---|---|
| Discos e hardware de armazenamento | `util-linux` `parted` `gptfdisk` `smartmontools` `nvme-cli` `hdparm` `sdparm` `sg3_utils` `lsscsi` |
| Recuperação e clonagem | `ddrescue` `testdisk` `partclone` `fsarchiver` |
| Filesystems | `e2fsprogs` `xfsprogs` `btrfs-progs` `dosfstools` `exfatprogs` `ntfs-3g` `f2fs-tools` `mtools` |
| Volumes e encriptação | `cryptsetup` `lvm2` `mdadm` (com autoativação desligada, §4) |
| Boot / EFI | `efibootmgr` `efivar` `os-prober` |
| Rede | `iproute2` `iputils` `dhcpcd` `wpa_supplicant` `openssh` `curl` `rsync` |
| Diagnóstico de rede | `tcpdump` `nmap`* `traceroute` `mtr` `ldns` `openbsd-netcat` `socat` `arp-scan` |
| Forense | `dcfldd` `libewf` `sleuthkit` `foremost` |
| Hardware e sistema | `dmidecode` `pciutils` `usbutils` `hwinfo` `chntpw` `f3` `lynis` |
| Operação | `tmux` `vim` `less` `man-db` `lsof` `strace` `pv` `zstd` `p7zip` `squashfs-tools` `dialog` `chrony` `xtools-minimal` |

\* O `nmap` vem do repositório **nonfree** (licença NPSL). O build tem de acrescentar `-r https://repo-default.voidlinux.org/current/nonfree`, porque o `mklive.sh` não inclui o nonfree por defeito. A redistribuição numa ISO gratuita é permitida pela NPSL; a licença será revista antes de qualquer publicação.

### 2.3 Gráfico X11 — pwm (16)
`xorg-minimal` `xorg-input-drivers` `xorg-video-drivers` `xinit` `setxkbmap` `xauth` `dejavu-fonts-ttf` `terminus-font` `font-misc-misc` `pwm`† `d77-st`† `dmenu` `sxhkd` `dbus` `elogind` `polkit`

### 2.4 Gráfico Wayland — wasp + Utumno (10)
`mesa-dri` `wasp`† `utumno`† `qsd77`† `quickshell` `matugen` `wmenu` `alacritty` `dunst` `awww`

### 2.5 Login (2 + overlay)
`greetd` `dwl`† e o greeter copiado de `d77void/common/quickshell-d77/greeter` (§3).

† Pacotes do repositório d77void (assinatura verificada, `keys/2b:d7:…`). No fecho entram ainda `d77-st-terminfo`, `font-JetBrainsMono` e `scenefx0.5`, também do d77void.

### 2.6 Serviços runit
| Serviço | Estado | Nota |
|---|---|---|
| `dbus` `elogind` `polkitd` `acpid` | ativo | necessários às sessões gráficas e ao ACPI |
| `greetd` | ativo, exceto com `d77.nogui` | D5–D7 |
| `dhcpcd` | ativo | D8 |
| `chronyd` | ativo | D9 |
| `sshd` | **desligado** | instalado; arranque manual com `sv up sshd` depois de mudar a palavra-passe |
| `wpa_supplicant` | desligado | usado manualmente ou via dhcpcd |

## 3. Opcional — fase 2 (não entra na PoC)
`exiftool`, `wireshark` (CLI tshark), `termshark`, `afflib`, `yara`, `binwalk`, `nikto`, `sqlmap`, `john`, `thc-hydra`, `testssl.sh`, `ssh-audit`, `fuse-sshfs`, `nfs-utils`, `cifs-utils`, `wireguard-tools`, `iperf3`, `rkhunter`, `chkrootkit`, `lshw`, acessibilidade na consola (`espeakup`, `brltty`, `void-live-audio`). Com todos estes a imagem passaria para ≈ 2,6 GiB instalado.

## 4. Fora (Out)
| Pacote | Razão |
|---|---|
| `zfs` | DKMS + compilador, +559 MiB |
| `hashcat` | sem GPU no live; o `john` cobre a função |
| `wireshark-qt` | +649 MiB |
| `nwipe` | destrutivo por natureza |
| `udiskie` `udisks2` `gvfs` | montagem automática, incompatível com a política de integridade |
| `NetworkManager` | +61 MiB; dhcpcd/wpa_supplicant chegam |
| `d77run` | GTK4, +369 MiB; `dmenu`/`wmenu`/launcher da Utumno chegam |
| `ollama`, `calamares`, `sddm`, `plymouth`, `pipewire` | sem função na PoC |
| `orca` | +373 MiB; a acessibilidade gráfica fica para depois |
| `bulk_extractor`, `dc3dd` | inexistentes no Void; não se portam |

## 5. O que se reutiliza do d77void e como

| Origem (commit `c567d0cf`) | Como | Alterações locais previstas no `d77orphaned` |
|---|---|---|
| `mklive.sh`, `lib.sh`, `version` | **cópia** + `COPYING` (BSD-2) + ficheiro de proveniência | label própria (ex.: `D77ORPHANED`) em vez de `VOID_LIVE`; remoção do autoinstaller (linha abaixo) |
| `dracut/vmklive/` | cópia | `adduser.sh`: sem `sshd` ativo; hook novo `nogui.sh` (D7); polkit mantido (o live user já tem `sudo` sem palavra-passe; o risco real era a montagem automática, que fica sem ferramentas) |
| `dracut/autoinstaller/` | **não copiar** | o `mklive.sh` refere-o em 3 sítios (`copy_autoinstaller_files`, `--force-add`, `rm -r`) → remover essas referências na cópia. Só ativa com `root=vai`, mas é um instalador **destrutivo** dentro do initramfs; não deve existir numa ISO forense |
| `dracut/netmenu/` | não copiar | o `mklive.sh` não o usa |
| `grub/`, `isolinux/` | cópia | título `D77orphaned`; entrada «consola (sem gráficos)» com `d77.nogui`; entradas de voz removidas (fase 2); `rd.lvm=0` acrescentado à cmdline |
| `keys/` (3 chaves públicas) | cópia | — |
| `data/splash.png` | cópia ou splash próprio | branding próprio quando existir |
| `common/quickshell-d77/greeter/` | cópia para o overlay `/etc/greetd/…` | `config.toml` com `[initial_session]` (pwm) |
| Repositório binário d77void | `-r` no build | — |

**O que não muda:** `mkd77.sh`, skels e `common/` do d77void, os pacotes pwm/wasp/Utumno/qsd77/dwl, o repositório binário e a Utumno. A meteorologia da Utumno é tratada por `/etc/hosts` no overlay (D1).

### Overlay próprio (`includedir/`)
- `/etc/hosts` com `0.0.0.0 wttr.in` (D1).
- `/etc/greetd/config.toml` + greeter + `greet-dwl.sh` (D4–D6).
- `/etc/skel/.config/pwm/config.toml` com `startup_script` próprio **sem `udiskie`** (pwm sem automontagem).
- `/etc/skel/.config/wasp/config.lua` próprio: autostart sem `udiskie`, sem `pipewire` e sem `ollama`; mantém `qsd77 run -c utumno`, `dunst`, `awww`.
- `/etc/lvm/lvm.conf` com `event_activation = 0` e `auto_activation_volume_list = []`; `/etc/mdadm.conf` com `AUTO -all` (a testar, §6).
- `/etc/os-release` próprio (`ID_LIKE=void`).
- **Não** levar `.auto.sh`, `d77-welcome`, `50-udisks.rules` nem as regras plymouth.

## 6. Plano de testes

**Onde:** construir num host Void. Os testes de integridade correm **só em VM com discos descartáveis**. O hardware real serve apenas para arranque, gráficos e rede: o T480s (Libreboot) e uma máquina com BIOS legado se houver. Nenhum teste destrutivo nas máquinas pessoais.

| # | Teste | Ambiente | Critério de sucesso |
|---|---|---|---|
| T1 | Build reproduzível | host Void | ISO gerada; o log lista os pacotes do manifesto; nenhum pacote de §4 no rootfs (`xbps-query -r`) |
| T2 | Arranque BIOS | QEMU SeaBIOS | menu isolinux; arranque até à TTY e ao greetd |
| T3 | Arranque UEFI | QEMU OVMF | menu GRUB; idem |
| T4 | `d77.nogui` | QEMU | greetd não arranca; TTY1 utilizável |
| T5 | `nomodeset` + pwm | QEMU (VGA std) | o autologin pwm arranca com fbdev/vesa |
| T6 | Autologin pwm → sair → greeter → wasp+Utumno | QEMU virtio-gpu | as duas sessões arrancam; a barra mostra «weather unavailable» com rede ativa (D1) |
| T7 | Ferramentas core | QEMU | cada binário do §2.2 corre `--version`/`-h` sem bibliotecas em falta (script de verificação) |
| T8 | Integridade: discos alvo | QEMU com discos de teste: ext4 com journal sujo, XFS, NTFS, LUKS2, RAID1 MD, LVM, swap | após o arranque e após login gráfico: nenhum `md*` assemblado, nenhum LV ativo, nenhum LUKS aberto, nada montado, swap inativa (`/proc/mdstat`, `lvs`, `lsblk`, `/proc/swaps`, `mount`); hashes SHA-256 dos discos iguais antes e depois |
| T9 | Montagem segura | QEMU | `blockdev --setro` + `mount -o ro,noload` (ext4) / `ro,norecovery` (XFS) não alteram o hash |
| T10 | Rede | QEMU + hardware | DHCP com fio (conforme P1); Wi-Fi via wpa_supplicant no T480s; `sshd` desligado (`ss -tln`) |
| T11 | Sem persistência | QEMU | arranque sem partição de dados não bloqueia nem atrasa |
| T12 | Hardware real | T480s (Libreboot) | arranque UEFI/payload, X11, Wayland, Wi-Fi |

A persistência LUKS2 fica para depois da PoC base, como diz o RESEARCH_PLAN (fase 5, último passo).

## 7. Riscos conhecidos
- **Autoativação MD/LVM depois do initramfs:** a mitigação (§5) não está testada. Se T8 falhar, avaliar regras udev locais no overlay.
- **Utumno no wasp:** os widgets de workspaces são para Hyprland/Sway/niri, por isso no wasp podem ficar vazios. É estético e não bloqueia.
- **greetd + pwm em live:** confirmado em uso real no portátil, nunca exercitado numa ISO.
- **`dwl` e `scenefx0.5` só existem no repositório d77void:** a ISO depende da disponibilidade do SourceForge no momento do build.
- **Label do ISO:** se ficar `VOID_LIVE`, há conflito com outras pens Void, daí a label própria.
- **Estimativas de tamanho:** calculadas a partir de `run_depends`; o T1 mede o valor real.

## 8. Perguntas pendentes
- **P1 — Rede ao arrancar:** `dhcpcd` ativo por defeito (ao estilo Grml, rede pronta, mas anuncia-se na rede ao arrancar) ou manual (`sv up dhcpcd`)?
- **P2 — Relógio:** `chronyd` ativo (hora certa nos registos e hashes, mas contacta servidores NTP) ou manual?
- **P3 — Aprovação:** aprovas o manifesto (§2), as exclusões (§3–4), a reutilização (§5) e o plano de testes (§6) para avançar para a fase 5?
