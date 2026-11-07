# Inventário de pacotes — FASE 0/1: ENCONTRADO NOS ÍNDICES, NÃO TESTADO

**Aviso:** «ENCONTRADO» significa que o pacote está no índice do repositório. **Nenhum foi instalado nem testado.** Pacote no índice ≠ pacote instalado ≠ ferramenta funcional em live. Não copiar esta tabela para nenhum script de build.

- **Data:** 2026-11-07
- **Método:** leitura de `index.plist` dos repositórios `repo-default.voidlinux.org/current` (+`nonfree`) e d77void (SourceForge), x86_64 e x86_64-musl. O fecho de dependências foi calculado a partir de `run_depends` e é uma estimativa. Detalhe e comandos de reprodução em `BASELINE_AUDIT.md`.
- **«+deps»** = pacotes/MiB que o pacote acrescenta ao fecho de `base-system` (x86_64). Valores musl idênticos salvo nota.
- **Decisão** = proposta para a fase 3; **pendente de aprovação**.

## Core (consola)

| Capacidade | Pacote exato (origem) | Versão | +deps | Estado | Decisão proposta / notas |
|---|---|---|---|---|---|
| Identificação/partições | `util-linux` `parted` `gptfdisk` (Void) | 2.41.4 / 3.8 / 1.0.10 | 0 / +2·3M / +2·1M | ENCONTRADO | INCLUIR |
| SMART / NVMe / ATA / SCSI | `smartmontools` `nvme-cli` `hdparm` `sdparm` `sg3_utils` `lsscsi` (Void) | 7.5 / 2.16 / 9.65 … | ≤ +3·3M cada | ENCONTRADO | INCLUIR |
| Imagem / recuperação de blocos | `ddrescue` (Void; **`gddrescue` não existe**) | 1.29.1 | +1·0M | ENCONTRADO | INCLUIR |
| Recuperação de partições/ficheiros | `testdisk` (Void; inclui photorec **[DESC]** confirmar) | 7.2 | +16·21M | ENCONTRADO | INCLUIR |
| Clonagem/backup de FS | `partclone` `fsarchiver` (Void) | 0.3.47 / 0.8.6 | +17·20M / +3·3M | ENCONTRADO | INCLUIR |
| Filesystems | `e2fsprogs` `xfsprogs` `btrfs-progs` `dosfstools` `exfatprogs` `ntfs-3g` `f2fs-tools` `mtools` | — | ntfs-3g +14·18M; resto ≈0 | ENCONTRADO | INCLUIR |
| Encriptação/volumes | `cryptsetup` `lvm2` `mdadm` (Void) | 2.8.8 / 2.03.29 / 4.4 | ≤ +5·6M | ENCONTRADO | INCLUIR; **desativar autoativação** (ver auditoria §5) |
| ZFS | `zfs` (Void, DKMS) | 2.4.4 | **+39·559M** | ENCONTRADO | **EXCLUIR** na PoC (DKMS + compilador) |
| EFI / boot | `efibootmgr` `efivar` `os-prober` `grub-x86_64-efi` `grub-i386-efi` (Void) | 18 / 39 / 1.84 / 2.12 | grub-efi +7·33M | ENCONTRADO | INCLUIR (os grub já vêm pelo mklive) |
| Memória | `memtest86+` (Void) | 9.00 | — | ENCONTRADO | Já incluído pelo `mklive.sh` em x86 |
| Rede base | `iproute2` `iputils` `dhcpcd` `iwd` **ou** `wpa_supplicant` `openssh` `curl` `rsync` | — | NetworkManager +31·61M | ENCONTRADO | INCLUIR sem NetworkManager [PROP]; **sshd desligado por defeito** |
| Diagnóstico de rede | `tcpdump` `traceroute` `mtr` `ldns` (drill) `openbsd-netcat` `socat` `nmap` (**nonfree**) | — | nmap +3·29M; bind-utils +15·14M | ENCONTRADO | INCLUIR; `ldns` em vez de `bind-utils` |
| Hashing / imagem forense | `coreutils` `dcfldd` (Void; **`dc3dd` não existe**) `libewf` | 9.4 / 1.3.4 / 2026-09-24 | libewf +2·10M | ENCONTRADO | INCLUIR |
| Análise forense | `sleuthkit` `foremost` `exiftool` (Void; **`perl-Image-ExifTool` → `exiftool`**) | 4.13 / 1.5.7 / 13.57 | sleuthkit +6·85M; exiftool +4·96M | ENCONTRADO | INCLUIR sleuthkit+foremost; exiftool a decidir (tamanho) |
| Hardware | `dmidecode` `pciutils` `usbutils` `hwinfo` `lshw` | — | lshw +1·8M | ENCONTRADO | INCLUIR (lshw opcional) |
| Firmware | `linux-firmware` (Void, já no `base-system`) | 20260810 | network = 442 MiB | ENCONTRADO | INCLUIR (necessário para Wi-Fi) |
| Windows offline | `chntpw` (Void) | 140201 | +1·0M | ENCONTRADO | INCLUIR [PROP] |
| Pens / falsificações | `f3` (Void) | 9.0 | +2·1M | ENCONTRADO | INCLUIR [PROP] |
| Consola / manutenção | `tmux` `vim` `less` `man-db` `lsof` `strace` `pv` `zstd` `p7zip` `squashfs-tools` | — | vim +5·44M; neovim +15·36M | ENCONTRADO | INCLUIR; um só editor |

## Opcional / fase 2

| Capacidade | Pacote exato (origem) | +deps | Estado | Decisão proposta / notas |
|---|---|---|---|---|
| Captura de tráfego CLI | `wireshark` (Void, pacote CLI; **não há `tshark`**) | +41·206M | ENCONTRADO | ADIAR; `tcpdump` cobre a PoC |
| Captura TUI | `termshark` | +42·223M | ENCONTRADO | ADIAR |
| Wireshark GUI | `wireshark-qt` | **+225·649M** | ENCONTRADO | EXCLUIR na PoC |
| Metadados avançados | `bulk_extractor` | — | **AUSENTE** | ADIAR (seria port) |
| Integridade/AFF | `afflib` `yara` `binwalk` | ≤ +15·10M | ENCONTRADO | ADIAR |
| Auditoria web | `nikto` `sqlmap` | +7·77M / +5·37M | ENCONTRADO | ADIAR |
| Passwords | `john` / `hashcat` | +51M / **+149M** | ENCONTRADO | `john` ADIAR; `hashcat` EXCLUIR (sem GPU no live) |
| Força bruta de serviços | `thc-hydra` (**não `hydra`**) | +6·30M | ENCONTRADO | ADIAR |
| Auditoria de host | `lynis` `rkhunter` `chkrootkit` | +1·2M / +17·83M / +19·49M | ENCONTRADO | `lynis` INCLUIR [PROP]; os outros ADIAR |
| TLS / SSH | `testssl.sh` `ssh-audit` | +16·17M / +5·25M | ENCONTRADO | ADIAR |
| Descoberta L2 | `arp-scan` | +1·2M | ENCONTRADO | INCLUIR [PROP] |
| Partilhas | `fuse-sshfs` (**não `sshfs`**) `nfs-utils` `cifs-utils` | +4·15M / +7·5M / +27·63M | ENCONTRADO | ADIAR |
| VPN | `wireguard-tools` | +2·0M | ENCONTRADO | ADIAR |
| Desempenho de rede | `iperf3` | +1·0M | ENCONTRADO | ADIAR |
| Apagamento seguro | `nwipe` | +6·4M | ENCONTRADO | **EXCLUIR** na PoC (destrutivo por natureza) |

## Gráficos d77

| Componente | Pacote exato (origem) | +deps | Estado | Notas |
|---|---|---|---|---|
| X11 base | `xorg-minimal` `xorg-input-drivers` `xorg-video-drivers` `xinit` + fontes (Void) | conjunto pwm completo: 183 pkgs / 751 MiB instalado | ENCONTRADO | sem SDDM [PROP] |
| pwm | `pwm` 0.6.7_1 (**d77void**, glibc e musl) | +19·249M (inclui X) | ENCONTRADO | startup do pacote arranca `udiskie -a`; sobrepor `startup_script` [INF] |
| Terminal X11 | `d77-st` (d77void, dependência do pwm) | +13·11M | ENCONTRADO | — |
| Launcher X11 | `dmenu` (Void, dependência do pwm) | +14·11M | ENCONTRADO | `rofi` (+42·58M) opcional |
| Wayland base | `mesa-dri` `dbus` `elogind` `polkit` | — | ENCONTRADO | — |
| wasp | `wasp` 0.10.1_1 (**d77void, só glibc**) + `scenefx0.5` (d77void) + `wlroots0.20` (Void) | +99·149M | ENCONTRADO | **AUSENTE em musl** |
| Utumno | `utumno` 0.2.0_1 (d77void) | +92·195M | ENCONTRADO | **não declara `quickshell` nem `qsd77`**: listar explicitamente; faz pedidos a wttr.in |
| Runtime do Utumno | `quickshell` 0.3.2 (Void) + `qsd77` 1.3.3 (d77void, CLI Go) | quickshell +143·291M | ENCONTRADO | obrigatórios para Utumno |
| Launcher Wayland | `wmenu` (Void) | +27·44M | ENCONTRADO | `d77run` (GTK4, +182·369M) EXCLUIR [PROP] |
| Terminal Wayland | `alacritty` (Void) | +23·31M | ENCONTRADO | — |
| Automontagem | `udiskie` `udisks2` `gvfs` | — | ENCONTRADO | **EXCLUIR** (conflito com a política de integridade) |

## Registo obrigatório por pacote aprovado

Copiar este modelo para **cada pacote** na investigação:

```text
Função:
Nome exato / origem (Void oficial, d77void, port novo):
Arquitetura / libc / versão / data:
Comando de pesquisa + saída relevante:
Dependências novas e dimensão:
Teste de instalação (ambiente descartável):
Teste funcional + resultado:
Riscos (kernel, firmware, licenças, privilégios):
Alternativas:
Esforço de manutenção:
Decisão: INCLUIR / ADIAR / EXCLUIR / PORT PROPOSTO
Justificação:
```

## Contadores (preencher após pesquisa)

- Pacotes core **encontrados** (não validados): ~65 nomes, todos no Void oficial/nonfree; **validados por teste: 0**
- Pacotes opcionais encontrados: ~20; validados: 0
- Pacotes d77 reutilizáveis sem alteração: `pwm`, `d77-st`, `wasp`, `scenefx0.5`, `utumno`, `qsd77` (6, só glibc para wasp/scenefx0.5); a verificar em teste
- Ports novos indispensáveis: **0** (x86_64 glibc)
- Ports novos opcionais: `bulk_extractor` (1); em musl, +2 (`wasp`, `scenefx0.5`)
- Dimensão estimada: core+pwm+wasp ≈ 2,4 GiB instalado → ISO ≈ 0,9–1,2 GiB (**estimativa, não medida**)

**Gate de sustentabilidade:** com **5** ports novos indispensáveis, parar e rever o escopo com o utilizador; perto de **30**, a conceção é inviável. A ausência de um pacote não obriga a portá-lo.
